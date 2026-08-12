import sys
import asyncio
import logging
import re
import cloudscraper
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Apply nest_asyncio safely (for compatibility)
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

    # Preview first 2000 characters of HTML for debugging
    html_preview = html_content[:2000]

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
        'source': 'cloudscraper',
        'html_preview': html_preview,
    }

def scrape_carrier_profile(dot_number: int) -> dict:
    url = f"https://dotsearch.io/dot/{dot_number}"
    logger.info(f"Scraping with cloudscraper: {url}")
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            logger.warning(f"Cloudscraper HTTP {response.status_code}")
            return {
                "error": f"HTTP {response.status_code} from dotsearch.io",
                "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
                "source": "error",
            }
        data = _parse_html(response.text)
        data['company']['dot_number'] = str(dot_number)
        return data
    except Exception as e:
        logger.error(f"Cloudscraper failed: {e}")
        return {
            "error": f"Scraper notice: {str(e)}",
            "company": {"legal_name": f"Carrier DOT #{dot_number}", "dot_number": str(dot_number)},
            "source": "error",
        }
