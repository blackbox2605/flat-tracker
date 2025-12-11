# #3_Billing.py
# import streamlit as st
# from bson import ObjectId
# from datetime import datetime
# from utils.db import flats_col, monthly_bills_col
# from utils.billing_utils import calc_water_charge, calc_total_payable

# st.set_page_config(page_title="Billing - Flat Tracker")

# # -------------------------------------------------------------------
# # Helper: Get previous month + year
# # -------------------------------------------------------------------
# def get_prev_month_year(month: int, year: int):
#     if month == 1:
#         return 12, year - 1
#     return month - 1, year

# # --- Ensure building is selected ---
# building_id = st.session_state.get("building_id")
# if not building_id:
#     st.error("Select a building on Home first.")
#     st.stop()

# st.title("📄 Billing")

# # --- Flat selection ---

# # flats = list(flats_col.find({"building_id": building_id}).sort("flat_no", 1))
# # if not flats:
# #     st.info("No flats found.")
# #     st.stop()

# # flat_map = {str(f["_id"]): f for f in flats}
# # options = {f"{f['flat_no']} ({f['bhk']}BHK)": str(f["_id"]) for f in flats}

# # selected_label = st.selectbox("Select flat", list(options.keys()))
# # selected_flat_id = options[selected_label]
# # st.session_state["selected_flat_id"] = selected_flat_id
# # flat = flat_map[selected_flat_id]

# # st.header(f"Flat {flat['flat_no']} — Billing")

# # # --- Month/Year ---
# # col1, col2 = st.columns(2)
# # month = col1.selectbox("Month", list(range(1, 13)), index=datetime.now().month - 1)
# # year = col2.number_input("Year", value=datetime.now().year, step=1)


# # --- Flat selection ---
# flats = list(flats_col.find({"building_id": building_id}).sort("flat_no", 1))
# if not flats:
#     st.info("No flats found.")
#     st.stop()

# flat_map = {str(f["_id"]): f for f in flats}
# options = {f"{f['flat_no']} ({f['bhk']}BHK)": str(f["_id"]) for f in flats}

# # Pre-select flat from session_state if available
# if "selected_flat_id" in st.session_state:
#     selected_flat_id = st.session_state["selected_flat_id"]
#     # Get label from flat_map
#     selected_label = next((lbl for lbl, fid in options.items() if fid == selected_flat_id), list(options.keys())[0])
# else:
#     selected_label = list(options.keys())[0]
#     selected_flat_id = options[selected_label]

# selected_label = st.selectbox("Select flat", list(options.keys()), index=list(options.keys()).index(selected_label))
# selected_flat_id = options[selected_label]
# st.session_state["selected_flat_id"] = selected_flat_id
# flat = flat_map[selected_flat_id]

# # --- Month/Year ---
# col1, col2 = st.columns(2)
# # Use session_state if available
# month_index = datetime.now().month - 1
# if "billing_month" in st.session_state:
#     month_index = st.session_state["billing_month"] - 1
# month = col1.selectbox("Month", list(range(1, 13)), index=month_index)

# year_value = datetime.now().year
# if "billing_year" in st.session_state:
#     year_value = st.session_state["billing_year"]
# year = col2.number_input("Year", value=year_value, step=1)

# # Check if bill already exists
# bill = monthly_bills_col.find_one({
#     "flat_id": selected_flat_id,
#     "month": int(month),
#     "year": int(year)
# })

# # -------------------------------------------------------------------
# #   AUTO-FILL previous readings from last month's CURRENT readings
# # -------------------------------------------------------------------
# prev_month, prev_year = get_prev_month_year(month, year)

# previous_bill = monthly_bills_col.find_one({
#     "flat_id": selected_flat_id,
#     "month": prev_month,
#     "year": prev_year
# })

# auto_prev_cold = float(previous_bill.get("cold_curr", 0)) if previous_bill else 0.0
# auto_prev_hot = float(previous_bill.get("hot_curr", 0)) if previous_bill else 0.0

