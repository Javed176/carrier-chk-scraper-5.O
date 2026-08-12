import sys
import asyncio
import subprocess
import logging
import re
import time
import streamlit as st
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Apply nest_asyncio safely
try:
    import nest_asyncio
    nest_asyncio.apply()
except Exception as e:
    logger.warning(f"nest_asyncio setup warning: {e}")

if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception as e:
        logger.warning(f"Event loop policy warning: {e}")

@st.cache_resource
def install_playwright_browsers():
    """Installs Playwright Chromium browser binary safely using sys.executable."""
    try:
        logger.info("Installing Playwright Chromium browser...")
        res = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=False,
            capture_output=True,
            text=True
        )
        if res.returncode == 0:
            logger.info("Playwright Chromium installed successfully.")
            return True
        else:
            logger.warning(f"Playwright install warning: {res.stderr}")
            return False
    except Exception as e:
        logger.warning(f"Could not run playwright install command: {e}")
        return False

def _safe_extract(soup: BeautifulSoup, selector: str, default: str = 'N/A') -> str:
    """Safely extracts text from a CSS selector."""
    try:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    except Exception:
        pass
    return default

def _extract_by_label(soup: BeautifulSoup, label_text: str, default: str = 'N/A') -> str:
    """
    Attempts to find a label and extract the adjacent or sibling value.
    Handles multiple common HTML structures.
    """
    # First try: find any text node containing the label
    elements = soup.find_all(string=lambda text: text and label_text.lower() in text.lower())
    for element in elements:
        parent = element.parent
        if not parent:
            continue

        # Case 1: label and value are siblings (e.g., <td>Label</td><td>Value</td>)
        if parent.name in ['th', 'td', 'dt', 'span', 'div', 'strong', 'b']:
            sibling = parent.find_next_sibling()
            if sibling and sibling.get_text(strip=True):
                return sibling.get_text(strip=True)

            # Case 2: label and value are in the same element with a colon
            text = parent.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()

            # Case 3: value is inside the parent's parent's next sibling
            if parent.parent:
                parent_sibling = parent.parent.find_next_sibling()
                if parent_sibling and parent_sibling.get_text(strip=True):
                    return parent_sibling.get_text(strip=True)

        # Case 4: label is inside a link (mailto:/tel:)
        if parent.name == 'a':
            href = parent.get('href', '')
            if href.startswith('mailto:'):
                return href.replace('mailto:', '').strip()
            if href.startswith('tel:'):
                return href.replace('tel:', '').strip()

    # Second try: search for label in any element's text and extract nearby text using regex
    text = soup.get_text(separator='\n')
    pattern = re.escape(label_text) + r'\s*[:\n]\s*([^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        if value and value.lower() not in ['n/a', 'none', 'unknown', '']:
            return value

    return default

def _extract_email(soup: BeautifulSoup) -> str:
    """Extract email from mailto links or regex."""
    # mailto link
    try:
        mail_link = soup.find('a', href=lambda h: h and h.startswith('mailto:'))
        if mail_link:
            return mail_link['href'].replace('mailto:', '').strip()
    except Exception:
        pass

    # regex on page text
    text = soup.get_text(separator='\n')
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if match:
        return match.group(0).strip()

    return 'N/A'

def _extract_phone(soup: BeautifulSoup) -> str:
    """Extract phone from tel links or regex."""
    # tel link
    try:
        tel_link = soup.find('a', href=lambda h: h and h.startswith('tel:'))
        if tel_link:
            return tel_link['href'].replace('tel:', '').strip()
    except Exception:
        pass

    # regex for common phone formats
    text = soup.get_text(separator='\n')
    match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if match:
        return match.group(0).strip()

    return 'N/A'

def _extract_owner_name(soup: BeautifulSoup) -> str:
    """
    Extract owner name from 'Officer 1' or 'Owner' labels.
    """
    # Try label 'Officer 1'
    val = _extract_by_label(soup, 'Officer 1', default='')
    if val and val not in ['N/A', 'None', '']:
        return val

    # Try label 'Owner'
    val = _extract_by_label(soup, 'Owner', default='')
    if val and val not in ['N/A', 'None', '']:
        return val

    # Fallback: search for 'Officer 1' and take next line
    text = soup.get_text(separator='\n')
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'officer 1' in line.lower():
            # Next non-empty line
            for j in range(i+1, len(lines)):
                candidate = lines[j].strip()
                if candidate:
                    return candidate
            break

    return 'N/A'

