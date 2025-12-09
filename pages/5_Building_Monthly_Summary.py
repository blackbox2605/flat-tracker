# pages/5_Building_Monthly_Summary.py
import streamlit as st
st.set_page_config(page_title="Building Monthly Summary", layout="wide")
from datetime import datetime
from utils.db import get_buildings, get_flats_by_building, get_bill, save_bill
from utils.billing_utils import calc_water_charge, calc_total_payable

st.title("🏘️ Building — Monthly Summary (Bulk Billing Edit)")

def get_prev_month_year(month: int, year: int):
    if month == 1:
        return 12, year - 1
    return month - 1, year

def safe_float(x, default=0.0):
    try: return float(x)
    except: return default

# ----------------------------
# Sticky header CSS
# ----------------------------
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
    }
    .sticky-header {
        position: sticky;
        top: 0rem;
        background-color: #0d6efd;
        color: white;
        font-weight: bold;
        z-index: 1000;
        display: flex;
        border-bottom: 2px solid #000;
        margin-left: -1rem;
        margin-right: -1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        height: 35px;
        align-items: center;
    }
    .sticky-header span { text-align: center; padding: 0 5px; }
    .sticky-header span:nth-child(1) { flex: 1.2; }
    .sticky-header span:nth-child(2) { flex: 1.4; }
    .sticky-header span:nth-child(3) { flex: 1.0; }
    .sticky-header span:nth-child(4) { flex: 1.0; }
    .sticky-header span:nth-child(5) { flex: 1.0; }
    .sticky-header span:nth-child(6) { flex: 1.0; }
    .sticky-header span:nth-child(7) { flex: 1.0; }
    .sticky-header span:nth-child(8) { flex: 1.2; }
    .sticky-header span:nth-child(9) { flex: 1.2; }
    .sticky-header span:nth-child(10){ flex: 1.2; }
    .sticky-header span:nth-child(11){ flex: 1.0; }
    .sticky-header span:nth-child(12){ flex: 1.2; }

    .stNumberInput div[data-baseweb="input"] input {
        text-align: right !important;
        font-size: 0.9em;
    }
    div[data-baseweb="input"] label { display: none; }
    .stContainer { padding: 5px 0; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# Select building
# ----------------------------
buildings = get_buildings()
if not buildings:
    st.info("No buildings found.")
    st.stop()

building_map = {b["name"]: str(b["_id"]) for b in buildings}
sel_building_name = st.selectbox("Select Building", list(building_map.keys()))
building_id = building_map[sel_building_name]

colm, coly = st.columns([1,1])
month = colm.selectbox("Month", list(range(1,13)), index=datetime.now().month-1)
year = coly.number_input("Year", value=datetime.now().year, step=1)

prev_m, prev_y = get_prev_month_year(month, year)

st.markdown(f"**Building:** {sel_building_name} — **Month:** {month}/{year}")
st.write("---")

flats = get_flats_by_building(building_id)
if not flats:
    st.info("No flats found.")
    st.stop()

# -------------------------------------------------------------
# FILTER occupied flats
# -------------------------------------------------------------
filtered_flats = []
for f in flats:
    tenant_history = f.get("tenant_history", [])
    if not tenant_history:
        continue

    latest = next((t for t in reversed(tenant_history) if not t.get("move_out")), None)
    if not latest:
        continue

    start = latest.get("move_in")
    end   = latest.get("move_out")

    if not start:
        continue

    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end) if end else None

    is_active = (
        (start_dt.year < year or (start_dt.year == year and start_dt.month <= month))
        and
        (end_dt is None or end_dt.year > year or (end_dt.year == year and end_dt.month >= month))
    )
    if is_active:
        filtered_flats.append(f)

flats = filtered_flats

# ----------------------------
# Header row
# ----------------------------
col_widths = [1.2,1.4,1,1,1,1,1,1.2,1.2,1.2,1.0,1.2]
headers = ["Flat","Tenant","Prev Cold","Curr Cold","Prev Hot","Curr Hot","Rate (₹/L)","Water ₹","Electricity ₹","Rent ₹","Misc ₹","Total Due ₹"]

