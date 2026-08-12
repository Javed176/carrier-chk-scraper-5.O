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
    """Installs Playwright Chromium browser binary with dependencies."""
    try:
        logger.info("Installing Playwright Chromium browser...")
        res = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
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

def _extract_by_label(soup: BeautifulSoup, label_text: str, default: str = 'N/A') -> str:
    """Generic label-value extractor using BeautifulSoup."""
    try:
        # Find all elements containing the label text
        for elem in soup.find_all(string=re.compile(re.escape(label_text), re.IGNORECASE)):
            parent = elem.parent
            if not parent:
                continue

            # Case 1: label and value are siblings
            sibling = parent.find_next_sibling()
            if sibling and sibling.get_text(strip=True):
                return sibling.get_text(strip=True)

            # Case 2: label and value in same element separated by colon
            text = parent.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()

            # Case 3: value is inside parent's parent's next sibling
            if parent.parent:
                parent_sibling = parent.parent.find_next_sibling()
                if parent_sibling and parent_sibling.get_text(strip=True):
                    return parent_sibling.get_text(strip=True)

            # Case 4: label is in a table cell, value is next cell in same row
            if parent.name in ['th', 'td']:
                next_td = parent.find_next('td')
                if next_td and next_td.get_text(strip=True):
                    return next_td.get_text(strip=True)
    except Exception as e:
        logger.warning(f"Label extraction error for {label_text}: {e}")
    return default

def _extract_email(soup: BeautifulSoup) -> str:
    """Extract email from mailto link or regex."""
    try:
        mail_link = soup.find('a', href=lambda h: h and h.startswith('mailto:'))
        if mail_link:
            return mail_link['href'].replace('mailto:', '').strip()
    except Exception:
        pass
    try:
        text = soup.get_text(separator='\n')
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if match:
            return match.group(0).strip()
    except Exception:
        pass
    return 'N/A'

def _extract_phone(soup: BeautifulSoup) -> str:
    """Extract phone from tel link or regex."""
    try:
        tel_link = soup.find('a', href=lambda h: h and h.startswith('tel:'))
        if tel_link:
            return tel_link['href'].replace('tel:', '').strip()
    except Exception:
        pass
    try:
        text = soup.get_text(separator='\n')
        match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if match:
            return match.group(0).strip()
    except Exception:
        pass
    return 'N/A'

def _extract_owner_name(soup: BeautifulSoup) -> str:
    """Extract owner name from 'Officer 1' label."""
    try:
        # Find element containing 'Officer 1'
        officer_elem = soup.find(string=re.compile('Officer 1', re.IGNORECASE))
        if officer_elem:
            parent = officer_elem.parent
            if parent:
                # Try next sibling first
                sibling = parent.find_next_sibling()
                if sibling and sibling.get_text(strip=True):
                    return sibling.get_text(strip=True)

                # Try parent's next sibling
                if parent.parent:
                    parent_sibling = parent.parent.find_next_sibling()
                    if parent_sibling and parent_sibling.get_text(strip=True):
                        return parent_sibling.get_text(strip=True)

                # If parent is a cell, get next cell
                if parent.name in ['th', 'td']:
                    next_td = parent.find_next('td')
                    if next_td and next_td.get_text(strip=True):
                        return next_td.get_text(strip=True)

                # Fallback: look for next line in parent's text
                text = parent.get_text(separator='\n')
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if 'officer 1' in line.lower():
                        for j in range(i+1, len(lines)):
                            cand = lines[j].strip()
                            if cand and cand.lower() not in ['n/a', 'none', '']:
                                return cand
    except Exception as e:
        logger.warning(f"Owner extraction error: {e}")
    return 'N/A'

def _extract_entity_type(soup: BeautifulSoup) -> str:
    """Extract entity type by looking for standalone 'Carrier' or 'Broker' text."""
    try:
        # Look for exact text matches in any tag
        for text in ['Carrier', 'Broker', 'Carrier/Broker', 'Broker/Carrier']:
            found = soup.find(string=re.compile(rf'^{re.escape(text)}$', re.IGNORECASE))
            if found:
                return text
    except Exception:
        pass

    # Fallback: label extraction
    val = _extract_by_label(soup, 'Entity Type', default='')
    if val and val.lower() not in ['n/a', 'unknown', '']:
        return val

    return 'Unknown'

def scrape_carrier_profile(dot_number: int) -> dict:
    """Scrapes carrier profile from dotsearch.io using Playwright and BeautifulSoup."""
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
                # Wait for either a tel link or mail link or h1 to appear
                page.wait_for_selector('a[href^="tel:"], a[href^="mailto:"], h1', timeout=20000)
                page.wait_for_timeout(3000)
            except Exception as nav_e:
                logger.warning(f"Page load/wait warning: {nav_e}")

            html_content = page.content()
            context.close()
            browser.close()

            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract fields
            legal_name = _extract_by_label(soup, 'Legal Name', default='')
            dba_name = _extract_by_label(soup, 'DBA Name', default='')
            mc_number = _extract_by_label(soup, 'MC Number', default='')
            operating_status = _extract_by_label(soup, 'Operating Status', default='')
            physical_address = _extract_by_label(soup, 'Physical Address', default='')
            mailing_address = _extract_by_label(soup, 'Mailing Address', default='')

            entity_type = _extract_entity_type(soup)
            phone = _extract_phone(soup)
            email = _extract_email(soup)
            owner_name = _extract_owner_name(soup)

            # If legal_name is still empty, use h1 or page title
            if not legal_name or legal_name in ['N/A', 'None', '']:
                h1 = soup.find('h1')
                if h1:
                    legal_name = h1.get_text(strip=True)

            return {
                'company': {
                    'legal_name': legal_name if legal_name and legal_name != 'N/A' else 'Unknown',
                    'dba_name': dba_name if dba_name and dba_name != 'N/A' else '',
                    'dot_number': str(dot_number),
                    'mc_number': mc_number if mc_number and mc_number != 'N/A' else '',
                    'operating_status': operating_status if operating_status and operating_status != 'N/A' else 'Unknown',
                    'entity_type': entity_type if entity_type != 'Unknown' else 'Unknown',
                    'owner_name': owner_name if owner_name != 'N/A' else 'N/A',
                },
                'contact': {
                    'physical_address': physical_address if physical_address and physical_address != 'N/A' else 'N/A',
                    'mailing_address': mailing_address if mailing_address and mailing_address != 'N/A' else '',
                    'phone': phone if phone != 'N/A' else 'N/A',
                    'email': email if email != 'N/A' else 'N/A',
                },
                'fleet': {
                    'power_units': 'N/A',
                    'drivers': 'N/A',
                    'cargo_types': [],
                },
                'safety': {},
                'insurance': {},
                'authority': {},
            }

    except Exception as e:
        logger.error(f"Error scraping DOT {dot_number}: {e}")
        return {
            "error": f"Scraper notice: {str(e)}",
            "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
        }