# # If bill exists, DO NOT override existing values
# if bill:
#     default_prev_cold = float(bill.get("cold_prev", 0))
#     default_prev_hot = float(bill.get("hot_prev", 0))
# else:
#     default_prev_cold = auto_prev_cold
#     default_prev_hot = auto_prev_hot

# # -------------------------------------------------------------------
# # Inputs
# # -------------------------------------------------------------------
# prev_cold = st.number_input("Cold previous", value=default_prev_cold)
# curr_cold = st.number_input("Cold current",
#                             value=float(bill.get("cold_curr", 0)) if bill else 0.0)

# prev_hot = st.number_input("Hot previous", value=default_prev_hot)
# curr_hot = st.number_input("Hot current",
#                            value=float(bill.get("hot_curr", 0)) if bill else 0.0)

# rate = st.number_input(
#     "Water rate",
#     value=float(bill.get("water_rate", flat.get("water_rate_per_liter") or 0))
#     if bill else (flat.get("water_rate_per_liter") or 0.0)
# )

# water_units, water_charge = calc_water_charge(prev_cold, curr_cold, prev_hot, curr_hot, rate)
# st.write(f"Water units: {water_units} — Charge: ₹{water_charge:.2f}")

# rent = st.number_input(
#     "Rent",
#     value=float(bill.get("rent", flat.get("base_rent", 0))) if bill else float(flat.get("base_rent", 0))
# )
# electricity = st.number_input("Electricity", value=float(bill.get("electricity", 0)) if bill else 0.0)

# # --- Miscellaneous (single total misc field) ---
# misc = st.number_input("Miscellaneous (maintenance/parking/etc.)", value=float(bill.get("misc", 0)) if bill else 0.0)

# # -------------------------------------------------------------------
# # Previous carry-forward (unchanged logic)
# # -------------------------------------------------------------------
# pm, py = get_prev_month_year(month, year)
# prev_bill = monthly_bills_col.find_one({"flat_id": selected_flat_id, "month": pm, "year": py})
# prev_carry = float(prev_bill.get("carry_forward", 0)) if prev_bill else 0.0
# st.write(f"Previous carry: ₹{prev_carry:.2f}")

# subtotal = calc_total_payable(rent, water_charge, electricity, misc)
# total = subtotal + prev_carry
# st.write(f"Subtotal: ₹{subtotal:.2f}")
# st.write(f"Total due: ₹{total:.2f}")

# amount_paid = st.number_input("Amount paid",
#                               value=float(bill.get("amount_paid", 0)) if bill else 0.0)

# pending = max(total - amount_paid, 0)
# carry = max(amount_paid - total, pending)

# st.write(f"Pending: ₹{pending:.2f}")
# st.write(f"Carry forward: ₹{carry:.2f}")

# # -------------------------------------------------------------------
# # Save
# # -------------------------------------------------------------------
# if st.button("Save bill"):
#     doc = {
#         "flat_id": selected_flat_id,
#         "building_id": building_id,
#         "month": int(month),
#         "year": int(year),

#         "cold_prev": prev_cold,
#         "cold_curr": curr_cold,
#         "hot_prev": prev_hot,
#         "hot_curr": curr_hot,

#         "water_rate": rate,
#         "water_units": water_units,
#         "water_charge": water_charge,

#         "rent": rent,
#         "electricity": electricity,

#         # NEW: misc (single field)
#         "misc": float(misc),

#         "subtotal": subtotal,
#         "prev_carry": prev_carry,
#         "total_due": total,

#         "amount_paid": amount_paid,
#         "pending": pending,
#         "carry_forward": carry,

#         "updated_at": datetime.utcnow().isoformat(),
#     }
#     # Save to billing collection
#     monthly_bills_col.update_one(
#         {"flat_id": selected_flat_id, "month": int(month), "year": int(year)},
#         {"$set": doc},
#         upsert=True
#     )

#     # 🔥 Sync monthly summary (recalculate derived fields)
#     from utils.db import update_flat_monthly_summary
#     update_flat_monthly_summary(selected_flat_id, building_id, int(month), int(year))

#     st.success("Saved and summary updated!")
#     st.rerun()


# # Back
# if st.button("⬅ Back to Flats"):
#     st.switch_page("pages/2_Flats.py")