header_html = "<div class='sticky-header'>"
for h in headers:
    header_html += f"<span>{h}</span>"
header_html += "</div>"

st.markdown(header_html, unsafe_allow_html=True)

flat_ids_in_order = []

# ----------------------------
# Tenant Rows
# ----------------------------
for f in flats:
    fid = str(f["_id"])
    flat_ids_in_order.append(fid)
    flat_no = f.get("flat_no", "")
    tenant_history = f.get("tenant_history", [])
    curr_tenant = next((t["tenant_name"] for t in reversed(tenant_history) if not t.get("move_out")), "-")

    existing = get_bill(fid, month, year)
    prev_bill = get_bill(fid, prev_m, prev_y)

    prev_cold_from_prev = safe_float(prev_bill.get("cold_curr",0)) if prev_bill else 0
    prev_hot_from_prev  = safe_float(prev_bill.get("hot_curr",0))  if prev_bill else 0

    default_prev_cold = safe_float(existing.get("cold_prev", prev_cold_from_prev)) if existing else prev_cold_from_prev
    default_prev_hot  = safe_float(existing.get("hot_prev", prev_hot_from_prev))   if existing else prev_hot_from_prev
    default_curr_cold = safe_float(existing.get("cold_curr", default_prev_cold)) if existing else default_prev_cold
    default_curr_hot  = safe_float(existing.get("hot_curr", default_prev_hot))   if existing else default_prev_hot
    default_rate      = safe_float(existing.get("water_rate", f.get("water_rate_per_liter",0))) if existing else safe_float(f.get("water_rate_per_liter",0))
    default_elec      = safe_float(existing.get("electricity",0)) if existing else 0
    default_rent      = safe_float(existing.get("rent", f.get("base_rent",0))) if existing else safe_float(f.get("base_rent",0))
    default_paid      = safe_float(existing.get("amount_paid",0)) if existing else 0
    prev_carry        = safe_float(prev_bill.get("carry_forward",0)) if prev_bill else 0
    default_misc      = safe_float(existing.get("misc", 0)) if existing else 0

    k_prev_cold = f"prev_cold__{fid}__{month}__{year}"
    k_curr_cold = f"curr_cold__{fid}__{month}__{year}"
    k_prev_hot  = f"prev_hot__{fid}__{month}__{year}"
    k_curr_hot  = f"curr_hot__{fid}__{month}__{year}"
    k_rate      = f"rate__{fid}__{month}__{year}"
    k_elec      = f"elec__{fid}__{month}__{year}"
    k_rent      = f"rent__{fid}__{month}__{year}"
    k_paid      = f"paid__{fid}__{month}__{year}"
    k_misc      = f"misc__{fid}__{month}__{year}"

    st.write("---")

    with st.container(border=False):

        r = st.columns(col_widths)

        # --------------------------
        # FIXED INDENTATION STARTS
        # --------------------------

        if r[0].button(flat_no, key=f"open_{fid}_{month}_{year}", use_container_width=True):
            st.session_state["building_id"] = building_id
            st.session_state["selected_flat_id"] = fid
            st.session_state["billing_month"] = int(month)
            st.session_state["billing_year"] = int(year)
            st.switch_page("pages/3_Billing.py")
            st.stop()

        r[1].write(curr_tenant)

        prev_cold_val = r[2].number_input("", value=float(default_prev_cold), key=k_prev_cold, format="%.2f", label_visibility="collapsed")
        curr_cold_val = r[3].number_input("", value=float(default_curr_cold), key=k_curr_cold, format="%.2f", label_visibility="collapsed")
        prev_hot_val  = r[4].number_input("", value=float(default_prev_hot), key=k_prev_hot, format="%.2f", label_visibility="collapsed")
        curr_hot_val  = r[5].number_input("", value=float(default_curr_hot), key=k_curr_hot, format="%.2f", label_visibility="collapsed")
        rate_val      = r[6].number_input("", value=float(default_rate), key=k_rate, format="%.4f", label_visibility="collapsed")

        water_units, water_charge = calc_water_charge(prev_cold_val, curr_cold_val, prev_hot_val, curr_hot_val, rate_val)
        r[7].write(f"₹{water_charge:.2f}")

        elec_val = r[8].number_input("", value=float(default_elec), key=k_elec, format="%.2f", label_visibility="collapsed")
        rent_val = r[9].number_input("", value=float(default_rent), key=k_rent, format="%.2f", label_visibility="collapsed")
        misc_val = r[10].number_input("", value=float(default_misc), key=k_misc, format="%.2f", label_visibility="collapsed")

        r_paid = st.empty().number_input(f"Paid - Flat {fid}", value=float(default_paid), key=k_paid, format="%.2f", label_visibility="collapsed")
        paid_val = r_paid

        subtotal = calc_total_payable(rent_val, water_charge, elec_val, misc_val)
        total_due = subtotal + prev_carry - paid_val

        r[11].markdown(f"**₹{total_due:.2f}**")

        # --------------------------
        # FIXED INDENTATION ENDS
        # --------------------------

