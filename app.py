import streamlit as st
import sys
import asyncio

# Page config must be the first Streamlit command
st.set_page_config(
    page_title='MC Carrier Lookup',
    page_icon='🚛',
    layout='wide',
    initial_sidebar_state='expanded'
)

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

# Set Windows event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@st.cache_data(ttl=3600, show_spinner=False)
def get_fmcsa_data(mc_number, api_key):
    return resolve_mc_to_usdot(mc_number, api_key)

@st.cache_data(ttl=3600, show_spinner=False)
def get_carrier_profile(dot_number):
    return scrape_carrier_profile(dot_number)

def main():
    inject_custom_css()
    render_header()
    
    # Sidebar
    st.sidebar.title('🚛 MC Carrier Lookup')
    st.sidebar.divider()
    
    st.sidebar.subheader('Configuration')
    api_key = st.sidebar.text_input(
        'FMCSA WebKey', 
        type='password', 
        value=st.secrets.get('FMCSA_WEB_KEY', ''), 
        help='Get your free key at mobile.fmcsa.dot.gov'
    )
    
    st.sidebar.divider()
    st.sidebar.subheader('About')
    st.sidebar.markdown(
        "Look up carrier information and safety records using an MC number. "
        "Data is aggregated from FMCSA and online sources."
    )
    st.sidebar.markdown("[FMCSA Developer Portal](https://mobile.fmcsa.dot.gov/developer)")
    
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
            
            # Assuming dot_number is available in fmcsa_data
            dot_number = fmcsa_data.get('dot_number') or fmcsa_data.get('content', {}).get('carrier', {}).get('dotNumber')
            if not dot_number:
                raise Exception("USDOT number not found in FMCSA response.")

            with st.spinner('Scraping carrier profile from dotsearch.io...'):
                profile = get_carrier_profile(str(dot_number))
            
            st.divider()
            
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
            render_error_card('Invalid API Key', 'The provided FMCSA WebKey is invalid or expired. Please check your configuration.')
        except FMCSANotFoundError:
            render_error_card('MC Number Not Found', f"Could not find a carrier with MC Number {mc}.")
        except FMCSAError as e:
            render_error_card('FMCSA API Error', str(e))
        except Exception as e:
            err_msg = str(e).lower()
            if 'scrape' in err_msg or 'playwright' in err_msg or 'timeout' in err_msg:
                render_error_card('Scraping Error', f"Failed to retrieve profile data from dotsearch.io. Please try again later. Details: {str(e)}")
            else:
                render_error_card('Unexpected Error', f"An unexpected error occurred: {str(e)}")
                
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
