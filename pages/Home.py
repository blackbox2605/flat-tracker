# # pages/1_Home.py
# import streamlit as st
# from utils.db import buildings_col

# st.set_page_config(page_title="Home - Flat Tracker")
# st.title("🏠 Home — Buildings")

# st.subheader("Add Building")
# with st.form("add_building"):
#     name = st.text_input("Building name", "")
#     address = st.text_input("Address (optional)", "")
#     submit = st.form_submit_button("Create Building")
#     if submit:
#         if not name.strip():
#             st.error("Please enter a building name.")
#         else:
#             buildings_col.insert_one({
#                 "name": name.strip(),
#                 "address": address.strip(),
#                 "created_at": None
#             })
#             st.success(f"Building '{name.strip()}' created.")
#             # store last created in session for convenience
#             st.session_state["last_created_building"] = name.strip()
#             # optional immediate navigation: set session_state and switch
#             # (user can also click Open)
#             st.rerun()

# st.subheader("Existing Buildings")
# buildings = list(buildings_col.find().sort("name", 1))
# if not buildings:
#     st.info("No buildings yet. Add one above.")
# else:
#     for b in buildings:
#         cols = st.columns([6,1,1])
#         cols[0].markdown(f"**{b.get('name')}**  \n_{b.get('address','')}_")
#         if cols[1].button("Open", key=f"open_{b['_id']}"):
#             st.session_state["building_id"] = str(b["_id"])
#             st.session_state["building_name"] = b.get("name")
#             st.rerun()
#         if cols[2].button("Delete", key=f"del_{b['_id']}"):
#             buildings_col.delete_one({"_id": b["_id"]})
#             st.success("Deleted.")
#             st.rerun()


import streamlit as st

st.title("Flat Tracker")

if st.button("Buildings"):
    st.switch_page("pages/1_Buildings.py")

if st.button("Billing"):
    st.switch_page("pages/3_Billing.py")

if st.button("Tenant History"):
    st.switch_page("pages/4_Tenant_History.py")
