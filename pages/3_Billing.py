#3_Billing.py
import streamlit as st
from bson import ObjectId
from datetime import datetime
from utils.db import flats_col, monthly_bills_col
from utils.billing_utils import calc_water_charge, calc_total_payable

st.set_page_config(page_title="Billing - Flat Tracker")

# -------------------------------------------------------------------
# Helper: Get previous month + year
# -------------------------------------------------------------------
def get_prev_month_year(month: int, year: int):
    if month == 1:
        return 12, year - 1
    return month - 1, year

# --- Ensure building is selected ---
building_id = st.session_state.get("building_id")
if not building_id:
    st.error("Select a building on Home first.")
    st.stop()

st.title("📄 Billing")

# --- Flat selection ---

# flats = list(flats_col.find({"building_id": building_id}).sort("flat_no", 1))
# if not flats:
#     st.info("No flats found.")
#     st.stop()

# flat_map = {str(f["_id"]): f for f in flats}
# options = {f"{f['flat_no']} ({f['bhk']}BHK)": str(f["_id"]) for f in flats}

# selected_label = st.selectbox("Select flat", list(options.keys()))
# selected_flat_id = options[selected_label]
# st.session_state["selected_flat_id"] = selected_flat_id
# flat = flat_map[selected_flat_id]

# st.header(f"Flat {flat['flat_no']} — Billing")

# # --- Month/Year ---
# col1, col2 = st.columns(2)
# month = col1.selectbox("Month", list(range(1, 13)), index=datetime.now().month - 1)
# year = col2.number_input("Year", value=datetime.now().year, step=1)


# --- Flat selection ---
flats = list(flats_col.find({"building_id": building_id}).sort("flat_no", 1))
if not flats:
    st.info("No flats found.")
    st.stop()

flat_map = {str(f["_id"]): f for f in flats}
options = {f"{f['flat_no']} ({f['bhk']}BHK)": str(f["_id"]) for f in flats}

# Pre-select flat from session_state if available
if "selected_flat_id" in st.session_state:
    selected_flat_id = st.session_state["selected_flat_id"]
    # Get label from flat_map
    selected_label = next((lbl for lbl, fid in options.items() if fid == selected_flat_id), list(options.keys())[0])
else:
    selected_label = list(options.keys())[0]
    selected_flat_id = options[selected_label]

selected_label = st.selectbox("Select flat", list(options.keys()), index=list(options.keys()).index(selected_label))
selected_flat_id = options[selected_label]
st.session_state["selected_flat_id"] = selected_flat_id
flat = flat_map[selected_flat_id]

# --- Month/Year ---
col1, col2 = st.columns(2)
# Use session_state if available
month_index = datetime.now().month - 1
if "billing_month" in st.session_state:
    month_index = st.session_state["billing_month"] - 1
month = col1.selectbox("Month", list(range(1, 13)), index=month_index)

year_value = datetime.now().year
if "billing_year" in st.session_state:
    year_value = st.session_state["billing_year"]
year = col2.number_input("Year", value=year_value, step=1)

# Check if bill already exists
bill = monthly_bills_col.find_one({
    "flat_id": selected_flat_id,
    "month": int(month),
    "year": int(year)
})

# -------------------------------------------------------------------
#   AUTO-FILL previous readings from last month's CURRENT readings
# -------------------------------------------------------------------
prev_month, prev_year = get_prev_month_year(month, year)

previous_bill = monthly_bills_col.find_one({
    "flat_id": selected_flat_id,
    "month": prev_month,
    "year": prev_year
})

auto_prev_cold = float(previous_bill.get("cold_curr", 0)) if previous_bill else 0.0
auto_prev_hot = float(previous_bill.get("hot_curr", 0)) if previous_bill else 0.0

# If bill exists, DO NOT override existing values
if bill:
    default_prev_cold = float(bill.get("cold_prev", 0))
    default_prev_hot = float(bill.get("hot_prev", 0))
