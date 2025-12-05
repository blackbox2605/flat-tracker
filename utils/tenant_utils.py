# tenant_utils.py
from utils.db import tenants_col
from datetime import datetime

def add_new_tenant(flat_id, tenant_name):
    tenant = {
        "flat_id": flat_id,
        "name": tenant_name,
        "start_date": datetime.now(),
        "end_date": None,
        "active": True
    }
    tenants_col.insert_one(tenant)
    return tenant


def mark_tenant_vacated(flat_id):
    tenants_col.update_many(
        {"flat_id": flat_id, "active": True},
        {"$set": {"active": False, "end_date": datetime.now()}}
    )


def get_current_tenant(flat_id):
    return tenants_col.find_one({"flat_id": flat_id, "active": True})


def get_tenant_history(flat_id):
    return list(tenants_col.find({"flat_id": flat_id}))
