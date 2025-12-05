# # utils/db.py
# from pymongo import MongoClient
# from bson import ObjectId
# import streamlit as st
# from datetime import datetime

# # -----------------------------
# # DB Initialization
# # -----------------------------
# def init_db():
#     uri = st.secrets.get("mongodb_uri")
#     if not uri:
#         st.error("MongoDB URI not found in .streamlit/secrets.toml")
#         st.stop()
#     client = MongoClient(uri)
#     return client["flat_tracker"]

# # Initialize DB once
# if "db" not in st.session_state:
#     st.session_state["db"] = init_db()

# db = st.session_state["db"]

# def get_db():
#     """Streamlit Cloud expects this function."""
#     return db

# # Collections
# buildings_col = db.buildings
# flats_col = db.flats
# monthly_bills_col = db.monthly_bills


# # -----------------------------
# # Building helpers
# # -----------------------------
# def get_buildings():
#     return list(buildings_col.find().sort("name", 1))

# def add_building(name, address=""):
#     doc = {"name": name, "address": address, "created_at": datetime.utcnow().isoformat()}
#     res = buildings_col.insert_one(doc)
#     return str(res.inserted_id)

# def get_building(building_id):
#     try:
#         return buildings_col.find_one({"_id": ObjectId(building_id)})
#     except:
#         return None


# # -----------------------------
# # Flats helpers
# # -----------------------------
# def get_flats_by_building(building_id):
#     return list(flats_col.find({"building_id": str(building_id)}).sort("flat_no", 1))

# def add_flat(building_id, flat_no, floor=None, bhk=None, base_rent=0.0, water_rate=None, tenant_name=None, move_in=None, phone=""):
#     flat_doc = {
#         "building_id": str(building_id),
#         "flat_no": str(flat_no),
#         "floor": int(floor) if floor not in (None, "", False) else None,
#         "bhk": int(bhk) if bhk not in (None, "", False) else None,
#         "base_rent": float(base_rent) if base_rent not in (None, "") else 0.0,
#         "water_rate_per_liter": float(water_rate) if water_rate not in (None, "") else None,
#         "tenant_history": [],
#         "created_at": datetime.utcnow().isoformat(),
#     }
#     res = flats_col.insert_one(flat_doc)
#     fid = str(res.inserted_id)

#     if tenant_name and move_in:
#         entry = {
#             "tenant_name": tenant_name,
#             "phone": phone or "",
#             "move_in": move_in,
#             "move_out": None,
#             "recorded_at": datetime.utcnow().isoformat()
#         }
#         flats_col.update_one({"_id": ObjectId(fid)}, {"$push": {"tenant_history": entry}})
#     return fid


# def update_flat(flat_id, **kwargs):
#     update_doc = {}

#     if "floor" in kwargs and kwargs["floor"] not in (None, ""):
#         update_doc["floor"] = int(kwargs["floor"])
#     if "bhk" in kwargs and kwargs["bhk"] not in (None, ""):
#         update_doc["bhk"] = int(kwargs["bhk"])
#     if "base_rent" in kwargs and kwargs["base_rent"] not in (None, ""):
#         update_doc["base_rent"] = float(kwargs["base_rent"])
#     if "water_rate_per_liter" in kwargs:
#         wr = kwargs["water_rate_per_liter"]
#         update_doc["water_rate_per_liter"] = float(wr) if wr not in (None, "") else None

#     if update_doc:
#         flats_col.update_one({"_id": ObjectId(flat_id)}, {"$set": update_doc})

#     # Auto sync to monthly summary
#     from datetime import datetime
#     curr_month, curr_year = datetime.now().month, datetime.now().year
#     building_id = kwargs.get("building_id") or flats_col.find_one({"_id": ObjectId(flat_id)})["building_id"]
#     update_flat_monthly_summary(flat_id, building_id, curr_month, curr_year)


# def delete_flat(flat_id):
#     flats_col.delete_one({"_id": ObjectId(flat_id)})
#     monthly_bills_col.delete_many({"flat_id": str(flat_id)})


# # -----------------------------
# # Tenant history
# # -----------------------------
# def add_tenant_entry(flat_id, tenant_name, move_in, phone=""):
#     entry = {
#         "tenant_name": tenant_name,
#         "phone": phone or "",
#         "move_in": move_in,
#         "move_out": None,
#         "recorded_at": datetime.utcnow().isoformat()
#     }
#     flats_col.update_one({"_id": ObjectId(flat_id)}, {"$push": {"tenant_history": entry}})


# def vacate_current_tenant(flat_id, move_out_date=None):
#     flat = flats_col.find_one({"_id": ObjectId(flat_id)})
#     if not flat:
#         return

