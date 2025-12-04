# # pages/4_Tenant_History.py
# import streamlit as st
# from bson import ObjectId
# import pandas as pd
# from utils.db import get_buildings, get_flats_by_building, get_building

# st.set_page_config(page_title="Tenant History - Flat Tracker", layout="wide")
# st.title("📜 Tenant History (Past tenants)")

# # Back button
# if st.button("⬅ Back to Flats"):
#     # if a building was selected previously, keep it, otherwise go to buildings
#     if st.session_state.get("selected_building_id"):
#         st.switch_page("pages/2_Flats.py")
#     else:
#         st.switch_page("pages/1_Buildings.py")

# # Choose building dialog
# buildings = get_buildings()
# if not buildings:
#     st.info("No buildings found. Add a building first on the Home page.")
#     st.stop()

# # Build a mapping label -> id for nicer dropdown display
# options = { f"{b.get('name')} ({b.get('address','')})": str(b.get('_id')) for b in buildings }
# labels = list(options.keys())

# selected_label = st.selectbox("Select building to view past tenants", labels, index=0)
# selected_building_id = options[selected_label]

# st.write(f"Showing past tenants for **{selected_label}**")
# st.write("---")

# # Fetch flats for that building
# flats = get_flats_by_building(selected_building_id)

# rows = []
# for f in flats:
#     flat_no = f.get("flat_no") or f.get("flat_no", "")
#     floor = f.get("floor", "")
#     bhk = f.get("bhk", "")
#     tenant_history = f.get("tenant_history", []) or []
#     # find entries where move_out is set -> past tenants
#     for entry in tenant_history:
#         move_out = entry.get("move_out")
#         if move_out and str(move_out).strip() != "":
#             rows.append({
#                 "building": selected_label.split(" (")[0],
#                 "flat": flat_no,
#                 "floor": floor,
#                 "bhk": f"{bhk}BHK" if bhk else "",
#                 "tenant_name": entry.get("tenant_name", ""),
#                 "move_in": entry.get("move_in") or "",
#                 "vacated": move_out
#             })

# if not rows:
#     st.info("No past tenants found for this building.")
# else:
#     df = pd.DataFrame(rows)
#     # Normalize column order
#     df = df[["building", "flat", "floor", "bhk", "tenant_name", "move_in", "vacated"]]
#     st.dataframe(df, use_container_width=True)



import streamlit as st
import pandas as pd
from utils.db import get_buildings, get_flats_by_building

st.set_page_config(page_title="Tenant History", layout="wide")
st.title("📜 Past Tenant History")

if st.button("⬅ Back to Flats"):
    st.switch_page("pages/2_Flats.py")

# --- Select building ---
buildings = get_buildings()
if not buildings:
    st.info("No buildings found.")
    st.stop()

building_opts = {b["name"]: str(b["_id"]) for b in buildings}
selected_name = st.selectbox("Select Building", list(building_opts.keys()))
building_id = building_opts[selected_name]

st.write(f"Showing tenant history for **{selected_name}**")
st.write("---")

# --- Gather past tenants ---
rows = []
flats = get_flats_by_building(building_id)

for f in flats:
    flat_no = f.get("flat_no")
    floor = f.get("floor")
    bhk = f.get("bhk")
    tenant_history = f.get("tenant_history", [])

    for entry in tenant_history:
        if entry.get("move_out"):  # past tenants only
            rows.append({
                "Flat": flat_no,
                "Floor": floor,
                "BHK": f"{bhk}BHK" if bhk else "",
                "Tenant Name": entry.get("tenant_name", ""),
                "Phone": entry.get("phone", ""),
                "Move-in": entry.get("move_in", ""),
                "Vacated": entry.get("move_out", "")
            })

if not rows:
    st.info("No past tenants recorded.")
else:
    df = pd.DataFrame(rows)
    df["Vacated"] = pd.to_datetime(df["Vacated"], errors="coerce")
    df = df.sort_values("Vacated", ascending=False)
    st.dataframe(df, use_container_width=True)
