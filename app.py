import streamlit as st
from utils.db import get_db

st.title("🏢 Flat Tracker App")

db = get_db()
buildings = list(db.buildings.find())

st.header("Buildings")

# --- Add Building ---
with st.form("add_building"):
    name = st.text_input("Building Name")
    if st.form_submit_button("Add Building"):
        if name.strip():
            doc = {"name": name, "created_at": st.timestamp()}
            bid = db.buildings.insert_one(doc).inserted_id

            # store building id and redirect
            st.session_state["building_id"] = str(bid)
            st.success("Building created!")
            st.switch_page("pages/2_Flats.py")

# --- Existing Buildings ---
for b in buildings:
    col1, col2, col3 = st.columns([3,1,1])

    with col1:
        st.write(f"🏢 **{b['name']}**")

    with col2:
        if st.button("Open", key=str(b["_id"])):
            st.session_state["building_id"] = str(b["_id"])
            st.switch_page("pages/2_Flats.py")

    with col3:
        if st.button("Delete", key=str(b["_id"])+"_del"):
            db.buildings.delete_one({"_id": b["_id"]})
            db.flats.delete_many({"building_id": str(b["_id"])})
            st.rerun()
