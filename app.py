import streamlit as st
import sys
import asyncio
import time

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title='MC Carrier Intelligence',
    page_icon='🚛',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Safe event loop policy configuration
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Safe imports
try:
    from fmcsa_client import resolve_mc_to_usdot, FMCSAError, FMCSAAuthError, FMCSANotFoundError
    from scraper import scrape_carrier_profile
    from ui_components import (
        inject_custom_css,
        render_header,
        render_history_table,
        render_company_card,
        render_contact_section,
        render_operations_section,
        render_safety_section,
        render_insurance_section,
        render_authority_section,
        render_fmcsa_summary,
        render_error_card
    )
except Exception as import_err:
    st.error(f"Initialization Error: Failed to load required modules: {import_err}")
    st.stop()

# Initialize Session State Variables
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
def get_carrier_profile(dot_number):
    return scrape_carrier_profile(dot_number)

def merge_fmcsa_and_profile(fmcsa_data: dict, profile_data: dict) -> dict:
    """Merges FMCSA primary response into profile data as fallbacks for any missing fields."""
    p = profile_data or {}
    f = fmcsa_data or {}
    
    p['searched_mc'] = f.get('searched_mc', '')

    comp = p.get('company', {})
    if comp.get('legal_name', 'N/A') in ['N/A', 'Unknown', '']:
        comp['legal_name'] = f.get('legal_name', 'Unknown Carrier')
    if comp.get('dba_name', 'N/A') in ['N/A', '']:
        comp['dba_name'] = f.get('dba_name', '')
    if comp.get('dot_number', 'N/A') in ['N/A', '']:
        comp['dot_number'] = str(f.get('dot_number', 'N/A'))
        
    mc_val = f.get('docket_number') or f.get('searched_mc') or 'N/A'
    if comp.get('mc_number', 'N/A') in ['N/A', '', 'None']:
        comp['mc_number'] = str(mc_val)
        
    if comp.get('operating_status', 'N/A') in ['N/A', 'Unknown', '']:
        comp['operating_status'] = f.get('status', 'Unknown')
    p['company'] = comp

    contact = p.get('contact', {})
    if contact.get('physical_address', 'N/A') in ['N/A', '']:
        contact['physical_address'] = f.get('physical_address', 'N/A')
    if contact.get('phone', 'N/A') in ['N/A', '']:
        contact['phone'] = f.get('phone', 'N/A')
    p['contact'] = contact

    return p

def process_single_mc_lookup(mc_str: str, api_key: str):
    """Executes a lookup for a single MC string and appends to history if successful."""
    mc_clean = mc_str.strip()
    if not mc_clean:
        return None
        
    fmcsa_data = get_fmcsa_data(mc_clean, api_key)
    dot_number = fmcsa_data.get('dot_number') or fmcsa_data.get('content', {}).get('carrier', {}).get('dotNumber')
    
    if dot_number:
        raw_profile = get_carrier_profile(str(dot_number))
    else:
        raw_profile = {}
        
    profile = merge_fmcsa_and_profile(fmcsa_data, raw_profile)
    
    # Check if already in history to avoid duplicates
    existing_mcs = [item.get('searched_mc') for item in st.session_state['history']]
    if mc_clean not in existing_mcs:
        st.session_state['history'].append(profile)
        
    return profile

def main():
    inject_custom_css()
    render_header()
    
    # Safe retrieval of secrets
    default_webkey = ""
    try:
        if hasattr(st, "secrets") and "FMCSA_WEB_KEY" in st.secrets:
            default_webkey = st.secrets["FMCSA_WEB_KEY"]
    except Exception:
        default_webkey = ""
    
    # Clean Sidebar (Configuration Only)
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

    # Controls Section (Single & Auto-Increment Batch Mode)
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
        stop_btn = st.button('🛑 Stop', kind='secondary', use_container_width=True)
        
    with col_clear:
        st.write("")
        st.write("")
        clear_btn = st.button('🗑️ Clear History', use_container_width=True)

    # Button Action Handlers
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
            # Strip non-digits to get starting integer
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

    # Auto-Increment Execution Loop
    if st.session_state.get('is_auto_running', False):
        curr_mc = st.session_state['current_auto_mc']
        with st.spinner(f"🔄 Auto-Processing MC {curr_mc}... (Click 🛑 Stop to halt)"):
            try:
                process_single_mc_lookup(str(curr_mc), api_key)
                st.session_state['current_auto_mc'] += 1
                time.sleep(1.0) # Brief pause between requests
                st.rerun()
            except Exception as auto_err:
                logger_msg = f"Skipping MC {curr_mc}: {auto_err}"
                st.toast(logger_msg)
                st.session_state['current_auto_mc'] += 1
                st.rerun()

    # Display Master 3D Glass Data Table (All Searched Carriers)
    if st.session_state['history']:
        st.subheader("📊 Searched Carriers Master History")
        render_history_table(st.session_state['history'])
        
        # Latest Carrier Full Details Section
        latest_carrier = st.session_state['history'][-1]
        st.divider()
        st.subheader(f"🔍 Carrier Deep-Dive Profile: {latest_carrier.get('company', {}).get('legal_name', '')}")
        
        render_company_card(latest_carrier.get('company', {}))
            
        col_a, col_b = st.columns(2)
        with col_a:
            render_contact_section(latest_carrier.get('contact', {}))
        with col_b:
            render_operations_section(latest_carrier.get('fleet', {}))
        
        render_safety_section(latest_carrier.get('safety', {}))
            
        col_c, col_d = st.columns(2)
        with col_c:
            render_insurance_section(latest_carrier.get('insurance', {}))
        with col_d:
            render_authority_section(latest_carrier.get('authority', {}))

    st.divider()
    st.markdown(
        "<div style='text-align: center; font-size: 12px; color: #64748B;'>"
        "Disclaimer: Data is sourced from FMCSA QCMobile API & dotsearch.io. Informational use only."
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()
