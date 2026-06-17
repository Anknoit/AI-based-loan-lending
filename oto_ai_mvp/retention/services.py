import random

UPGRADE_BIKES = {
    'hero_splendor': 'honda_activa',
    'honda_activa': 'suzuki_access',
    'suzuki_access': 'bajaj_pulsar',
    'bajaj_pulsar': 're_meteor',
    're_meteor': 'ather_450x',
    'ola_s1x': 'ather_450x',
    'ather_450x': 'ather_450x',
    'tvs_ntorq': 'ola_s1x',
}

BIKE_PRICES = {
    'honda_activa': 95000, 'suzuki_access': 100000, 'bajaj_pulsar': 135000,
    're_meteor': 195000, 'ather_450x': 148000, 'ola_s1x': 100000,
    'hero_splendor': 80000,
}

BIKE_DISPLAY = {
    'hero_splendor': 'Hero Splendor Plus', 'honda_activa': 'Honda Activa 125',
    'suzuki_access': 'Suzuki Access 125', 'bajaj_pulsar': 'Bajaj Pulsar N160',
    're_meteor': 'Royal Enfield Meteor 350', 'ather_450x': 'Ather 450X',
    'ola_s1x': 'Ola S1 X', 'tvs_ntorq': 'TVS NTorq 125',
}


def compute_upgrade_score(applicant, months_completed, on_time_rate, browse_events) -> dict:
    random.seed(applicant.id * 97)
    base = 0.10
    base += on_time_rate * 0.30
    base += min(browse_events, 10) * 0.02
    base += max(0, (months_completed - 6) / applicant.tenure_months) * 0.25
    base += random.uniform(-0.05, 0.05)
    prob = round(min(base, 0.95), 3)

    if prob >= 0.65:
        band = 'Hot'
    elif prob >= 0.35:
        band = 'Warm'
    else:
        band = 'Cold'

    upgrade_bike = UPGRADE_BIKES.get(applicant.bike_model, 'ather_450x')
    new_price = BIKE_PRICES.get(upgrade_bike, 120000)
    new_emi = int(new_price * 0.85 / 24)
    current_emi = applicant.loan_amount // applicant.tenure_months
    delta = new_emi - current_emi

    upgrade_display = BIKE_DISPLAY.get(upgrade_bike, upgrade_bike.replace('_', ' ').title())
    offer = (f"Hi {applicant.name.split()[0]}! You've made {months_completed} on-time payments — "
             f"you're eligible to upgrade to a {upgrade_display} "
             f"at just ₹{new_emi:,}/month. Upgrade today, zero processing fee.")

    return {
        'upgrade_probability': prob,
        'upgrade_score_band': band,
        'recommended_bike': upgrade_bike,
        'estimated_new_emi': new_emi,
        'emi_delta': delta,
        'trigger_channel': ('App Push' if prob > 0.65 else
                            ('WhatsApp' if prob > 0.35 else 'Agent')),
        'offer_message': offer,
    }
