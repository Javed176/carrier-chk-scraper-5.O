import streamlit as st
import sys
import asyncio

# Must be the very first Streamlit command
st.set_page_config(
    page_title='MC Carrier Lookup',
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

@st.cache_data(ttl=3600, show_spinner=False)
def get_fmcsa_data(mc_number, api_key):
    return resolve_mc_to_usdot(mc_number, api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_carrier_profile(dot_number):
    return scrape_carrier_profile(dot_number)

def merge_fmcsa_and_profile(fmcsa_data: dict, profile_data: dict) -> dict:
    """Merges FMCSA primary response into profile data as fallbacks for any missing fields."""
    p = profile_data or {}
    f = fmcsa_data or {}
    
    comp = p.get('company', {})
    if comp.get('legal_name', 'N/A') in ['N/A', 'Unknown', '']:
        comp['legal_name'] = f.get('legal_name', 'Unknown Carrier')
    if comp.get('dba_name', 'N/A') in ['N/A', '']:
        comp['dba_name'] = f.get('dba_name', '')
    if comp.get('dot_number', 'N/A') in ['N/A', '']:
        comp['dot_number'] = str(f.get('dot_number', 'N/A'))
    if comp.get('mc_number', 'N/A') in ['N/A', '']:
        comp['mc_number'] = str(f.get('docket_number', 'N/A'))
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
    
    # Sidebar
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
    st.sidebar.subheader('About')
    st.sidebar.markdown(
        "Look up carrier information and safety records using an MC number. "
        "Data is aggregated from FMCSA and dotsearch.io."
    )
    st.sidebar.markdown("[FMCSA Developer Portal](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiAccess)")
    
    st.sidebar.divider()
    st.sidebar.subheader('How It Works')
    st.sidebar.markdown(
        "1. Enter an MC Number.\n"
        "2. The app queries the FMCSA API to resolve the USDOT number.\n"
        "3. It scrapes the detailed carrier profile using the USDOT number.\n"
        "4. The combined data is presented in an easy-to-read dashboard."
    )

    # Main area
    col1, col2 = st.columns([3, 1])
    with col1:
        mc_number = st.text_input('Enter MC Number', placeholder='e.g., 1800000 or MC-1800000')
    with col2:
        st.write("") # Alignment spacing
        st.write("")
        lookup_clicked = st.button('🔍 Lookup Carrier', type='primary', use_container_width=True)

    if lookup_clicked:
        st.session_state['mc_number'] = mc_number
        st.session_state['lookup_triggered'] = True

    if st.session_state.get('lookup_triggered', False):
        mc = st.session_state.get('mc_number', '').strip()
        
        if not api_key:
            st.warning("Please provide an FMCSA WebKey in the sidebar configuration.")
            return
            
        if not mc:
            st.warning("Please enter an MC Number.")
            return

        try:
            with st.spinner('Resolving MC number via FMCSA...'):
                fmcsa_data = get_fmcsa_data(mc, api_key)
                
            render_fmcsa_summary(fmcsa_data)
            
            dot_number = fmcsa_data.get('dot_number') or fmcsa_data.get('content', {}).get('carrier', {}).get('dotNumber')
            if not dot_number:
                raise Exception("USDOT number not found in FMCSA response.")

            with st.spinner('Fetching carrier profile details...'):
                raw_profile = get_carrier_profile(str(dot_number))
            
            profile = merge_fmcsa_and_profile(fmcsa_data, raw_profile)
            
            st.divider()
            
            if "error" in profile and profile["error"]:
                st.info(f"Information: {profile['error']}")
            
            render_company_card(profile.get('company', {}))
                
            col_a, col_b = st.columns(2)
            with col_a:
                render_contact_section(profile.get('contact', {}))
            with col_b:
                render_operations_section(profile.get('fleet', {}))
            
            render_safety_section(profile.get('safety', {}))
                
            col_c, col_d = st.columns(2)
            with col_c:
                render_insurance_section(profile.get('insurance', {}))
            with col_d:
                render_authority_section(profile.get('authority', {}))

        except FMCSAAuthError:
            render_error_card('Invalid API Key', 'The provided FMCSA WebKey is invalid or expired. Please check your configuration in the sidebar.')
        except FMCSANotFoundError:
            render_error_card('MC Number Not Found', f"Could not find a carrier matching MC Number {mc}.")
        except FMCSAError as e:
            render_error_card('FMCSA API Error', str(e))
        except Exception as e:
            render_error_card('Unexpected Error', f"An error occurred: {str(e)}")
                
    st.divider()
    st.markdown(
        "<div style='text-align: center; font-size: 12px; color: gray;'>"
        "Disclaimer: Data is sourced from the FMCSA and dotsearch.io. "
        "This application is for informational purposes only."
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == '__main__':
    main()
