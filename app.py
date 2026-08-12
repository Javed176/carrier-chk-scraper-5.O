import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="MOTUS / DOT Search", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC Number:", placeholder="e.g. 1800000")

def get_motus_profile(mc_number):
    clean_mc = re.sub(r"\D", "", str(mc_number))
    if not clean_mc:
        return pd.DataFrame()
        
    session = requests.Session()
    
    # Heavy anti-bot headers to help bypass cloud WAF blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }

    dot_number = None
    
    # STRATEGY 1: The Direct /mc/ Route Bypass on dotsearch.io
    mc_route_url = f"https://www.dotsearch.io/mc/{clean_mc}"
    try:
        mc_res = session.get(mc_route_url, headers=headers, timeout=10, allow_redirects=True)
        if mc_res.status_code == 200 and "DOT" in mc_res.text:
            soup = BeautifulSoup(mc_res.text, "html.parser")
            dot_badge = soup.find(string=re.compile(r"DOT\s*#?\s*\d+", re.I))
            if dot_badge:
                dot_match = re.search(r"\d+", dot_badge)
                if dot_match:
                    dot_number = dot_match.group(0)
                    st.info(f"✅ Resolved via Strategy 1 (dotsearch.io direct routing): DOT {dot_number}")
    except Exception as e:
        st.warning(f"Strategy 1 Failed to connect: {e}")

    # STRATEGY 2: FMCSA QCMobile API with spoofed headers
    if not dot_number:
        fmcsa_url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{clean_mc}?webKey=4f03930b80baedfb65a1e78eb3dd9db3d4dca889"
        try:
            fmcsa_res = session.get(fmcsa_url, headers=headers, timeout=10)
            if fmcsa_res.status_code == 200:
                data = fmcsa_res.json()
                content = data.get("content", [])
                if isinstance(content, dict):
                    content = [content]
                for item in content:
                    carrier = item.get("carrier", item)
                    if carrier and carrier.get("dotNumber"):
                        dot_number = str(carrier.get("dotNumber"))
                        st.info(f"✅ Resolved via Strategy 2 (FMCSA API): DOT {dot_number}")
                        break
            else:
                # This exposes the exact WAF block error to your screen
                st.error(f"❌ Strategy 2 Failed: FMCSA API blocked the request. HTTP Status: {fmcsa_res.status_code}")
        except Exception as e:
            st.error(f"Strategy 2 Connection Error: {e}")

    # If both resolution strategies fail, stop execution
    if not dot_number:
        st.error("🚨 Critical Failure: Could not resolve MC number to DOT number. The cloud IP is likely being actively blocked by the FMCSA WAF, or the MC doesn't exist.")
        return pd.DataFrame()

    # Step 3: Fetch MOTUS data from dotsearch.io using the resolved DOT
    profile_url = f"https://www.dotsearch.io/dot/{dot_number}"
    
    try:
        profile_res = session.get(profile_url, headers=headers, timeout=10)
        
        if profile_res.status_code == 200:
            soup = BeautifulSoup(profile_res.text, "html.parser")
            
            name_heading = soup.find("h1")
            company_name = name_heading.get_text(strip=True) if name_heading else "N/A"
            
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
                "MC NUMBER": f"MC {clean_mc}",
                "DOT NUMBER": dot_number,
                "BROKER NAME": company_name,
                "ENTITY TYPE": entity_type,
                "OPERATING STATUS": status,
                "PHONE NUMBER": phone_num,
                "EMAIL ADDRESS": email_addr,
                "LOCATION": location_val,
            }])
        else:
            st.error(f"❌ Failed to load MOTUS profile. dotsearch.io returned HTTP {profile_res.status_code}")

    except Exception as e:
        st.error(f"Error querying dotsearch.io profile HTML: {e}")
        
    return pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Executing bypass strategies to fetch data..."):
        df = get_motus_profile(query_input)
        if not df.empty and df["BROKER NAME"].iloc[0] != "N/A":
            st.success("Successfully loaded MOTUS profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Execution finished, but no valid records were returned.")
