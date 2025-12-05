#Home.py
import streamlit as st

st.title("Flat Tracker")

if st.button("Buildings"):
    st.switch_page("pages/1_Buildings.py")

if st.button("Billing"):
    st.switch_page("pages/3_Billing.py")

if st.button("Tenant History"):
    st.switch_page("pages/4_Tenant_History.py")