def _extract_entity_type(soup: BeautifulSoup) -> str:
    """
    Extract entity type (Carrier/Broker) using multiple strategies.
    """
    # Try label 'Entity Type'
    val = _extract_by_label(soup, 'Entity Type', default='')
    if val and val.lower() not in ['n/a', 'unknown', '']:
        return val

    # Try label 'Type'
    val = _extract_by_label(soup, 'Type', default='')
    if val and val.lower() in ['carrier', 'broker', 'carrier/broker', 'broker/carrier']:
        return val

    # Fallback: search for standalone 'Broker' or 'Carrier' in page text
    text = soup.get_text(separator='\n')
    if re.search(r'\bBroker\b', text, re.IGNORECASE):
        return 'Broker'
    if re.search(r'\bCarrier\b', text, re.IGNORECASE):
        return 'Carrier'

    return 'Unknown'

def _extract_profile_data(soup: BeautifulSoup) -> dict:
    """Extracts structured profile data from BeautifulSoup object."""
    email = _extract_email(soup)
    phone = _extract_phone(soup)
    owner_name = _extract_owner_name(soup)
    entity_type = _extract_entity_type(soup)

    data = {
        'company': {
            'legal_name': _extract_by_label(soup, 'Legal Name'),
            'dba_name': _extract_by_label(soup, 'DBA Name'),
            'dot_number': _extract_by_label(soup, 'DOT Number', default=_safe_extract(soup, 'h1')),
            'mc_number': _extract_by_label(soup, 'MC Number'),
            'operating_status': _extract_by_label(soup, 'Operating Status'),
            'entity_type': entity_type,
            'operation_classification': _extract_by_label(soup, 'Operation Classification'),
            'owner_name': owner_name,
        },
        'contact': {
            'physical_address': _extract_by_label(soup, 'Physical Address'),
            'mailing_address': _extract_by_label(soup, 'Mailing Address'),
            'phone': phone if phone != 'N/A' else _extract_by_label(soup, 'Phone'),
            'email': email if email != 'N/A' else _extract_by_label(soup, 'Email'),
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

    # Cargo extraction
    try:
        cargo_section = soup.find(string=lambda text: text and 'Cargo' in text and 'Carried' in text)
        if cargo_section and cargo_section.parent:
            container = cargo_section.parent.find_parent('div', class_=lambda c: c and 'card' in c.lower()) or cargo_section.parent.parent
            if container:
                items = container.find_all('li')
                cargo_types = [item.get_text(strip=True) for item in items if item.get_text(strip=True) and len(item.get_text(strip=True)) > 2]
                data['fleet']['cargo_types'] = cargo_types if cargo_types else ['General Freight']
    except Exception as e:
        logger.warning(f"Failed to extract cargo types: {e}")
        data['fleet']['cargo_types'] = ['General Freight']

    return data

def scrape_carrier_profile(dot_number: int) -> dict:
    """Scrapes carrier profile from dotsearch.io for a given DOT number using Playwright sync API."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "error": "Playwright library is missing. Install with: pip install playwright",
            "company": {"legal_name": f"DOT #{dot_number}", "dot_number": str(dot_number)},
        }

    install_playwright_browsers()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-setuid-sandbox'
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            url = f"https://dotsearch.io/dot/{dot_number}"
            logger.info(f"Navigating to {url}")

            try:
                page.goto(url, timeout=30000)
                page.wait_for_load_state('networkidle', timeout=20000)
                page.wait_for_timeout(5000)
            except Exception as nav_e:
                logger.warning(f"Page load timeout/warning: {nav_e}")

            try:
                page.wait_for_selector('div.card, div[class*="card"], h1', timeout=10000)
            except Exception:
                pass

            html_content = page.content()
            context.close()
            browser.close()

            soup = BeautifulSoup(html_content, 'html.parser')
            data = _extract_profile_data(soup)
            data['raw_html'] = html_content
            return data

    except Exception as e:
        logger.error(f"Error scraping DOT {dot_number}: {e}")
        return {
            "error": f"Scraper notice: {str(e)}",
            "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
        }