st.write("---")

# ----------------------------
# Save All
# ----------------------------
if st.button("💾 Save All Bills"):
    saved = 0
    for fid in flat_ids_in_order:
        prev_cold_val = safe_float(st.session_state.get(f"prev_cold__{fid}__{month}__{year}",0))
        curr_cold_val = safe_float(st.session_state.get(f"curr_cold__{fid}__{month}__{year}",prev_cold_val))
        prev_hot_val  = safe_float(st.session_state.get(f"prev_hot__{fid}__{month}__{year}",0))
        curr_hot_val  = safe_float(st.session_state.get(f"curr_hot__{fid}__{month}__{year}",prev_hot_val))
        rate_val      = safe_float(st.session_state.get(f"rate__{fid}__{month}__{year}",0))
        elec_val      = safe_float(st.session_state.get(f"elec__{fid}__{month}__{year}",0))
        rent_val      = safe_float(st.session_state.get(f"rent__{fid}__{month}__{year}",0))
        paid_val      = safe_float(st.session_state.get(f"paid__{fid}__{month}__{year}",0))
        misc_val      = safe_float(st.session_state.get(f"misc__{fid}__{month}__{year}",0))

        prev_bill = get_bill(fid, prev_m, prev_y)
        prev_carry_val = safe_float(prev_bill.get("carry_forward",0)) if prev_bill else 0

        water_units, water_charge = calc_water_charge(prev_cold_val, curr_cold_val, prev_hot_val, curr_hot_val, rate_val)
        subtotal = calc_total_payable(rent_val, water_charge, elec_val, misc_val)
        total_due = subtotal + prev_carry_val - paid_val
        
        pending = max(0, total_due) 
        carry_forward = total_due 

        doc = {
            "flat_id": fid,
            "building_id": building_id,
            "month": int(month),
            "year": int(year),
            "cold_prev": prev_cold_val,
            "cold_curr": curr_cold_val,
            "hot_prev": prev_hot_val,
            "hot_curr": curr_hot_val,
            "water_rate": rate_val,
            "water_units": water_units,
            "water_charge": water_charge,
            "rent": rent_val,
            "electricity": elec_val,
            "misc": misc_val,
            "subtotal": subtotal,
            "prev_carry": prev_carry_val,
            "total_due": total_due,
            "amount_paid": paid_val,
            "pending": pending,
            "carry_forward": carry_forward,
            "updated_at": datetime.utcnow().isoformat(),
        }

        save_bill(fid, building_id, month, year, doc)
        from utils.db import update_flat_monthly_summary
        update_flat_monthly_summary(fid, building_id, month, year)
        saved += 1

    st.success(f"Saved {saved} bills successfully!")

if st.button("⬅ Back to Flats"):
    st.session_state["building_id"] = building_id
    st.switch_page("pages/2_Flats.py")
