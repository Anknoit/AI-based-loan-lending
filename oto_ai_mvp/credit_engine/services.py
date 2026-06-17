import random
import json

RISK_GRADES = [('A+', 0.03), ('A', 0.07), ('B', 0.13), ('C', 0.22), ('D', 0.40)]


def compute_pd(applicant, bureau_score, alt_data: dict) -> float:
    """Mock LightGBM PD output."""
    random.seed(applicant.id * 31)
    base_pd = 0.50
    if bureau_score:
        base_pd -= (bureau_score - 300) / 600 * 0.35
    income_ratio = applicant.monthly_income / (applicant.loan_amount / applicant.tenure_months)
    base_pd -= min(income_ratio * 0.04, 0.12)
    base_pd -= alt_data.get('telecom_tenure_yrs', 0) * 0.01
    base_pd += alt_data.get('upi_volatility', 0.3) * 0.08
    noise = random.uniform(-0.04, 0.04)
    return round(max(0.02, min(0.85, base_pd + noise)), 3)


def get_risk_grade(pd: float) -> str:
    for grade, threshold in RISK_GRADES:
        if pd <= threshold:
            return grade
    return 'D'


def get_decision(pd: float, bureau_score) -> str:
    if pd < 0.10:
        return 'approve'
    if pd < 0.22:
        return 'review'
    return 'reject'


def mock_shap(applicant, pd, bureau_score, alt_data) -> dict:
    """Mock SHAP feature contributions."""
    random.seed(applicant.id * 41)
    shap = {
        'bureau_score': round(-(bureau_score or 600 - 600) / 600 * 0.30, 4) if bureau_score else 0.08,
        'monthly_income': round(-min(applicant.monthly_income / 50000, 1) * 0.12, 4),
        'upi_stability': round(-alt_data.get('upi_volatility', 0.3) * 0.06, 4),
        'telecom_tenure': round(-alt_data.get('telecom_tenure_yrs', 2) * 0.01, 4),
        'loan_to_income': round((applicant.loan_amount / (applicant.monthly_income * 12)) * 0.10, 4),
        'tenure_length': round((applicant.tenure_months - 24) / 48 * 0.03, 4),
        'employment_type': {'salaried': -0.05, 'gig': 0.04, 'self_employed': 0.02, 'student': 0.09}
                           .get(applicant.employment_type, 0),
    }
    return shap
