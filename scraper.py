import sys
import asyncio
import logging
import re
import os
import requests
from bs4 import BeautifulSoup
import subprocess
from urllib.parse import quote

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
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

PROXY_URLS = [
    "https://api.allorigins.win/raw?url={}",
    "https://corsproxy.io/?url={}",
]

def _install_playwright_if_needed():
    """Check if Playwright browser exists; if not, install it."""
    cache_dir = os.path.expanduser("~/.cache/ms-playwright")
    if os.path.exists(cache_dir):
        for name in os.listdir(cache_dir):
            if name.startswith("chromium-"):
                chrome_path = os.path.join(cache_dir, name, "chrome-linux", "chrome")
                if os.path.exists(chrome_path):
                    logger.info("Chromium browser already installed.")
                    return True
    try:
        logger.info("Installing Playwright Chromium...")
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
            logger.warning(f"Playwright install failed: {res.stderr}")
            return False
    except Exception as e:
        logger.warning(f"Could not run playwright install: {e}")
        return False

def _extract_by_label(soup: BeautifulSoup, label_text: str, default: str = 'N/A') -> str:
    try:
        for elem in soup.find_all(string=re.compile(re.escape(label_text), re.IGNORECASE)):
            parent = elem.parent
            if not parent:
                continue
            sibling = parent.find_next_sibling()
            if sibling and sibling.get_text(strip=True):
                return sibling.get_text(strip=True)
            text = parent.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip()
            if parent.parent:
                parent_sibling = parent.parent.find_next_sibling()
                if parent_sibling and parent_sibling.get_text(strip=True):
                    return parent_sibling.get_text(strip=True)
            if parent.name in ['th', 'td']:
                next_td = parent.find_next('td')
                if next_td and next_td.get_text(strip=True):
                    return next_td.get_text(strip=True)
    except Exception as e:
        logger.warning(f"Label extraction error for {label_text}: {e}")
    return default

def _extract_email(soup: BeautifulSoup) -> str:
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
    try:
        officer_elem = soup.find(string=re.compile('Officer 1', re.IGNORECASE))
        if officer_elem:
            parent = officer_elem.parent
            if parent:
                sibling = parent.find_next_sibling()
                if sibling and sibling.get_text(strip=True):
                    return sibling.get_text(strip=True)
                if parent.parent:
                    parent_sibling = parent.parent.find_next_sibling()
                    if parent_sibling and parent_sibling.get_text(strip=True):
                        return parent_sibling.get_text(strip=True)
                if parent.name in ['th', 'td']:
                    next_td = parent.find_next('td')
                    if next_td and next_td.get_text(strip=True):
                        return next_td.get_text(strip=True)
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
    try:
        for text in ['Carrier', 'Broker', 'Carrier/Broker', 'Broker/Carrier']:
            found = soup.find(string=re.compile(rf'^{re.escape(text)}$', re.IGNORECASE))
            if found:
                return text
    except Exception:
        pass
    val = _extract_by_label(soup, 'Entity Type', default='')
    if val and val.lower() not in ['n/a', 'unknown', '']:
        return val
    return 'Unknown'

def _parse_html(html_content: str) -> dict:
    soup = BeautifulSoup(html_content, 'html.parser')

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

    if not legal_name or legal_name in ['N/A', 'None', '']:
        h1 = soup.find('h1')
        if h1:
            legal_name = h1.get_text(strip=True)

    return {
        'company': {
            'legal_name': legal_name if legal_name and legal_name != 'N/A' else 'Unknown',
            'dba_name': dba_name if dba_name and dba_name != 'N/A' else '',
            'dot_number': '',
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
        'source': 'requests',
    }

def scrape_with_requests(dot_number: int) -> dict:
    """Try direct requests first."""
    url = f"https://dotsearch.io/dot/{dot_number}"
    logger.info(f"Attempting direct requests scrape for {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        if response.status_code == 200:
            data = _parse_html(response.text)
            if data['contact']['email'] != 'N/A' or data['contact']['phone'] != 'N/A':
                data['company']['dot_number'] = str(dot_number)
                data['source'] = 'direct'
                return data
            else:
                logger.warning("Direct requests returned no email/phone")
        else:
            logger.warning(f"Direct requests HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Direct requests failed: {e}")
    return None

def scrape_with_proxy(dot_number: int) -> dict:
    """Try CORS proxies to bypass IP restrictions."""
    url = f"https://dotsearch.io/dot/{dot_number}"
    encoded_url = quote(url, safe='')
    for proxy_template in PROXY_URLS:
        proxy_url = proxy_template.format(encoded_url)
        logger.info(f"Attempting proxy scrape via {proxy_url}")
        try:
            response = requests.get(proxy_url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                data = _parse_html(response.text)
                if data['contact']['email'] != 'N/A' or data['contact']['phone'] != 'N/A':
                    data['company']['dot_number'] = str(dot_number)
                    data['source'] = f'proxy_{proxy_template.split(".")[0]}'
                    return data
                else:
                    logger.warning(f"Proxy returned no email/phone: {proxy_template}")
            else:
                logger.warning(f"Proxy HTTP {response.status_code}: {proxy_template}")
        except Exception as e:
            logger.warning(f"Proxy failed: {proxy_template}: {e}")
    return None

def scrape_carrier_profile(dot_number: int) -> dict:
    # Try direct requests
    result = scrape_with_requests(dot_number)
    if result:
        return result

    # Try proxies
    result = scrape_with_proxy(dot_number)
    if result:
        return result

    # Fallback to Playwright (requires dependencies)
    logger.info("Falling back to Playwright")
    if not _install_playwright_if_needed():
        return {
            "error": "Playwright browser installation failed. Please try again.",
            "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
            "source": "error",
        }

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "error": "Playwright library is missing. Install with: pip install playwright",
            "company": {"legal_name": f"DOT #{dot_number}", "dot_number": str(dot_number)},
        }

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
                page.wait_for_selector('a[href^="tel:"], a[href^="mailto:"], h1', timeout=20000)
                page.wait_for_timeout(3000)
            except Exception as nav_e:
                logger.warning(f"Page load/wait warning: {nav_e}")

            html_content = page.content()
            context.close()
            browser.close()

            data = _parse_html(html_content)
            data['company']['dot_number'] = str(dot_number)
            data['source'] = 'playwright'
            return data

    except Exception as e:
        logger.error(f"Error scraping DOT {dot_number}: {e}")
        return {
            "error": f"Scraper notice: {str(e)}",
            "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
            "source": "error",
        }
