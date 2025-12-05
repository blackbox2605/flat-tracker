# pages/2_Flats.py
import streamlit as st
from datetime import datetime
from utils.db import (
    get_building,
    get_flats_by_building,
    add_flat,
    update_flat,
    delete_flat,
    add_tenant_entry,
    vacate_current_tenant,
    move_flat_to_history,
    add_advance_payment,
    get_advance_summary,
)

st.set_page_config(page_title="Flats - Flat Tracker")
st.title("🏢 Flats — Manage Building")

if "building_id" not in st.session_state:
    st.error("No building selected. Go back to Buildings.")
    st.stop()

building_id = st.session_state["building_id"]
building = get_building(building_id)

if not building:
    st.error("Building not found.")
    st.stop()

st.header(f"{building.get('name')}")
colA, colB = st.columns(2)
if colA.button("⬅ Back to Buildings"):
    st.switch_page("pages/1_Buildings.py")
if colB.button("Tenant History"):
    st.switch_page("pages/4_Tenant_History.py")

st.write("---")

# Add flat
with st.expander("➕ Add new flat"):
    with st.form("add_flat"):
        flat_no = st.text_input("Flat No")
        floor = st.number_input("Floor", value=0)
        bhk = st.selectbox("BHK", ["1", "2", "3"])
        base_rent = st.number_input("Base Rent", value=0.0)
        water_rate = st.number_input("Water Rate (optional)", value=0.0)
        tenant_name = st.text_input("Initial Tenant Name")
        move_in = st.date_input("Move-in Date", value=datetime.today())

        # New advance fields
        total_advance = st.number_input("Total Advance", value=0.0)
        initial_paid = st.number_input("Advance Paid Now", value=0.0)

        submit = st.form_submit_button("Create")

        if submit:
            fid = add_flat(
                building_id,
                flat_no,
                floor,
                bhk,
                base_rent,
                water_rate if water_rate > 0 else None,
                tenant_name if tenant_name else None,
                move_in.isoformat() if tenant_name else None,
                total_advance=total_advance,  # <-- ADDED
            )

            if total_advance > 0 and initial_paid > 0:
                add_advance_payment(fid, initial_paid)

            st.success("Flat created.")
            st.rerun()

st.write("---")

# List flats
flats = get_flats_by_building(building_id)

if not flats:
    st.info("No flats found.")
else:
    for f in flats:
        fid = str(f["_id"])

        th = f.get("tenant_history", [])
        curr = next((x for x in reversed(th) if not x.get("move_out")), None)

        header = f"Flat {f['flat_no']} — {f['bhk']}BHK"
        if curr:
            header += f" — Tenant: {curr['tenant_name']}"

        with st.expander(header):

            # Advance summary
            total_adv, paid_adv, remaining_adv = get_advance_summary(fid)
            st.markdown(
                f"**Advance:** Total: ₹{total_adv:.2f} | Paid: ₹{paid_adv:.2f} | Remaining: ₹{remaining_adv:.2f}"
            )

            # Add new payment
            with st.form(f"adv_{fid}"):
                new_payment = st.number_input("Add Advance Payment", min_value=0.0, value=0.0)
                ok = st.form_submit_button("Add Payment")
                if ok and new_payment > 0:
                    add_advance_payment(fid, new_payment)
                    st.success("Payment added.")
                    st.rerun()

            # Edit section
            with st.form(f"edit_{fid}"):
                new_rent = st.number_input("Base Rent", value=f.get("base_rent", 0.0))
                new_rate = st.number_input("Water Rate", value=f.get("water_rate_per_liter") or 0.0)

                assign_name = st.text_input("New Tenant Name")
                assign_phone = st.text_input("Tenant Phone")
                assign_movein = st.date_input("Tenant Move-in Date", value=datetime.today())

                vac_chk = st.checkbox("Vacate current tenant")

                submitted = st.form_submit_button("Save")

                if submitted:
                    update_flat(fid, base_rent=new_rent, water_rate_per_liter=new_rate)

                    from utils.db import update_flat_monthly_summary
                    curr_month, curr_year = datetime.now().month, datetime.now().year
                    update_flat_monthly_summary(fid, building_id, curr_month, curr_year)

                    if vac_chk:
                        vacate_current_tenant(fid, assign_movein.isoformat())

                    if assign_name:
                        add_tenant_entry(
                            fid,
                            assign_name,
                            assign_movein.isoformat(),
                            assign_phone,
                        )

                    st.success("Updated.")
                    st.rerun()

            col1, col2, col3 = st.columns(3)

            if col1.button("Open Billing", key=f"bl_{fid}"):
                st.session_state["selected_flat_id"] = fid
                st.switch_page("pages/3_Billing.py")

            if col2.button("Tenant History", key=f"th_{fid}"):
                st.session_state["selected_flat_id"] = fid
                st.switch_page("pages/4_Tenant_History.py")

            if col3.button("Vacate", key=f"vac_{fid}"):
                move_flat_to_history(fid)
                st.success("Tenant moved to history.")
                st.rerun()
