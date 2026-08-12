import os
import time
import pandas as pd
import streamlit as st

os.system("playwright install chromium")

from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Carrier Detail Scraper", layout="wide")
st.title("MC / DOT Background Search")

query_input = st.text_input("Enter MC or DOT Number:", placeholder="e.g. 1800000 or 4535979")

def scrape_dotsearch_detail(number):
    clean_num = str(number).strip()
    data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        # Step 1: Go to search page and submit query
        page.goto("https://www.dotsearch.io/", wait_until="domcontentloaded")
        search_input = page.wait_for_selector('input[type="text"], input[type="search"]')
        
        if search_input:
            search_input.fill(clean_num)
            search_input.press("Enter")

        # Step 2: Wait for redirection to /dot/<DOT_NUMBER> URL
        time.sleep(3)

        # Step 3: Extract carrier details from the final detail page DOM
        try:
            # Extract Company Name
            name_elem = page.query_selector("h1")
            company_name = name_elem.inner_text().strip() if name_elem else "N/A"

            # Extract MC & DOT numbers from the badges
            dot_num = page.inner_text("text=DOT").strip() if page.query_selector("text=DOT") else "N/A"
            mc_num = page.inner_text("text=MC").strip() if page.query_selector("text=MC") else clean_num

            # Extract Phone & Email under Contact Information
            body_text = page.inner_text("body")
            
            data = {
                "MC NUMBER": mc_num,
                "DOT NUMBER": dot_num,
                "CARRIER / BROKER NAME": company_name,
                "CURRENT URL": page.url
            }
        except Exception as e:
            st.error(f"Error parsing page elements: {e}")

        browser.close()

    return pd.DataFrame([data]) if data else pd.DataFrame()

if st.button("Search") and query_input:
    with st.spinner("Resolving MC to DOT and extracting profile details..."):
        df = scrape_dotsearch_detail(query_input)
        if not df.empty:
            st.success("Successfully fetched company profile!")
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Could not find a carrier matching this number.")
