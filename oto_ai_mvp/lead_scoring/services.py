import random

FEATURE_WEIGHTS = {
    'emi_calc_used': 0.25,
    'return_visit': 0.20,
    'session_minutes': 0.02,
    'models_viewed': 0.05,
}


def compute_propensity(applicant, session_data: dict) -> float:
    """Deterministic mock of XGBoost propensity model."""
    random.seed(applicant.id * 7)
    base = random.uniform(0.30, 0.55)
    score = base
    score += FEATURE_WEIGHTS['emi_calc_used'] * session_data.get('emi_calc_used', 0)
    score += FEATURE_WEIGHTS['return_visit'] * session_data.get('return_visit', 0)
    score += FEATURE_WEIGHTS['session_minutes'] * min(session_data.get('minutes', 0), 10)
    score += FEATURE_WEIGHTS['models_viewed'] * min(session_data.get('models_viewed', 0), 5)
    return round(min(score, 0.99), 3)


def get_band(score: float) -> str:
    if score >= 0.70:
        return 'Hot'
    if score >= 0.45:
        return 'Warm'
    return 'Cold'
