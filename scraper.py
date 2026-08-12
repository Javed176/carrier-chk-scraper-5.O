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

def _extract_text_after_label(page, label: str) -> str:
    """
    Uses Playwright locator to find an element containing the exact label text,
    then returns the text of the next sibling or the next line in the parent's text.
    """
    try:
        # Find element containing the label text (case-insensitive)
        locator = page.locator(f'text="{label}"').first
        if locator.count() == 0:
            # Try regex
            locator = page.locator(f'text=/{label}/i').first
            if locator.count() == 0:
                return 'N/A'

        # Get the parent element's text (includes label and possibly value)
        parent = locator.locator('..')
        parent_text = parent.inner_text().strip()
        lines = parent_text.split('\n')

        for i, line in enumerate(lines):
            if label.lower() in line.lower():
                # Look for value in next non-empty line
                for j in range(i + 1, len(lines)):
                    candidate = lines[j].strip()
                    if candidate and candidate.lower() not in ['n/a', 'none', '']:
                        return candidate
                # Also check if value is in same line after colon
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) > 1 and parts[1].strip():
                        return parts[1].strip()

        # Fallback: find next sibling element's text
        sibling = locator.locator('xpath=following-sibling::*[1]')
        if sibling.count() > 0:
            return sibling.inner_text().strip()

    except Exception as e:
        logger.warning(f"Error extracting after label {label}: {e}")
    return 'N/A'

def _extract_entity_type(page) -> str:
    """Extract entity type using the page's visible text."""
    try:
        body_text = page.locator('body').inner_text()
        # Look for standalone 'Broker' or 'Carrier' lines
        for line in body_text.split('\n'):
            stripped = line.strip().lower()
            if stripped == 'carrier':
                return 'Carrier'
            elif stripped == 'broker':
                return 'Broker'
            elif stripped in ['carrier/broker', 'broker/carrier']:
                return 'Broker/Carrier'
        # Also check for patterns like 'Entity Type: Carrier'
        match = re.search(r'Entity\s*Type\s*:\s*([^\n]+)', body_text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val:
                return val
    except Exception as e:
        logger.warning(f"Entity type extraction error: {e}")
    return 'Unknown'

def _extract_phone(page) -> str:
    """Extract phone number from tel links or visible text."""
    # Try tel: link first
    try:
        tel_locator = page.locator('a[href^="tel:"]')
        if tel_locator.count() > 0:
            href = tel_locator.first.get_attribute('href')
            return href.replace('tel:', '').strip()
    except Exception:
        pass

    # Regex on body text
    try:
        body_text = page.locator('body').inner_text()
        match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', body_text)
        if match:
            return match.group(0).strip()
    except Exception:
        pass
    return 'N/A'

def _extract_email(page) -> str:
    """Extract email from mailto links or regex."""
    try:
        mail_locator = page.locator('a[href^="mailto:"]')
        if mail_locator.count() > 0:
            href = mail_locator.first.get_attribute('href')
            return href.replace('mailto:', '').strip()
    except Exception:
        pass

    try:
        body_text = page.locator('body').inner_text()
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', body_text)
        if match:
            return match.group(0).strip()
    except Exception:
        pass
    return 'N/A'

def _extract_owner_name(page) -> str:
    """Extract owner name from 'Officer 1' or 'Owner' labels."""
    # Try exact label 'Officer 1'
    val = _extract_text_after_label(page, 'Officer 1')
    if val != 'N/A':
        return val

    # Try 'Owner'
    val = _extract_text_after_label(page, 'Owner')
    if val != 'N/A':
        return val

    return 'N/A'

def scrape_carrier_profile(dot_number: int) -> dict:
    """Scrapes carrier profile from dotsearch.io using Playwright."""
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
                # Wait for a known label to appear
                page.wait_for_selector('text=Phone', timeout=15000)
                page.wait_for_load_state('networkidle', timeout=20000)
                page.wait_for_timeout(3000)
            except Exception as nav_e:
                logger.warning(f"Page load/wait warning: {nav_e}")

            # Extract using Playwright
            legal_name = _extract_text_after_label(page, 'Legal Name')
            dba_name = _extract_text_after_label(page, 'DBA Name')
            mc_number = _extract_text_after_label(page, 'MC Number')
            operating_status = _extract_text_after_label(page, 'Operating Status')
            entity_type = _extract_entity_type(page)
            phone = _extract_phone(page)
            email = _extract_email(page)
            owner_name = _extract_owner_name(page)
            physical_address = _extract_text_after_label(page, 'Physical Address')
            mailing_address = _extract_text_after_label(page, 'Mailing Address')

            # Fallback to BeautifulSoup if Playwright extraction fails
            if legal_name == 'N/A' or not physical_address:
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n')
                lines = text.split('\n')
                # Basic fallback: search for labels
                def find_after(label):
                    for i, line in enumerate(lines):
                        if label.lower() in line.lower():
                            for j in range(i + 1, len(lines)):
                                cand = lines[j].strip()
                                if cand:
                                    return cand
                    return 'N/A'
                if legal_name == 'N/A':
                    legal_name = find_after('Legal Name')
                if physical_address == 'N/A':
                    physical_address = find_after('Physical Address')
                if mailing_address == 'N/A':
                    mailing_address = find_after('Mailing Address')
                if dba_name == 'N/A':
                    dba_name = find_after('DBA Name')
                if mc_number == 'N/A':
                    mc_number = find_after('MC Number')

            context.close()
            browser.close()

            return {
                'company': {
                    'legal_name': legal_name if legal_name != 'N/A' else 'Unknown',
                    'dba_name': dba_name if dba_name != 'N/A' else '',
                    'dot_number': str(dot_number),
                    'mc_number': mc_number if mc_number != 'N/A' else '',
                    'operating_status': operating_status if operating_status != 'N/A' else 'Unknown',
                    'entity_type': entity_type if entity_type != 'Unknown' else 'Unknown',
                    'owner_name': owner_name if owner_name != 'N/A' else 'N/A',
                },
                'contact': {
                    'physical_address': physical_address if physical_address != 'N/A' else 'N/A',
                    'mailing_address': mailing_address if mailing_address != 'N/A' else '',
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
