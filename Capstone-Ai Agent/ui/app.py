

import streamlit as st
import csv
import io
from agent import analyze_transaction, load_rules
from ui.components import render_transaction_card

if "results" not in st.session_state:
    st.session_state["results"] = []

st.title("Fraud Detection Dashboard")

uploaded_file = st.file_uploader("Upload Transactions CSV", type=["csv"])
if uploaded_file is not None:
    if st.button("Analyze Uploaded CSV"):
        with st.spinner("Analyzing uploaded transactions..."):
            try:
                text = uploaded_file.getvalue().decode("utf-8")
                reader = csv.DictReader(io.StringIO(text))
                rows = list(reader)
                if not rows:
                    st.error("CSV file is empty or has no data rows.")
                else:
                    rules = load_rules()
                    results = [analyze_transaction(row, rules) for row in rows]
                    st.session_state["results"] = results
                    st.success(f"Analyzed {len(results)} transactions!")
            except Exception as exc:
                st.error(f"Error parsing CSV: {exc}")

if st.session_state["results"]:
    st.header("Results")
    for result in st.session_state["results"]:
        render_transaction_card(result)
