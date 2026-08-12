import os
import time
import re
import pandas as pd
import streamlit as st

# Ensure Playwright browser binaries are present
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Carrier Lookup Tool", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC or DOT Number:", placeholder="e.g. 1800000 or 4535979")

def scrape_carrier_details(search_term):
    clean_term = str(search_term).strip()
    data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        # Step 1: Open search page
        page.goto("https://www.dotsearch.io/", wait_until="networkidle")

        # Step 2: Fill search box
        search_input = page.wait_for_selector('input[type="text"], input[type="search"]')
        if search_input:
            search_input.fill(clean_term)
            search_input.press("Enter")

        # Step 3: Explicitly wait for navigation away from search home page
        try:
            page.wait_for_url(lambda url: "/dot/" in url or "/search" not in url, timeout=10000)
        except Exception:
            # Fallback direct URL if navigation doesn't trigger automatically
            page.goto(f"https://www.dotsearch.io/dot/{clean_term}", wait_until="networkidle")

        # Give profile elements time to render XHR content
        time.sleep(3)

        # Step 4: Extract parsed profile fields
        try:
            # Company Name (h1 tag)
            name_elem = page.query_selector("h1")
            company_name = name_elem.inner_text().strip() if name_elem else "N/A"

            # Page body text for targeted Regex extraction
            body_text = page.inner_text("body")

            # Extract MC Number badge
            mc_match = re.search(r"MC\s*(\d+)", body_text)
            mc_val = f"MC {mc_match.group(1)}" if mc_match else f"MC {clean_term}"

            # Extract Entity Type (Broker / Carrier / Freight Forwarder)
            entity_type = "Broker" if "Broker" in body_text else ("Carrier" if "Carrier" in body_text else "N/A")

            # Extract Operating Status
            status_match = re.search(r"(Authorized|Active|NOT AUTHORIZED|Inactive)", body_text, re.IGNORECASE)
            operating_status = status_match.group(1).upper() if status_match else "AUTHORIZED"

            # Extract Phone Number
            phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", body_text)
            phone_num = phone_match.group(0) if phone_match else "N/A"

            # Extract Email Address
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", body_text)
            email_addr = email_match.group(0) if email_match else "N/A"

            # Extract Location (City, State)
            location_match = re.search(r"([A-Z\s]+,\s*[A-Z]{2})", body_text)
            location_val = location_match.group(1).strip() if location_match else "N/A"

            data = {
                "MC NUMBER": mc_val,
                "BROKER NAME": company_name,
                "ENTITY TYPE": entity_type,
                "OPERATING STATUS": operating_status,
                "PHONE NUMBER": phone_num,
                "EMAIL ADDRESS": email_addr,
                "LOCATION": location_val,
            }
        except Exception as e:
            st.error(f"DOM Extraction Error: {e}")

        browser.close()

    return pd.DataFrame([data]) if data.get("BROKER NAME") != "N/A" else pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Resolving carrier page and extracting details..."):
        df = scrape_carrier_details(query_input)
        if not df.empty:
            st.success("Successfully fetched company profile!")
            # Render identical table layout
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Could not extract carrier profile. Please double check the MC / DOT number.")
