import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Carrier Lookup Tool", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC or DOT Number:", placeholder="e.g. 1800000 or 4535979")

def fetch_dotsearch_api(search_term):
    clean_term = str(search_term).strip().replace("MC", "").replace("mc", "").strip()
    
    # Target dotsearch.io backend search endpoint directly
    url = f"https://www.dotsearch.io/api/search?q={clean_term}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.dotsearch.io/"
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        results = response.json()
        
        # Handle single dictionary or list of results
        if isinstance(results, dict):
            results = results.get("data", [results]) if "data" in results else [results]
            
        parsed_data = []
        for item in results:
            # Extract fields directly from backend JSON response
            mc_num = item.get("mc_number") or item.get("mcNumber") or f"MC {clean_term}"
            name = item.get("legal_name") or item.get("dba_name") or item.get("name") or "N/A"
            entity = item.get("entity_type") or item.get("entityType") or "Broker"
            status = item.get("operating_status") or item.get("status") or "AUTHORIZED"
            phone = item.get("phone") or item.get("telephone") or "N/A"
            email = item.get("email") or "N/A"
            
            city = item.get("city") or item.get("phyCity") or ""
            state = item.get("state") or item.get("phyState") or ""
            location = f"{city}, {state}".strip(", ") if (city or state) else "N/A"
            
            parsed_data.append({
                "MC NUMBER": mc_num,
                "BROKER NAME": name,
                "ENTITY TYPE": entity,
                "OPERATING STATUS": status,
                "PHONE NUMBER": phone,
                "EMAIL ADDRESS": email,
                "LOCATION": location,
            })
            
        return pd.DataFrame(parsed_data)
    else:
        st.error(f"API Error {response.status_code}")
        return pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Querying dotsearch backend..."):
        df = fetch_dotsearch_api(query_input)
        if not df.empty and df["BROKER NAME"].iloc[0] != "N/A":
            st.success("Successfully fetched company profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No valid records returned for this number.")
