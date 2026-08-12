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

def _get_value(carrier: Dict[str, Any], *keys: str, default: str = "") -> str:
    """Safely retrieve first non-empty value from a list of possible keys."""
    for key in keys:
        val = carrier.get(key)
        if val is not None and str(val).strip() not in ['', 'None', 'N/A']:
            return str(val).strip()
    return default

def _parse_carrier_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and format the carrier data from the FMCSA response.
    """
    content = data.get("content", {})
    if isinstance(content, list) and len(content) > 0:
        carrier = content[0].get("carrier", {})
    elif isinstance(content, dict):
        carrier = content.get("carrier", {})
    else:
        carrier = {}

    # Physical address
    phy_street = _get_value(carrier, "phyStreet", "physicalStreet", "street", default="")
    phy_city = _get_value(carrier, "phyCity", "physicalCity", "city", default="")
    phy_state = _get_value(carrier, "phyState", "physicalState", "state", default="")
    phy_zip = _get_value(carrier, "phyZipcode", "physicalZipcode", "zip", default="")

    address_parts = [p for p in [phy_street, phy_city, phy_state, phy_zip] if p]
    physical_address = ", ".join(address_parts) if address_parts else "N/A"

    # Operating status
    allowed = _get_value(carrier, "allowedToOperate", "allowed_to_operate", default="")
    oos = _get_value(carrier, "outOfService", "out_of_service", default="")
    status = "Unknown"
    if allowed.upper() == "Y":
        status = "Authorized"
    elif oos.upper() == "Y":
        status = "Out of Service"
    elif allowed.upper() == "N":
        status = "Not Authorized"

    # Entity type (try multiple possible keys)
    entity_type = _get_value(
        carrier,
        "entityType",
        "entity_type",
        "carrierType",
        "carrier_type",
        "classification",
        "operationClass",
        default=""
    ).upper()

    # If entity type still empty, try to infer from authority fields
    if not entity_type:
        broker_auth = _get_value(carrier, "brokerAuthorityStatus", "broker_authority", default="")
        common_auth = _get_value(carrier, "commonAuthorityStatus", "common_authority", default="")
        if broker_auth or common_auth:
            # If broker authority exists, likely broker/carrier combo
            entity_type = "BROKER/CARRIER"
        else:
            entity_type = "UNKNOWN"

    # Phone
    phone = _get_value(carrier, "phyPhone", "phone", "telephone", "contactPhone", "phoneNumber", default="N/A")

    # Owner name (try multiple possible keys)
    owner_name = _get_value(carrier, "ownerName", "owner_name", "principalName", "contactName", "contact_name", default="")

    # Email (usually not present, but try)
    email = _get_value(carrier, "email", "emailAddress", "contactEmail", default="")

    # Power units and drivers
    power_units = _get_value(carrier, "powerUnits", "power_units", default="0")
    drivers = _get_value(carrier, "drivers", "driverCount", default="0")

    return {
        "dot_number": _get_value(carrier, "dotNumber", "dot_number", default=""),
        "legal_name": _get_value(carrier, "legalName", "legal_name", default=""),
        "dba_name": _get_value(carrier, "dbaName", "dba_name", default=""),
        "allowed_to_operate": allowed,
        "out_of_service": oos,
        "docket_number": _get_value(carrier, "docketNumber", "docket_number", default=""),
        "physical_address": physical_address,
        "phone": phone if phone != "N/A" else "N/A",
        "status": status,
        "entity_type": entity_type if entity_type else "Unknown",
        "operation_classification": _get_value(carrier, "operationClassification", "operation_classification", default="Unknown"),
        "power_units": power_units,
        "drivers": drivers,
        "email": email if email else "N/A",
        "owner_name": owner_name if owner_name else "N/A",
    }

def _handle_response(response: requests.Response) -> Dict[str, Any]:
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
