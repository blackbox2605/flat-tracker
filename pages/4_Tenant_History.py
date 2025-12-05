#4_Tenant_History.py    
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
