# pages/1_Buildings.py
import streamlit as st
from utils.db import get_buildings, add_building, get_building, get_db
from utils.db import delete_building   # ADD THIS AT TOP
st.set_page_config(page_title="Buildings - Flat Tracker")

st.title("🏠 Buildings")

# Add building form
with st.form("add_building"):
    name = st.text_input("Building name")
    address = st.text_input("Address (optional)")
    submit = st.form_submit_button("Create building")
    if submit:
        if not name.strip():
            st.error("Please give a building name.")
        else:
            bid = add_building(name.strip(), address.strip())
            st.success("Building created.")
            # store selection in session and go to flats page
            st.session_state["building_id"] = bid
            st.session_state["building_name"] = name.strip()
            st.rerun()

st.write("---")
st.header("Existing buildings")
buildings = get_buildings()
if not buildings:
    st.info("No buildings yet.")
else:
    for b in buildings:
        cols = st.columns([6,1,1])
        # show readable name + address
        cols[0].markdown(f"**{b.get('name')}**  \n_{b.get('address','')}_")
        # use stringified id as key so it's stable
        bid_str = str(b["_id"])
        if cols[1].button("Open", key=f"open_{bid_str}"):
            st.session_state["building_id"] = bid_str
            st.session_state["building_name"] = b.get("name")
            st.switch_page("pages/2_Flats.py")
        if cols[2].button("Delete", key=f"del_{bid_str}"):
            delete_building(bid_str)   # USE THE CENTRALIZED CLEAN DELETE FUNCTION
            st.success("Building deleted.")
            st.rerun()

