import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Carrier Lookup Tool", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC or DOT Number:", placeholder="e.g. 1800000 or 4535979")

def fetch_fmcsa_carrier_data(search_term):
    clean_term = str(search_term).strip().replace("MC", "").replace("mc", "").strip()
    
    # Official FMCSA Public API Endpoint (Query by MC Number)
    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/mc/{clean_term}?webKey=4f03930b80baedfb65a1e78eb3dd9db3d4dca889"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        json_data = response.json()
        content = json_data.get("content", {})
        carrier = content.get("carrier", {}) if content else {}
        
        if carrier:
            mc_num = f"MC {clean_term}"
            name = carrier.get("legalName") or carrier.get("dbaName") or "N/A"
            
            # Determine operating authority / entity type
            allowed = carrier.get("allowedToOperate")
            operating_status = "AUTHORIZED" if allowed == "Y" else ("NOT AUTHORIZED" if allowed == "N" else "INACTIVE")
            
            phone = carrier.get("telephone") or "N/A"
            email = carrier.get("emailAddress") or "N/A"
            
            city = carrier.get("phyCity") or ""
            state = carrier.get("phyState") or ""
            location = f"{city}, {state}".strip(", ") if (city or state) else "N/A"
            
            # Entity classification
            entity_type = "Carrier"
            if carrier.get("brokerAuthorityStatus") == "A":
                entity_type = "Broker"
            elif carrier.get("commonAuthorityStatus") == "A":
                entity_type = "Carrier"
                
            return pd.DataFrame([{
                "MC NUMBER": mc_num,
                "BROKER NAME": name,
                "ENTITY TYPE": entity_type,
                "OPERATING STATUS": operating_status,
                "PHONE NUMBER": phone,
                "EMAIL ADDRESS": email,
                "LOCATION": location,
            }])
            
    return pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Fetching official FMCSA carrier records..."):
        df = fetch_fmcsa_carrier_data(query_input)
        if not df.empty:
            st.success("Successfully fetched carrier profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No records found for this MC/DOT number.")
