# utils/billing_utils.py
def calc_water_charge(prev_cold, curr_cold, prev_hot, curr_hot, rate_per_liter):
    cold_used = max(0.0, float(curr_cold) - float(prev_cold))
    hot_used = max(0.0, float(curr_hot) - float(prev_hot))
    total_used = cold_used + hot_used
    return total_used, total_used * float(rate_per_liter)

def calc_total_payable(rent, water_charge, electricity, misc=0.0):
    """
    Returns subtotal (rent + water_charge + electricity + misc).
    `misc` is optional and defaults to 0.
    """
    return float(rent) + float(water_charge) + float(electricity) + float(misc)
