import sys
import asyncio
import subprocess
import logging
import time
import streamlit as st
from bs4 import BeautifulSoup
import nest_asyncio

# Apply nest_asyncio to allow nested event loops in Streamlit
nest_asyncio.apply()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def install_playwright_browsers():
    """Installs playwright browsers (Chromium)."""
    try:
        logger.info("Installing Playwright Chromium browser...")
        subprocess.run(['playwright', 'install', 'chromium'], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Playwright browser: {e.stderr}")
        return False

@st.cache_resource
def _get_browser():
    """Gets or creates a cached Playwright browser instance."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        args=[
            '--no-sandbox', 
            '--disable-dev-shm-usage', 
            '--disable-gpu', 
            '--disable-setuid-sandbox'
        ]
    )
    return playwright, browser

def _safe_extract(soup: BeautifulSoup, selector: str, default: str = 'N/A') -> str:
    """Safely extracts text from a CSS selector."""
    element = soup.select_one(selector)
    if element:
        return element.get_text(strip=True)
    return default

def _extract_by_label(soup: BeautifulSoup, label_text: str, default: str = 'N/A') -> str:
    """Attempts to find a label and extract the adjacent or sibling value."""
    # Find any element containing the label text
    elements = soup.find_all(string=lambda text: text and label_text.lower() in text.lower())
    for element in elements:
        parent = element.parent
        if not parent:
            continue
            
        # Case 1: Label and value are in siblings (e.g. <dt>Label</dt><dd>Value</dd>)
        if parent.name in ['th', 'td', 'dt', 'span', 'div', 'strong', 'b']:
            sibling = parent.find_next_sibling()
            if sibling:
                return sibling.get_text(strip=True)
            
            # Case 2: Label and value are in the same element, separated by colon
            text = parent.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
                    
            # Case 3: Parent's parent might contain the value in the next cell (e.g. table row)
            if parent.parent:
                parent_sibling = parent.parent.find_next_sibling()
                if parent_sibling:
                    return parent_sibling.get_text(strip=True)
                
    return default

def _extract_profile_data(soup: BeautifulSoup) -> dict:
    """Extracts structured profile data from BeautifulSoup object."""
    data = {
        'company': {
            'legal_name': _extract_by_label(soup, 'Legal Name'),
            'dba_name': _extract_by_label(soup, 'DBA Name'),
            'dot_number': _extract_by_label(soup, 'DOT Number', default=_safe_extract(soup, 'h1')),
            'mc_number': _extract_by_label(soup, 'MC Number'),
            'operating_status': _extract_by_label(soup, 'Operating Status'),
            'entity_type': _extract_by_label(soup, 'Entity Type'),
            'operation_classification': _extract_by_label(soup, 'Operation Classification'),
        },
        'contact': {
            'physical_address': _extract_by_label(soup, 'Physical Address'),
            'mailing_address': _extract_by_label(soup, 'Mailing Address'),
            'phone': _extract_by_label(soup, 'Phone'),
            'email': _extract_by_label(soup, 'Email'),
        },
        'fleet': {
            'power_units': _extract_by_label(soup, 'Power Units'),
            'drivers': _extract_by_label(soup, 'Drivers'),
            'cargo_types': [], 
        },
        'safety': {
            'safety_rating': _extract_by_label(soup, 'Safety Rating'),
            'rating_date': _extract_by_label(soup, 'Rating Date'),
            'total_inspections': _extract_by_label(soup, 'Total Inspections'),
            'vehicle_oos_pct': _extract_by_label(soup, 'Vehicle OOS'),
            'driver_oos_pct': _extract_by_label(soup, 'Driver OOS'),
            'total_crashes': _extract_by_label(soup, 'Total Crashes'),
            'fatal_crashes': _extract_by_label(soup, 'Fatal Crashes'),
        },
        'insurance': {
            'bipd_required': _extract_by_label(soup, 'BIPD Required'),
            'bipd_on_file': _extract_by_label(soup, 'BIPD on File'),
            'cargo_required': _extract_by_label(soup, 'Cargo Required'),
            'cargo_on_file': _extract_by_label(soup, 'Cargo on File'),
            'bond_required': _extract_by_label(soup, 'Bond Required'),
            'bond_on_file': _extract_by_label(soup, 'Bond on File'),
        },
        'authority': {
            'common_authority': _extract_by_label(soup, 'Common Authority'),
            'contract_authority': _extract_by_label(soup, 'Contract Authority'),
            'broker_authority': _extract_by_label(soup, 'Broker Authority'),
        },
    }
    
    # Try to extract cargo types defensively
    try:
        cargo_section = soup.find(string=lambda text: text and 'Cargo' in text and 'Carried' in text)
        if cargo_section and cargo_section.parent:
            container = cargo_section.parent.find_parent('div', class_=lambda c: c and 'card' in c.lower()) or cargo_section.parent.parent
            if container:
                items = container.find_all('li')
                cargo_types = [item.get_text(strip=True) for item in items if item.get_text(strip=True) and len(item.get_text(strip=True)) > 2]
                if cargo_types:
                    data['fleet']['cargo_types'] = cargo_types
                else:
                    data['fleet']['cargo_types'] = ['N/A']
    except Exception as e:
        logger.warning(f"Failed to extract cargo types: {e}")
        data['fleet']['cargo_types'] = ['N/A']

    return data

def scrape_carrier_profile(dot_number: int) -> dict:
    """Scrapes carrier profile from dotsearch.io for a given DOT number."""
    install_playwright_browsers()
    
    playwright, browser = _get_browser()
    context = None
    
    try:
        # Create a new context with a realistic User-Agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        url = f"https://dotsearch.io/dot/{dot_number}"
        logger.info(f"Navigating to {url}")
        
        page.goto(url)
        page.wait_for_load_state('networkidle', timeout=30000)
        
        # Wait briefly for any remaining dynamic content
        time.sleep(2.5)
        
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = _extract_profile_data(soup)
        data['raw_html'] = html_content
        return data
        
    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout while scraping DOT {dot_number}: {e}")
        return {"error": "Timeout while loading the page", "raw_html": ""}
    except Exception as e:
        logger.error(f"Error while scraping DOT {dot_number}: {e}")
        return {"error": str(e), "raw_html": ""}
    finally:
        if context:
            context.close()
