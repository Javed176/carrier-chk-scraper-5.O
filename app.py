import streamlit as st
import sys
import asyncio
import time

DEBUG = True  # Set to False to hide debug expander

st.set_page_config(
    page_title='MC Carrier Intelligence',
    page_icon='🚛',
    layout='wide',
    initial_sidebar_state='expanded'
)

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

try:
    from fmcsa_client import resolve_mc_to_usdot, get_carrier_by_dot, FMCSAError, FMCSAAuthError, FMCSANotFoundError
    from scraper import scrape_carrier_profile
    from ui_components import (
        inject_custom_css,
        render_header,
        render_history_table,
        render_error_card
    )
except Exception as import_err:
    st.error(f"Initialization Error: Failed to load required modules: {import_err}")
    st.stop()

if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'is_auto_running' not in st.session_state:
    st.session_state['is_auto_running'] = False
if 'current_auto_mc' not in st.session_state:
    st.session_state['current_auto_mc'] = 0

@st.cache_data(ttl=3600, show_spinner=False)
def get_fmcsa_data(mc_number, api_key):
    res = resolve_mc_to_usdot(mc_number, api_key)
    res['searched_mc'] = mc_number
    return res

@st.cache_data(ttl=3600, show_spinner=False)
def get_fmcsa_by_dot(dot_number, api_key):
    return get_carrier_by_dot(dot_number, api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_carrier_profile(dot_number, cache_version=1):
    return scrape_carrier_profile(dot_number)

def merge_fmcsa_and_profile(fmcsa_data: dict, profile_data: dict) -> dict:
    p = profile_data or {}
    f = fmcsa_data or {}
    p['searched_mc'] = f.get('searched_mc', p.get('searched_mc', ''))

    comp = p.get('company', {})
    current_name = comp.get('legal_name', '')
    fmcsa_name = f.get('legal_name', '')
    if (not current_name or current_name in ['N/A', 'Unknown', 'None'] or str(current_name).startswith('Carrier DOT #')) and fmcsa_name:
        comp['legal_name'] = fmcsa_name

    if not comp.get('dba_name') and f.get('dba_name'):
        comp['dba_name'] = f.get('dba_name')

    if not comp.get('dot_number') or comp.get('dot_number') in ['N/A', '']:
        comp['dot_number'] = str(f.get('dot_number', comp.get('dot_number', 'N/A')))

    mc_val = f.get('docket_number') or f.get('searched_mc') or comp.get('mc_number', 'N/A')
    if not comp.get('mc_number') or comp.get('mc_number') in ['N/A', 'None', '']:
        comp['mc_number'] = str(mc_val)

    current_status = comp.get('operating_status', '')
    fmcsa_status = f.get('status', '')
    if (not current_status or current_status in ['N/A', 'Unknown', 'None']) and fmcsa_status:
        comp['operating_status'] = fmcsa_status

    current_entity = comp.get('entity_type', '')
    fmcsa_entity = f.get('entity_type', '')
    if (not current_entity or current_entity in ['N/A', 'Unknown', 'None', '']):
        if fmcsa_entity and fmcsa_entity != 'Unknown':
            comp['entity_type'] = fmcsa_entity
        else:
            comp['entity_type'] = current_entity if current_entity else 'Unknown'

    current_owner = comp.get('owner_name', '')
    fmcsa_owner = f.get('owner_name', '')
    if (not current_owner or current_owner in ['N/A', 'None', '']) and fmcsa_owner:
        comp['owner_name'] = fmcsa_owner

    p['company'] = comp

    contact = p.get('contact', {})
    if not contact.get('physical_address') or contact.get('physical_address') in ['N/A', '', 'None']:
        contact['physical_address'] = f.get('physical_address', contact.get('physical_address', 'N/A'))
    if not contact.get('phone') or contact.get('phone') in ['N/A', '', 'None']:
        contact['phone'] = f.get('phone', contact.get('phone', 'N/A'))
    if not contact.get('email') or contact.get('email') in ['N/A', '', 'None']:
        contact['email'] = f.get('email', contact.get('email', 'N/A'))
    p['contact'] = contact

    return p

def process_single_mc_lookup(mc_str: str, api_key: str):
    mc_clean = mc_str.strip()
    if not mc_clean:
        return None

    # 1. Resolve MC to DOT
    fmcsa_data = get_fmcsa_data(mc_clean, api_key)
    dot_number = fmcsa_data.get('dot_number')

    # 2. Fetch full carrier details by DOT (often has phone/owner)
    fmcsa_detail = {}
    if dot_number:
        try:
            fmcsa_detail = get_fmcsa_by_dot(str(dot_number), api_key)
        except Exception:
            fmcsa_detail = {}

    # 3. Scrape dotsearch using cloudscraper
    raw_profile = {}
    if dot_number:
        raw_profile = get_carrier_profile(str(dot_number), cache_version=9)  # bump to invalidate old cache

    # 4. Merge all data (priority: FMCSA detail > FMCSA basic > scraper)
    combined_fmcsa = {**fmcsa_data, **fmcsa_detail}
    profile = merge_fmcsa_and_profile(combined_fmcsa, raw_profile)
    profile['searched_mc'] = mc_clean

    if DEBUG:
        with st.expander(f"Debug for MC {mc_clean}", expanded=False):
            st.write("**FMCSA basic (docket):**", fmcsa_data)
            st.write("**FMCSA detail (DOT):**", fmcsa_detail)
            st.write("**Raw scraper profile:**", raw_profile)
            st.write("**Raw HTML preview:**", raw_profile.get('html_preview', 'N/A'))
            st.write("**Merged profile:**", profile)

    existing_mcs = [item.get('searched_mc') for item in st.session_state['history']]
    if mc_clean not in existing_mcs:
        st.session_state['history'].append(profile)

    return profile

def main():
    inject_custom_css()
    render_header()

    default_webkey = ""
    try:
        if hasattr(st, "secrets") and "FMCSA_WEB_KEY" in st.secrets:
            default_webkey = st.secrets["FMCSA_WEB_KEY"]
    except Exception:
        default_webkey = ""

    st.sidebar.title('🚛 MC Carrier Lookup')
    st.sidebar.divider()
    st.sidebar.subheader('Configuration')
    api_key = st.sidebar.text_input(
        'FMCSA WebKey',
        type='password',
        value=default_webkey,
        help='Get your free key at mobile.fmcsa.dot.gov'
    )
    st.sidebar.divider()

    col_input, col_single, col_auto, col_stop, col_clear = st.columns([2.5, 1.2, 1.4, 1, 1.2])

    with col_input:
        mc_input = st.text_input('Enter Starting MC Number', placeholder='e.g., 1066434')

    with col_single:
        st.write("")
        st.write("")
        single_btn = st.button('🔍 Lookup', use_container_width=True)

    with col_auto:
        st.write("")
        st.write("")
        auto_start_btn = st.button('▶ Start Auto', type='primary', use_container_width=True)

    with col_stop:
        st.write("")
        st.write("")
        stop_btn = st.button('🛑 Stop', type='secondary', use_container_width=True)

    with col_clear:
        st.write("")
        st.write("")
        clear_btn = st.button('🗑️ Clear History', use_container_width=True)

    if stop_btn:
        st.session_state['is_auto_running'] = False
        st.toast("🛑 Auto-increment lookup stopped.")

    if clear_btn:
        st.session_state['history'] = []
        st.session_state['is_auto_running'] = False
        st.toast("🗑️ History cleared!")
        st.rerun()

    if auto_start_btn:
        if not api_key:
            st.warning("Please provide an FMCSA WebKey in the sidebar configuration.")
            return
        if not mc_input:
            st.warning("Please enter a starting MC Number.")
            return

        try:
            import re
            cleaned_start = re.sub(r'\D', '', mc_input)
            st.session_state['current_auto_mc'] = int(cleaned_start)
            st.session_state['is_auto_running'] = True
            st.toast(f"▶ Auto lookup started from MC-{st.session_state['current_auto_mc']}")
        except ValueError:
            st.error("Starting MC Number must contain numeric digits.")
            return

    if single_btn:
        if not api_key:
            st.warning("Please provide an FMCSA WebKey in the sidebar configuration.")
            return
        if not mc_input:
            st.warning("Please enter an MC Number.")
            return

        try:
            with st.spinner(f"Fetching carrier details for MC {mc_input}..."):
                process_single_mc_lookup(mc_input, api_key)
        except Exception as e:
            render_error_card('Lookup Error', str(e))

    if st.session_state.get('is_auto_running', False):
        curr_mc = st.session_state['current_auto_mc']
        with st.spinner(f"🔄 Auto-Processing MC {curr_mc}... (Click 🛑 Stop to halt)"):
            try:
                process_single_mc_lookup(str(curr_mc), api_key)
                st.session_state['current_auto_mc'] += 1
                time.sleep(1.0)
                st.rerun()
            except Exception as auto_err:
                st.toast(f"Skipping MC {curr_mc}: {auto_err}")
                st.session_state['current_auto_mc'] += 1
                st.rerun()

    if st.session_state['history']:
        st.subheader("📊 Searched Carriers Master History")
        render_history_table(st.session_state['history'])

if __name__ == '__main__':
    main()
