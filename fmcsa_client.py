"""
FMCSA QCMobile API Client.
Handles MC number to USDOT number resolution and carrier data retrieval.
"""

import logging
import requests
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

FMCSA_BASE_URL = 'https://mobile.fmcsa.dot.gov/qc/services'
TIMEOUT_SECONDS = 15

class FMCSAError(Exception):
    """Base exception for FMCSA client errors."""
    pass

class FMCSAAuthError(FMCSAError):
    """Raised when authentication fails (e.g., invalid webKey)."""
    pass

class FMCSANotFoundError(FMCSAError):
    """Raised when the requested carrier or docket number is not found."""
    pass

def _parse_carrier_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and format the carrier data from the FMCSA response.
    
    Args:
        data: The raw JSON dictionary from the API response.
        
    Returns:
        A formatted dictionary containing carrier information.
    """
    content = data.get("content", {})
    if isinstance(content, list) and len(content) > 0:
        # In case the content is a list of results (sometimes happens with docket lookups)
        carrier = content[0].get("carrier", {})
    elif isinstance(content, dict):
        carrier = content.get("carrier", {})
    else:
        carrier = {}
    
    phy_street = carrier.get("phyStreet", "")
    phy_city = carrier.get("phyCity", "")
    phy_state = carrier.get("phyState", "")
    phy_zip = carrier.get("phyZipcode", "")
    
    address_parts = [p for p in [phy_street, phy_city, phy_state, phy_zip] if p]
    physical_address = ", ".join(address_parts)
    
    allowed = carrier.get("allowedToOperate", "")
    oos = carrier.get("outOfService", "")
    
    if allowed == "Y":
        status = "Authorized"
    elif oos == "Y":
        status = "Out of Service"
    elif allowed == "N":
        status = "Not Authorized"
    else:
        status = "Unknown"
    
    # Additional fields we can pull
    entity_type = carrier.get("entityType", "")
    operation_class = carrier.get("operationClass", "")
    power_units = carrier.get("powerUnits", "")
    drivers = carrier.get("drivers", "")
    email = carrier.get("email", "")  # May not exist, but we try
    
    return {
        "dot_number": carrier.get("dotNumber"),
        "legal_name": carrier.get("legalName"),
        "dba_name": carrier.get("dbaName"),
        "allowed_to_operate": allowed,
        "out_of_service": oos,
        "docket_number": carrier.get("docketNumber"),
        "physical_address": physical_address,
        "phone": carrier.get("phyPhone"),
        "status": status,
        "entity_type": entity_type,
        "operation_classification": operation_class,
        "power_units": power_units,
        "drivers": drivers,
        "email": email,
    }

def _handle_response(response: requests.Response) -> Dict[str, Any]:
    """
    Handles the HTTP response, raising appropriate exceptions on errors.
    """
    if response.status_code == 401:
        raise FMCSAAuthError("Invalid FMCSA Web Key (401 Unauthorized).")
    elif response.status_code == 404:
        raise FMCSANotFoundError("Carrier or Docket Number not found (404 Not Found).")
    elif not response.ok:
        raise FMCSAError(f"FMCSA API Error: HTTP {response.status_code} - {response.text}")
    
    try:
        data = response.json()
    except ValueError as e:
        raise FMCSAError(f"Failed to parse FMCSA API JSON response: {e}")
        
    return _parse_carrier_response(data)


def resolve_mc_to_usdot(mc_number: str, web_key: str) -> Dict[str, Any]:
    """
    Resolves an MC number to a USDOT number and fetches carrier data.
    
    Args:
        mc_number: The MC number (e.g., 'MC123456', 'MC-123456', or '123456').
        web_key: The FMCSA API web key.
        
    Returns:
        A dictionary containing the carrier's parsed data.
        
    Raises:
        ValueError: If the MC number is invalid.
        FMCSAAuthError: On authentication failure.
        FMCSANotFoundError: If not found.
        FMCSAError: On other API errors.
    """
    # Strip 'MC' or 'MC-' prefix
    cleaned_mc = re.sub(r'^MC-?', '', str(mc_number).upper()).strip()
    
    if not cleaned_mc.isdigit():
        raise ValueError(f"Invalid MC number format: {mc_number}. Must be numeric after prefix.")
        
    url = f"{FMCSA_BASE_URL}/carriers/docket-number/{cleaned_mc}"
    params = {"webKey": web_key}
    
    logger.info(f"Resolving MC number: {cleaned_mc}")
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        raise FMCSAError(f"Request to FMCSA API timed out after {TIMEOUT_SECONDS}s.")
    except requests.exceptions.RequestException as e:
        raise FMCSAError(f"Network error calling FMCSA API: {e}")

def get_carrier_by_dot(dot_number: int, web_key: str) -> Dict[str, Any]:
    """
    Fetches carrier data using a USDOT number.
    
    Args:
        dot_number: The USDOT number.
        web_key: The FMCSA API web key.
        
    Returns:
        A dictionary containing the carrier's parsed data.
        
    Raises:
        FMCSAAuthError: On authentication failure.
        FMCSANotFoundError: If not found.
        FMCSAError: On other API errors.
    """
    url = f"{FMCSA_BASE_URL}/carriers/{dot_number}"
    params = {"webKey": web_key}
    
    logger.info(f"Fetching carrier by DOT number: {dot_number}")
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        return _handle_response(response)
    except requests.exceptions.Timeout:
        raise FMCSAError(f"Request to FMCSA API timed out after {TIMEOUT_SECONDS}s.")
    except requests.exceptions.RequestException as e:
        raise FMCSAError(f"Network error calling FMCSA API: {e}")
