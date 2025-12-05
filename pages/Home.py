# Home.py
import streamlit as st

st.set_page_config(page_title="Flat Tracker", layout="centered")

st.title("🏠 Flat & Billing Tracker")
st.write("""
Welcome to the **Flat & Billing Tracker**.

Use the buttons below or the sidebar to navigate:
""")

st.write("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏢 Buildings"):
        st.switch_page("pages/1_Buildings.py")

with col2:
    if st.button("💳 Billing"):
        st.switch_page("pages/3_Billing.py")

with col3:
    if st.button("📜 Tenant History"):
        st.switch_page("pages/4_Tenant_History.py")

st.write("---")
st.write("A simple home page for easy navigation.")