#     hist = flat.get("tenant_history", []) or []

#     for i in range(len(hist) - 1, -1, -1):
#         if not hist[i].get("move_out"):
#             hist[i]["move_out"] = move_out_date or datetime.utcnow().isoformat()
#             break

#     flats_col.update_one({"_id": ObjectId(flat_id)}, {"$set": {"tenant_history": hist}})


# def move_flat_to_history(flat_id):
#     vacate_current_tenant(flat_id)
#     flats_col.delete_one({"_id": ObjectId(flat_id)})
#     monthly_bills_col.delete_many({"flat_id": str(flat_id)})


# # -----------------------------
# # Billing helpers
# # -----------------------------
# def get_bill(flat_id, month, year):
#     return monthly_bills_col.find_one({
#         "flat_id": str(flat_id),
#         "month": int(month),
#         "year": int(year)
#     })


# def save_bill(flat_id, building_id, month, year, bill_doc):
#     monthly_bills_col.update_one(
#         {"flat_id": str(flat_id), "month": int(month), "year": int(year)},
#         {"$set": bill_doc},
#         upsert=True
#     )


# # -----------------------------
# # Monthly summary updater
# # -----------------------------
# def update_flat_monthly_summary(flat_id, building_id, month, year):
#     from utils.billing_utils import calc_water_charge, calc_total_payable

#     bill = get_bill(flat_id, month, year)
#     if not bill:
#         return

#     flat = flats_col.find_one({"_id": ObjectId(flat_id)})
#     if not flat:
#         return

#     water_units, water_charge = calc_water_charge(
#         bill.get("cold_prev", 0),
#         bill.get("cold_curr", 0),
#         bill.get("hot_prev", 0),
#         bill.get("hot_curr", 0),
#         flat.get("water_rate_per_liter", 0)
#     )

#     subtotal = calc_total_payable(
#         bill.get("rent", flat.get("base_rent", 0)),
#         water_charge,
#         bill.get("electricity", 0)
#     )

#     total_due = subtotal + bill.get("prev_carry", 0)

#     monthly_bills_col.update_one(
#         {"flat_id": str(flat_id), "month": int(month), "year": int(year)},
#         {"$set": {
#             "water_units": water_units,
#             "water_charge": water_charge,
#             "subtotal": subtotal,
#             "total_due": total_due
#         }}
#     )


from pymongo import MongoClient
from bson import ObjectId
import streamlit as st
from datetime import datetime

# -----------------------------
# DB Initialization
# -----------------------------
def init_db():
    uri = st.secrets.get("mongodb_uri")
    if not uri:
        st.error("MongoDB URI not found in .streamlit/secrets.toml")
        st.stop()
    client = MongoClient(uri)
    return client["flat_tracker"]

# Initialize DB once
if "db" not in st.session_state:
    st.session_state["db"] = init_db()

db = st.session_state["db"]

def get_db():
    """Streamlit Cloud expects this function."""
    return db

# Collections
buildings_col = db.buildings
flats_col = db.flats
monthly_bills_col = db.monthly_bills


# -----------------------------
# Building helpers
# -----------------------------
def get_buildings():
    return list(buildings_col.find().sort("name", 1))

def add_building(name, address=""):
    doc = {"name": name, "address": address, "created_at": datetime.utcnow().isoformat()}
    res = buildings_col.insert_one(doc)
    return str(res.inserted_id)

def get_building(building_id):
    try:
        return buildings_col.find_one({"_id": ObjectId(building_id)})
    except:
        return None


# -----------------------------
# Flats helpers
# -----------------------------
def get_flats_by_building(building_id):
    return list(flats_col.find({"building_id": str(building_id)}).sort("flat_no", 1))

