import os
import time
import pandas as pd
import streamlit as st

# Install Playwright browser binaries on startup
os.system("playwright install chromium")

from playwright.sync_api import sync_playwright

st.set_page_config(page_title="MC Lookup Tool", layout="wide")
st.title("MC Number Background Search")

col1, col2 = st.columns([3, 1])
with col1:
    mc_number = st.text_input("Enter MC Number:", placeholder="e.g. 1800000")
with col2:
    max_results = st.number_input("Max Results", min_value=5, max_value=100, value=20)

def search_by_mc(mc_query, max_items):
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
        page.goto("https://www.dotsearch.io/", wait_until="domcontentloaded")
        
        # Locate the search input box
        search_input = page.wait_for_selector('input[type="text"], input[type="search"]')
        if search_input:
            search_input.fill(str(mc_query).strip())
            search_input.press("Enter")
        
        # Give the page time to fetch XHR data from FMCSA/MOTUS
        time.sleep(4)
        
        # Extract rows from the result table
        rows = page.query_selector_all("table tbody tr")
        for row in rows[:max_items]:
            cols = row.query_selector_all("td")
            if len(cols) >= 7:
                data.append({
                    "MC NUMBER": cols[0].inner_text().strip(),
                    "BROKER / CARRIER NAME": cols[1].inner_text().strip(),
                    "ENTITY TYPE": cols[2].inner_text().strip(),
                    "OPERATING STATUS": cols[3].inner_text().strip(),
                    "PHONE NUMBER": cols[4].inner_text().strip(),
                    "EMAIL ADDRESS": cols[5].inner_text().strip(),
                    "LOCATION": cols[6].inner_text().strip(),
                })
        
        browser.close()
    return pd.DataFrame(data)

if st.button("Search MC") and mc_number:
    with st.spinner(f"Searching dotsearch.io for MC #{mc_number}..."):
        try:
            df = search_by_mc(mc_number, max_results)
            if not df.empty:
                st.success(f"Found {len(df)} matching record(s)!")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No records found for this MC Number.")
        except Exception as e:
            st.error(f"Search error: {e}")
