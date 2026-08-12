import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import subprocess

# Auto-install Playwright browser binaries on deployment
@st.cache_resource
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Error installing Playwright browser: {e}")

install_playwright_browsers()

st.set_page_config(page_title="DOT Search Scraper", layout="wide")
st.title("Background DOT / Broker Search")

col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Enter Search Term (MC#, Legal Name, Phone, etc.):")
with col2:
    max_results = st.number_input("Max Results", min_value=5, max_value=100, value=20)

def scrape_dotsearch(query, max_items):
    data = []
    with sync_playwright() as p:
        # Launch Chromium headless with sandbox disabled for container compatibility
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
        
        # Fill search box
        search_input = page.wait_for_selector('input[type="text"], input[type="search"]')
        if search_input:
            search_input.fill(query)
            search_input.press("Enter")
        
        # Wait for dynamic table rendering
        time.sleep(3)
        
        rows = page.query_selector_all("table tbody tr")
        for row in rows[:max_items]:
            cols = row.query_selector_all("td")
            if len(cols) >= 7:
                data.append({
                    "MC NUMBER": cols[0].inner_text().strip(),
                    "BROKER NAME": cols[1].inner_text().strip(),
                    "ENTITY TYPE": cols[2].inner_text().strip(),
                    "OPERATING STATUS": cols[3].inner_text().strip(),
                    "PHONE NUMBER": cols[4].inner_text().strip(),
                    "EMAIL ADDRESS": cols[5].inner_text().strip(),
                    "LOCATION": cols[6].inner_text().strip(),
                })
        
        browser.close()
    return pd.DataFrame(data)

if st.button("Run Background Search") and search_query:
    with st.spinner("Fetching background data from dotsearch.io..."):
        try:
            df = scrape_dotsearch(search_query, max_results)
            if not df.empty:
                st.success(f"Retrieved {len(df)} records successfully!")
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No records found for the given search input.")
        except Exception as e:
            st.error(f"Execution Error: {e}")