def add_flat(building_id, flat_no, floor=None, bhk=None, base_rent=0.0, water_rate=None, tenant_name=None, move_in=None, phone=""):
    flat_doc = {
        "building_id": str(building_id),
        "flat_no": str(flat_no),
        "floor": int(floor) if floor not in (None, "", False) else None,
        "bhk": int(bhk) if bhk not in (None, "", False) else None,
        "base_rent": float(base_rent) if base_rent not in (None, "") else 0.0,
        "water_rate_per_liter": float(water_rate) if water_rate not in (None, "") else None,
        "tenant_history": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    res = flats_col.insert_one(flat_doc)
    fid = str(res.inserted_id)

    if tenant_name and move_in:
        entry = {
            "tenant_name": tenant_name,
            "phone": phone or "",
            "move_in": move_in,
            "move_out": None,
            "recorded_at": datetime.utcnow().isoformat()
        }
        flats_col.update_one({"_id": ObjectId(fid)}, {"$push": {"tenant_history": entry}})
    return fid


def update_flat(flat_id, **kwargs):
    update_doc = {}

    if "floor" in kwargs and kwargs["floor"] not in (None, ""):
        update_doc["floor"] = int(kwargs["floor"])
    if "bhk" in kwargs and kwargs["bhk"] not in (None, ""):
        update_doc["bhk"] = int(kwargs["bhk"])
    if "base_rent" in kwargs and kwargs["base_rent"] not in (None, ""):
        update_doc["base_rent"] = float(kwargs["base_rent"])
    if "water_rate_per_liter" in kwargs:
        wr = kwargs["water_rate_per_liter"]
        update_doc["water_rate_per_liter"] = float(wr) if wr not in (None, "") else None

    if update_doc:
        flats_col.update_one({"_id": ObjectId(flat_id)}, {"$set": update_doc})

    # Auto sync to monthly summary
    from datetime import datetime
    curr_month, curr_year = datetime.now().month, datetime.now().year
    building_id = kwargs.get("building_id") or flats_col.find_one({"_id": ObjectId(flat_id)})["building_id"]
    update_flat_monthly_summary(flat_id, building_id, curr_month, curr_year)


def delete_flat(flat_id):
    flats_col.delete_one({"_id": ObjectId(flat_id)})
    monthly_bills_col.delete_many({"flat_id": str(flat_id)})


# -----------------------------
# Tenant history
# -----------------------------
def add_tenant_entry(flat_id, tenant_name, move_in, phone=""):
    entry = {
        "tenant_name": tenant_name,
        "phone": phone or "",
        "move_in": move_in,
        "move_out": None,
        "recorded_at": datetime.utcnow().isoformat()
    }
    flats_col.update_one({"_id": ObjectId(flat_id)}, {"$push": {"tenant_history": entry}})


def vacate_current_tenant(flat_id, move_out_date=None):
    flat = flats_col.find_one({"_id": ObjectId(flat_id)})
    if not flat:
        return

    hist = flat.get("tenant_history", []) or []

    for i in range(len(hist) - 1, -1, -1):
        if not hist[i].get("move_out"):
            hist[i]["move_out"] = move_out_date or datetime.utcnow().isoformat()
            break

    flats_col.update_one({"_id": ObjectId(flat_id)}, {"$set": {"tenant_history": hist}})


def move_flat_to_history(flat_id):
    vacate_current_tenant(flat_id)
    flats_col.delete_one({"_id": ObjectId(flat_id)})
    monthly_bills_col.delete_many({"flat_id": str(flat_id)})


# -----------------------------
# Billing helpers
# -----------------------------
def get_bill(flat_id, month, year):
    return monthly_bills_col.find_one({
        "flat_id": str(flat_id),
        "month": int(month),
        "year": int(year)
    })


def save_bill(flat_id, building_id, month, year, bill_doc):
    monthly_bills_col.update_one(
        {"flat_id": str(flat_id), "month": int(month), "year": int(year)},
        {"$set": bill_doc},
        upsert=True
    )


# -----------------------------
# Monthly summary updater
# -----------------------------
def update_flat_monthly_summary(flat_id, building_id, month, year):
    """
    Recalculate and update derived fields for a bill (water_units, water_charge, subtotal, total_due).
    This reads the saved monthly_bills_col document for the given flat/month/year and uses the
    flat's water_rate_per_liter if available for water charge calculation if bill doesn't contain explicit rate.
    """
    from utils.billing_utils import calc_water_charge, calc_total_payable

    bill = get_bill(flat_id, month, year)
    if not bill:
        return

    flat = flats_col.find_one({"_id": ObjectId(flat_id)})
    if not flat:
        return

    # Prefer water rate from bill if present, else use flat's stored water_rate_per_liter
    rate_to_use = bill.get("water_rate")
    if rate_to_use is None:
        rate_to_use = flat.get("water_rate_per_liter", 0)

    water_units, water_charge = calc_water_charge(
        bill.get("cold_prev", 0),
        bill.get("cold_curr", 0),
        bill.get("hot_prev", 0),
        bill.get("hot_curr", 0),
        rate_to_use
    )

    # include misc in subtotal if present
    misc_amount = float(bill.get("misc", 0) or 0)

    subtotal = calc_total_payable(
        bill.get("rent", flat.get("base_rent", 0)),
        water_charge,
        bill.get("electricity", 0),
        misc_amount
    )

    total_due = subtotal + float(bill.get("prev_carry", 0) or 0)

    monthly_bills_col.update_one(
        {"flat_id": str(flat_id), "month": int(month), "year": int(year)},
        {"$set": {
            "water_units": water_units,
            "water_charge": water_charge,
            "subtotal": subtotal,
            "total_due": total_due
        }}
    )
