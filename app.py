import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="MOTUS / DOT Search", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC Number:", placeholder="e.g. 1800000")

def get_carrier_profile(mc_number):
    # Clean digits and explicitly format with MC- prefix for dotsearch
    clean_digits = re.sub(r"\D", "", str(mc_number))
    if not clean_digits:
        return pd.DataFrame()
        
    mc_formatted = f"MC-{clean_digits}"
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.dotsearch.io/"
    }
    
    try:
        # Step 1: Send search query with explicit MC- prefix
        search_url = "https://www.dotsearch.io/Home/Search"
        payload = {"searchTerm": mc_formatted}
        
        search_res = session.post(search_url, data=payload, headers=headers, timeout=10)
        
        dot_number = None
        if search_res.status_code == 200:
            try:
                res_json = search_res.json()
                dot_number = res_json.get("dotNumber") or res_json.get("dot_number")
            except Exception:
                # Extract target DOT number from returned redirect path string
                match = re.search(r"dot/(\d+)", search_res.text)
                if match:
                    dot_number = match.group(1)

        # If dotsearch returns the detail page directly or resolved DOT number
        if dot_number:
            profile_url = f"https://www.dotsearch.io/dot/{dot_number}"
        else:
            # Fallback search if resolution path wasn't JSON
            profile_url = f"https://www.dotsearch.io/Home/Search?searchTerm={mc_formatted}"

        # Step 2: Fetch profile HTML
        profile_res = session.get(profile_url, headers=headers, timeout=10)
        
        if profile_res.status_code == 200:
            soup = BeautifulSoup(profile_res.text, "html.parser")
            
            # Extract Company Name
            name_heading = soup.find("h1")
            company_name = name_heading.get_text(strip=True) if name_heading else "N/A"
            
            # Extract Resolved DOT Number from page badges if available
            dot_badge = soup.find(string=re.compile(r"DOT\s*#?\s*\d+", re.I))
            if dot_badge:
                dot_match = re.search(r"\d+", dot_badge)
                if dot_match:
                    dot_number = dot_match.group(0)

            page_text = soup.get_text()
            
            entity_type = "Broker" if "Broker" in page_text else ("Carrier" if "Carrier" in page_text else "N/A")
            status = "AUTHORIZED" if "MOTUS" in page_text or "Authorized" in page_text or "Interstate" in page_text else "INACTIVE"
            
            phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", page_text)
            phone_num = phone_match.group(0) if phone_match else "N/A"
            
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", page_text)
            email_addr = email_match.group(0) if email_match else "N/A"
            
            loc_match = re.search(r"([A-Z\s]+,\s*[A-Z]{2})", page_text)
            location_val = loc_match.group(1).strip() if loc_match else "N/A"

            return pd.DataFrame([{
                "MC NUMBER": f"MC {clean_digits}",
                "DOT NUMBER": dot_number or "N/A",
                "BROKER NAME": company_name,
                "ENTITY TYPE": entity_type,
                "OPERATING STATUS": status,
                "PHONE NUMBER": phone_num,
                "EMAIL ADDRESS": email_addr,
                "LOCATION": location_val,
            }])

    except Exception as e:
        st.error(f"Error querying dotsearch.io: {e}")
        
    return pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Fetching MOTUS profile for MC number..."):
        df = get_carrier_profile(query_input)
        if not df.empty and df["BROKER NAME"].iloc[0] != "N/A":
            st.success("Successfully loaded MOTUS profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No records found for this MC number on dotsearch.io.")