# pages/3_Billing.py
import streamlit as st
from datetime import datetime
from io import BytesIO
from utils.db import (
    get_buildings,
    get_flats_by_building,
    update_flat_monthly_summary,
)
from utils.db import monthly_bills_col  # direct collection for queries
from utils.billing_utils import calc_water_charge, calc_total_payable

st.set_page_config(page_title="Billing - Flat Tracker")

# -------------------------------------------------------------------
# Helper: Get previous month + year
# -------------------------------------------------------------------
def get_prev_month_year(month: int, year: int):
    if month == 1:
        return 12, year - 1
    return month - 1, year

# -------------------------------------------------------------------
# Page header and building selection
# -------------------------------------------------------------------
st.title("📄 Billing")

# Load buildings
buildings = get_buildings()
if not buildings:
    st.info("No buildings found. Create a building first.")
    st.stop()

# Build mapping name -> id (string)
building_map = {b.get("name", f"Building {i}"): str(b.get("_id")) for i, b in enumerate(buildings, 1)}
# Determine default selection (session_state > first in list)
default_building_id = st.session_state.get("building_id") or list(building_map.values())[0]
# figure default index
building_labels = list(building_map.keys())
default_label = next((lbl for lbl, bid in building_map.items() if bid == default_building_id), building_labels[0])
selected_building_label = st.selectbox("Select building", building_labels, index=building_labels.index(default_label))
selected_building_id = building_map[selected_building_label]

# persist building selection to session_state (so other pages can use it)
st.session_state["building_id"] = selected_building_id

# -------------------------------------------------------------------
# Flats dropdown (filtered by selected building)
# -------------------------------------------------------------------
flats = get_flats_by_building(selected_building_id)
if not flats:
    st.info("No flats found for this building.")
    st.stop()

flat_map = {f"{f.get('flat_no','?')} ({f.get('bhk','?')}BHK)": str(f.get("_id")) for f in flats}
flat_labels = list(flat_map.keys())

# default flat selection logic:
if "selected_flat_id" in st.session_state and st.session_state["selected_flat_id"] in flat_map.values():
    # find the label for the stored selected_flat_id
    default_label = next((lbl for lbl, fid in flat_map.items() if fid == st.session_state["selected_flat_id"]), flat_labels[0])
else:
    # if session stored flat not present in this building (or not set), pick first
    default_label = flat_labels[0]
    st.session_state["selected_flat_id"] = flat_map[default_label]

selected_flat_label = st.selectbox("Select flat", flat_labels, index=flat_labels.index(default_label))
selected_flat_id = flat_map[selected_flat_label]
st.session_state["selected_flat_id"] = selected_flat_id

# Show header for selected flat
# fetch flat doc (we have flats list)
flat_doc = next((f for f in flats if str(f.get("_id")) == selected_flat_id), None)
if not flat_doc:
    st.error("Selected flat not found (unexpected).")
    st.stop()

st.header(f"Flat {flat_doc.get('flat_no')} — Billing")

# -------------------------------------------------------------------
# Month/Year selection (respect session state if provided)
# -------------------------------------------------------------------
col1, col2 = st.columns(2)

# month default index
if "billing_month" in st.session_state:
    month_index = max(0, st.session_state["billing_month"] - 1)
else:
    month_index = datetime.now().month - 1

month = col1.selectbox("Month", list(range(1, 13)), index=month_index)
# year default
if "billing_year" in st.session_state:
    year_default = st.session_state["billing_year"]
else:
    year_default = datetime.now().year
year = col2.number_input("Year", value=year_default, step=1, format="%d")

# persist month/year
st.session_state["billing_month"] = int(month)
st.session_state["billing_year"] = int(year)

# -------------------------------------------------------------------
# Load existing bill (if any)
# -------------------------------------------------------------------
bill = monthly_bills_col.find_one({
    "flat_id": selected_flat_id,
    "month": int(month),
    "year": int(year)
})

# -------------------------------------------------------------------
# Auto-fill previous readings from last month's 'curr' if present
# -------------------------------------------------------------------
prev_month, prev_year = get_prev_month_year(month, year)
previous_bill = monthly_bills_col.find_one({
    "flat_id": selected_flat_id,
    "month": prev_month,
    "year": prev_year
})

