import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Carrier Lookup Tool", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC or DOT Number:", placeholder="e.g. 1800000 or 4535979")

def fetch_fmcsa_carrier_data(search_term):
    clean_term = str(search_term).strip().replace("MC", "").replace("mc", "").replace("-", "").strip()
    
    # Official FMCSA QCMobile API Docket Search Endpoint
    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{clean_term}?webKey=4f03930b80baedfb65a1e78eb3dd9db3d4dca889"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            json_data = response.json()
            content = json_data.get("content", [])
            
            # QC Mobile returns a list or single object under content
            if isinstance(content, dict):
                content = [content]
                
            records = []
            for item in content:
                carrier = item.get("carrier", item)
                if carrier:
                    legal_name = carrier.get("legalName") or carrier.get("dbaName") or "N/A"
                    dot_num = carrier.get("dotNumber") or "N/A"
                    allowed = carrier.get("allowedToOperate")
                    
                    status = "AUTHORIZED" if allowed == "Y" else ("NOT AUTHORIZED" if allowed == "N" else "INACTIVE")
                    phone = carrier.get("telephone") or "N/A"
                    email = carrier.get("emailAddress") or "N/A"
                    
                    city = carrier.get("phyCity") or ""
                    state = carrier.get("phyState") or ""
                    location = f"{city}, {state}".strip(", ") if (city or state) else "N/A"
                    
                    entity_type = "Carrier"
                    if carrier.get("brokerAuthorityStatus") == "A":
                        entity_type = "Broker"
                    
                    records.append({
                        "MC NUMBER": f"MC {clean_term}",
                        "BROKER NAME": legal_name,
                        "ENTITY TYPE": entity_type,
                        "OPERATING STATUS": status,
                        "PHONE NUMBER": phone,
                        "EMAIL ADDRESS": email,
                        "LOCATION": location
                    })
                    
            return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Request Error: {e}")
        
    return pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Fetching official FMCSA carrier records..."):
        df = fetch_fmcsa_carrier_data(query_input)
        if not df.empty:
            st.success("Successfully fetched carrier profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No records found for this MC/DOT number.")
