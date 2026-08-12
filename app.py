import os
import time
import pandas as pd
import streamlit as st

# Ensure Playwright browser binaries are present on Streamlit Cloud
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright

st.set_page_config(page_title="MC Lookup Tool", layout="wide")
st.title("MC Number Background Search")

col1, col2 = st.columns([3, 1])
with col1:
    raw_mc_input = st.text_input("Enter MC Number:", placeholder="e.g. 1800000 or MC-1800000")
with col2:
    max_results = st.number_input("Max Results", min_value=5, max_value=100, value=20)

def search_by_mc(query, max_items):
    # Sanitize and format MC input to match dotsearch expectations
    clean_query = str(query).strip().upper()
    if not clean_query.startswith("MC"):
        clean_query = f"MC-{clean_query}"
        
    data = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        page = browser.new_page()
        page.goto("https://www.dotsearch.io/", wait_until="networkidle")
        
        # Locate search input element
        search_input = page.wait_for_selector('input[type="text"], input[type="search"]')
        if search_input:
            search_input.fill(clean_query)
            search_input.press("Enter")
        
        # Wait until loading spinner disappears or table populates
        try:
            page.wait_for_selector("table tbody tr", timeout=8000)
        except Exception:
            pass  # Fallthrough to extract whatever is present
        
        time.sleep(2)
        
        # Extract row elements
        rows = page.query_selector_all("table tbody tr")
        
        for row in rows[:max_items]:
            cols = row.query_selector_all("td")
            if len(cols) >= 7:
                data.append({
                    "MC NUMBER": cols[0].inner_text().strip(),
                    "CARRIER / BROKER NAME": cols[1].inner_text().strip(),
                    "ENTITY TYPE": cols[2].inner_text().strip(),
                    "OPERATING STATUS": cols[3].inner_text().strip(),
                    "PHONE NUMBER": cols[4].inner_text().strip(),
                    "EMAIL ADDRESS": cols[5].inner_text().strip(),
                    "LOCATION": cols[6].inner_text().strip(),
                })
        
        browser.close()
        
    return pd.DataFrame(data)

if st.button("Search MC") and raw_mc_input:
    with st.spinner("Executing background search on dotsearch.io..."):
        try:
            df = search_by_mc(raw_mc_input, max_results)
            if not df.empty:
                st.success(f"Retrieved {len(df)} matching record(s)!")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No records found. Please check if the MC number is active on FMCSA/dotsearch.io.")
        except Exception as e:
            st.error(f"Search Execution Error: {e}")