else:
    default_prev_cold = auto_prev_cold
    default_prev_hot = auto_prev_hot

# -------------------------------------------------------------------
# Inputs
# -------------------------------------------------------------------
prev_cold = st.number_input("Cold previous", value=default_prev_cold)
curr_cold = st.number_input("Cold current",
                            value=float(bill.get("cold_curr", 0)) if bill else 0.0)

prev_hot = st.number_input("Hot previous", value=default_prev_hot)
curr_hot = st.number_input("Hot current",
                           value=float(bill.get("hot_curr", 0)) if bill else 0.0)

rate = st.number_input(
    "Water rate",
    value=float(bill.get("water_rate", flat.get("water_rate_per_liter") or 0))
    if bill else (flat.get("water_rate_per_liter") or 0.0)
)

water_units, water_charge = calc_water_charge(prev_cold, curr_cold, prev_hot, curr_hot, rate)
st.write(f"Water units: {water_units} — Charge: ₹{water_charge:.2f}")

rent = st.number_input(
    "Rent",
    value=float(bill.get("rent", flat.get("base_rent", 0))) if bill else float(flat.get("base_rent", 0))
)
electricity = st.number_input("Electricity", value=float(bill.get("electricity", 0)) if bill else 0.0)

# --- Miscellaneous (single total misc field) ---
misc = st.number_input("Miscellaneous (maintenance/parking/etc.)", value=float(bill.get("misc", 0)) if bill else 0.0)

# -------------------------------------------------------------------
# Previous carry-forward (unchanged logic)
# -------------------------------------------------------------------
pm, py = get_prev_month_year(month, year)
prev_bill = monthly_bills_col.find_one({"flat_id": selected_flat_id, "month": pm, "year": py})
prev_carry = float(prev_bill.get("carry_forward", 0)) if prev_bill else 0.0
st.write(f"Previous carry: ₹{prev_carry:.2f}")

subtotal = calc_total_payable(rent, water_charge, electricity, misc)
total = subtotal + prev_carry
st.write(f"Subtotal: ₹{subtotal:.2f}")
st.write(f"Total due: ₹{total:.2f}")

amount_paid = st.number_input("Amount paid",
                              value=float(bill.get("amount_paid", 0)) if bill else 0.0)

pending = max(total - amount_paid, 0)
carry = max(amount_paid - total, pending)

st.write(f"Pending: ₹{pending:.2f}")
st.write(f"Carry forward: ₹{carry:.2f}")

# -------------------------------------------------------------------
# Save
# -------------------------------------------------------------------
if st.button("Save bill"):
    doc = {
        "flat_id": selected_flat_id,
        "building_id": building_id,
        "month": int(month),
        "year": int(year),

        "cold_prev": prev_cold,
        "cold_curr": curr_cold,
        "hot_prev": prev_hot,
        "hot_curr": curr_hot,

        "water_rate": rate,
        "water_units": water_units,
        "water_charge": water_charge,

        "rent": rent,
        "electricity": electricity,

        # NEW: misc (single field)
        "misc": float(misc),

        "subtotal": subtotal,
        "prev_carry": prev_carry,
        "total_due": total,

        "amount_paid": amount_paid,
        "pending": pending,
        "carry_forward": carry,

        "updated_at": datetime.utcnow().isoformat(),
    }
    # Save to billing collection
    monthly_bills_col.update_one(
        {"flat_id": selected_flat_id, "month": int(month), "year": int(year)},
        {"$set": doc},
        upsert=True
    )

    # 🔥 Sync monthly summary (recalculate derived fields)
    from utils.db import update_flat_monthly_summary
    update_flat_monthly_summary(selected_flat_id, building_id, int(month), int(year))

    st.success("Saved and summary updated!")
    st.rerun()


# Back
if st.button("⬅ Back to Flats"):
    st.switch_page("pages/2_Flats.py")