auto_prev_cold = float(previous_bill.get("cold_curr", 0)) if previous_bill else 0.0
auto_prev_hot = float(previous_bill.get("hot_curr", 0)) if previous_bill else 0.0

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
curr_cold = st.number_input("Cold current", value=float(bill.get("cold_curr", 0)) if bill else 0.0)

prev_hot = st.number_input("Hot previous", value=default_prev_hot)
curr_hot = st.number_input("Hot current", value=float(bill.get("hot_curr", 0)) if bill else 0.0)

rate = st.number_input(
    "Water rate",
    value=float(bill.get("water_rate", flat_doc.get("water_rate_per_liter") or 0)) if bill else (flat_doc.get("water_rate_per_liter") or 0.0)
)

water_units, water_charge = calc_water_charge(prev_cold, curr_cold, prev_hot, curr_hot, rate)
st.write(f"Water units: {water_units} — Charge: ₹{water_charge:.2f}")

rent = st.number_input(
    "Rent",
    value=float(bill.get("rent", flat_doc.get("base_rent", 0))) if bill else float(flat_doc.get("base_rent", 0))
)
electricity = st.number_input("Electricity", value=float(bill.get("electricity", 0)) if bill else 0.0)
misc = st.number_input("Miscellaneous (maintenance/parking/etc.)", value=float(bill.get("misc", 0)) if bill else 0.0)

# -------------------------------------------------------------------
# Previous carry-forward
# -------------------------------------------------------------------
pm, py = get_prev_month_year(month, year)
prev_bill = monthly_bills_col.find_one({"flat_id": selected_flat_id, "month": pm, "year": py})
prev_carry = float(prev_bill.get("carry_forward", 0)) if prev_bill else 0.0
st.write(f"Previous carry: ₹{prev_carry:.2f}")

subtotal = calc_total_payable(rent, water_charge, electricity, misc)
total = subtotal + prev_carry
st.write(f"Subtotal: ₹{subtotal:.2f}")
st.write(f"Total due: ₹{total:.2f}")

amount_paid = st.number_input("Amount paid", value=float(bill.get("amount_paid", 0)) if bill else 0.0)

pending = max(total - amount_paid, 0)
carry = max(amount_paid - total, pending)

st.write(f"Pending: ₹{pending:.2f}")
st.write(f"Carry forward: ₹{carry:.2f}")

# -------------------------------------------------------------------
# Save bill
# -------------------------------------------------------------------
if st.button("Save bill"):
    doc = {
        "flat_id": selected_flat_id,
        "building_id": selected_building_id,
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
        "misc": float(misc),
        "subtotal": subtotal,
        "prev_carry": prev_carry,
        "total_due": total,
        "amount_paid": amount_paid,
        "pending": pending,
        "carry_forward": carry,
        "updated_at": datetime.utcnow().isoformat(),
    }

    monthly_bills_col.update_one(
        {"flat_id": selected_flat_id, "month": int(month), "year": int(year)},
        {"$set": doc},
        upsert=True
    )

    # Update monthly summary for the flat
    update_flat_monthly_summary(selected_flat_id, selected_building_id, int(month), int(year))

    st.success("Saved and summary updated!")
    st.rerun()

