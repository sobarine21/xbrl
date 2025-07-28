import streamlit as st
import pandas as pd
import tempfile
import os
import base64

from google import genai
from google.generativeai import configure
from google.generativeai import GenerativeModel

# --- Load Gemini API Key from Streamlit Secrets ---
GEMINI_API_KEY = st.secrets["GEMINI_API"]

# --- Helper functions ---

def extract_text_from_pdf(uploaded_file):
    # Try to extract text from PDF using PyPDF2
    try:
        import PyPDF2
    except ImportError:
        st.error("PyPDF2 is not installed. Please run `pip install PyPDF2`.")
        return ""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_excel(uploaded_file):
    # Read Excel to DataFrame, then convert to text
    try:
        xl = pd.ExcelFile(uploaded_file)
        text = ""
        for sheet in xl.sheet_names:
            df = xl.parse(sheet)
            text += f"Sheet: {sheet}\n"
            text += df.to_csv(index=False)
        return text
    except Exception as e:
        st.error(f"Failed to read Excel file: {e}")
        return ""

def generate_xbrl_with_gemini(input_text):
    configure(api_key=GEMINI_API_KEY)
    model = GenerativeModel('gemini-2.5-flash')
    prompt = (
        "You are an expert in financial data and XBRL conversion. "
        "Convert the following data into valid XBRL XML format. "
        "If the data is a financial table, infer the correct tags and contexts. "
        "If the data is textual, extract relevant financial facts and represent them in XBRL. "
        "Output only the XBRL XML. Here is the input:\n\n"
        f"{input_text}"
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error during XBRL generation: {e}")
        return None

def download_button(xml_content, filename):
    b64 = base64.b64encode(xml_content.encode()).decode()
    href = f'<a href="data:text/xml;base64,{b64}" download="{filename}">Download XBRL Output</a>'
    st.markdown(href, unsafe_allow_html=True)

# --- Streamlit UI ---

st.set_page_config(page_title="PDF/Excel to XBRL Converter (AI-powered)", layout="centered")
st.title("📄➡️🧠➡️📑 PDF/Excel to XBRL Converter using Gemini AI")
st.write(
    "Upload a **PDF** or **Excel** file containing financial data. "
    "This app uses Google's Gemini AI model to convert your data into XBRL format."
)

uploaded_file = st.file_uploader("Upload PDF or Excel file", type=["pdf", "xlsx", "xls"])

if uploaded_file:
    filetype = uploaded_file.type
    st.success(f"Uploaded file: {uploaded_file.name}")

    with st.spinner("Extracting data..."):
        if filetype == "application/pdf":
            input_text = extract_text_from_pdf(uploaded_file)
        elif filetype in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
            input_text = extract_text_from_excel(uploaded_file)
        else:
            st.error("Unsupported file type.")
            input_text = None

    if input_text:
        st.subheader("Extracted Data Preview")
        st.code(input_text[:2000] + ("\n... (truncated)" if len(input_text) > 2000 else ""), language="text")

        if st.button("Convert to XBRL"):
            with st.spinner("Converting to XBRL using Gemini AI..."):
                try:
                    xbrl_output = generate_xbrl_with_gemini(input_text)
                    if xbrl_output:
                        st.subheader("Generated XBRL")
                        st.code(xbrl_output[:2000] + ("\n... (truncated)" if len(xbrl_output) > 2000 else ""), language="xml")
                        download_button(xbrl_output, "converted_output.xbrl")
                except Exception as e:
                    st.error(f"Error during XBRL generation: {e}")
    else:
        st.error("Failed to extract data from the uploaded file.")

st.markdown("""
---
Powered by [Google Gemini](https://ai.google.dev/) and [Streamlit](https://streamlit.io/)
""")
