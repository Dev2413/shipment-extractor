
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import io
import re

st.set_page_config(page_title="Amazon Shipment Extractor", layout="wide")
st.title("📦 Amazon Shipment Summary Extractor")

uploaded_files = st.file_uploader("Upload one or more Amazon shipment HTML/txt files", type=["html", "txt"], accept_multiple_files=True)

def extract_numbers(text):
    numbers = re.findall(r'\d+', text)
    return int(numbers[0]) if numbers else None

def extract_shipment_summary(file_content):
    soup = BeautifulSoup(file_content, "html.parser")
    rows = soup.select("kat-table-body kat-table-row")
    data = []

    for row in rows:
        cells = row.find_all("kat-table-cell")
        if len(cells) < 6:
            continue

        msku = cells[0].get_text(strip=True)
        title_block = cells[1]
        title = title_block.find(id="title-col").get_text(strip=True) if title_block.find(id="title-col") else ""
        condition = title_block.find(id="condition-col").get_text(strip=True) if title_block.find(id="condition-col") else ""
        additional_info = cells[2].get_text(separator=", ", strip=True)

        units_expected_block = cells[3].get_text(separator=" ", strip=True)
        units_expected = extract_numbers(units_expected_block)

        units_located_match = re.search(r"Units located \((\d+)\)", units_expected_block)
        units_located = int(units_located_match.group(1)) if units_located_match else None

        discrepancy = None
        if units_expected is not None and units_located is not None:
            discrepancy = units_expected - units_located

        status_div = cells[5].find("div", id="units-located")
        status = status_div.get_text(strip=True) if status_div else "Action required"

        data.append({
            "MSKU": msku,
            "Title": title,
            "Condition": condition,
            "Additional Info": additional_info,
            "Units Expected": units_expected,
            "Units Located": units_located,
            "Discrepancy": discrepancy,
            "Status": status
        })

    return pd.DataFrame(data)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.subheader(f"📄 {uploaded_file.name}")
        content = uploaded_file.read()
        df = extract_shipment_summary(content)
        st.dataframe(df)

        # Export options
        csv = df.to_csv(index=False).encode('utf-8')
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{uploaded_file.name}_summary.csv",
            mime="text/csv"
        )
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"{uploaded_file.name}_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