# -------------------------------------------------------------------
# PDF Export (uses reportlab if available)
# -------------------------------------------------------------------
def make_pdf_bytes(bill_doc, flat, building_name, month, year):
    """
    Returns bytes of a small one-page PDF summarizing the bill.
    Falls back to a simple text if reportlab is not available.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, f"Billing — {building_name} — Flat {flat.get('flat_no')}")
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Month/Year: {month}/{year}")
    y -= 20

    # Draw fields
    lines = [
        f"Tenant (current): { (next((t['tenant_name'] for t in reversed(flat.get('tenant_history', [])) if not t.get('move_out')), '-')) }",
        f"Cold previous: {bill_doc.get('cold_prev', 0)}",
        f"Cold current:  {bill_doc.get('cold_curr', 0)}",
        f"Hot previous:  {bill_doc.get('hot_prev', 0)}",
        f"Hot current:   {bill_doc.get('hot_curr', 0)}",
        f"Water units:   {bill_doc.get('water_units', 0)}",
        f"Water charge:  ₹{bill_doc.get('water_charge', 0):.2f}",
        f"Water rate:    {bill_doc.get('water_rate', 0)}",
        f"Rent:          ₹{bill_doc.get('rent', 0):.2f}",
        f"Electricity:   ₹{bill_doc.get('electricity', 0):.2f}",
        f"Misc:          ₹{bill_doc.get('misc', 0):.2f}",
        f"Prev carry:    ₹{bill_doc.get('prev_carry', 0):.2f}",
        f"Subtotal:      ₹{bill_doc.get('subtotal', 0):.2f}",
        f"Total due:     ₹{bill_doc.get('total_due', 0):.2f}",
        f"Amount paid:   ₹{bill_doc.get('amount_paid', 0):.2f}",
        f"Pending:       ₹{bill_doc.get('pending', 0):.2f}",
        f"Carry forward: ₹{bill_doc.get('carry_forward', 0):.2f}",
    ]

    for line in lines:
        if y < margin + 40:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 11)
        c.drawString(margin, y, line)
        y -= 16

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

def make_text_bytes(bill_doc, flat, building_name, month, year):
    # fallback plain text
    lines = [
        f"Building: {building_name}",
        f"Flat: {flat.get('flat_no')}",
        f"Month/Year: {month}/{year}",
        "-"*40
    ]
    keys = [
        ("cold_prev", "Cold prev"),
        ("cold_curr", "Cold curr"),
        ("hot_prev", "Hot prev"),
        ("hot_curr", "Hot curr"),
        ("water_units", "Water units"),
        ("water_charge", "Water charge"),
        ("water_rate", "Water rate"),
        ("rent", "Rent"),
        ("electricity", "Electricity"),
        ("misc", "Misc"),
        ("prev_carry", "Prev carry"),
        ("subtotal", "Subtotal"),
        ("total_due", "Total due"),
        ("amount_paid", "Amount paid"),
        ("pending", "Pending"),
        ("carry_forward", "Carry forward"),
    ]
    for k, label in keys:
        lines.append(f"{label}: {bill_doc.get(k, 0)}")
    content = "\n".join(lines)
    return content.encode("utf-8")

# Build a doc to export (prefer existing bill values, otherwise values from form)
export_doc = {
    "cold_prev": prev_cold,
    "cold_curr": curr_cold,
    "hot_prev": prev_hot,
    "hot_curr": curr_hot,
    "water_units": water_units,
    "water_charge": water_charge,
    "water_rate": rate,
    "rent": rent,
    "electricity": electricity,
    "misc": misc,
    "prev_carry": prev_carry,
    "subtotal": subtotal,
    "total_due": total,
    "amount_paid": amount_paid,
    "pending": pending,
    "carry_forward": carry,
}

# Try PDF bytes
pdf_bytes = make_pdf_bytes(export_doc, flat_doc, selected_building_label, month, year)
if pdf_bytes:
    st.download_button(
        label="⬇️ Export bill as PDF",
        data=pdf_bytes,
        file_name=f"bill_flat_{flat_doc.get('flat_no')}_{month}_{year}.pdf",
        mime="application/pdf",
    )
else:
    # fallback: plain text download
    text_bytes = make_text_bytes(export_doc, flat_doc, selected_building_label, month, year)
    st.download_button(
        label="⬇️ Export bill (text fallback)",
        data=text_bytes,
        file_name=f"bill_flat_{flat_doc.get('flat_no')}_{month}_{year}.txt",
        mime="text/plain",
    )

# -------------------------------------------------------------------
# Back
# -------------------------------------------------------------------
if st.button("⬅ Back to Flats"):
    # keep building_id in session so flats page displays that building
    st.session_state["building_id"] = selected_building_id
    st.experimental_set_query_params()  # ensure navigation clean
    st.experimental_rerun()
    # st.switch_page("pages/2_Flats.py")  # old approach — rerun ensures state kept
