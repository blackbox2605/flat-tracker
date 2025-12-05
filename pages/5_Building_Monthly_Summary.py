import streamlit as st
from datetime import datetime
from utils.db import get_buildings, get_flats_by_building, get_bill, save_bill
from utils.billing_utils import calc_water_charge, calc_total_payable

st.set_page_config(page_title="Building Monthly Summary", layout="wide")
st.title("🏘️ Building — Monthly Summary (Bulk Billing Edit)")

def get_prev_month_year(month: int, year: int):
    if month == 1:
        return 12, year - 1
    return month - 1, year

def safe_float(x, default=0.0):
    try: return float(x)
    except: return default

# Select building
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

# Add an extra column for Misc
col_widths = [1.2,1.4,1,1,1,1,1,1.2,1.2,1.2,1.0,1.2]  # added one width for misc (at index 10)
headers = ["Flat","Tenant","Prev Cold","Curr Cold","Prev Hot","Curr Hot","Rate (₹/L)","Water ₹","Electricity ₹","Rent ₹","Misc ₹","Total Due ₹"]
cols = st.columns(col_widths)
for c,h in zip(cols, headers): c.markdown(f"**{h}**")
st.write("---")

flat_ids_in_order = []

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

    r = st.columns(col_widths)

    # Flat → Billing page
    if r[0].button(flat_no, key=f"open_{fid}_{month}_{year}"):
        st.session_state["building_id"] = building_id
        st.session_state["selected_flat_id"] = fid
        st.session_state["billing_month"] = int(month)
        st.session_state["billing_year"] = int(year)
        st.switch_page("pages/3_Billing.py")

    r[1].write(curr_tenant)

    prev_cold_val = r[2].number_input("", value=default_prev_cold, key=k_prev_cold)
    curr_cold_val = r[3].number_input("", value=default_curr_cold, key=k_curr_cold)
    prev_hot_val  = r[4].number_input("", value=default_prev_hot, key=k_prev_hot)
    curr_hot_val  = r[5].number_input("", value=default_curr_hot, key=k_curr_hot)
    rate_val      = r[6].number_input("", value=default_rate, key=k_rate)
    water_units, water_charge = calc_water_charge(prev_cold_val, curr_cold_val, prev_hot_val, curr_hot_val, rate_val)
    r[7].write(f"₹{water_charge:.2f}")
    elec_val      = r[8].number_input("", value=default_elec, key=k_elec)
    rent_val      = r[9].number_input("", value=default_rent, key=k_rent)
    misc_val      = r[10].number_input("", value=default_misc, key=k_misc)
    subtotal = calc_total_payable(rent_val, water_charge, elec_val, misc_val)
    total_due = subtotal + prev_carry
    r[11].markdown(f"**₹{total_due:.2f}**")

st.write("---")

# Save All
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
        total_due = subtotal + prev_carry_val
        pending = max(total_due - paid_val, 0)
        carry_forward = max(paid_val - total_due, 0)

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
            # NEW: misc
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

        # 🔥 Sync monthly summary (recalculate derived fields) after saving.
        from utils.db import update_flat_monthly_summary
        update_flat_monthly_summary(fid, building_id, month, year)

        saved += 1

    st.success(f"Saved {saved} bills successfully!")

if st.button("⬅ Back to Flats"):
    st.session_state["building_id"] = building_id
    st.switch_page("pages/2_Flats.py")
