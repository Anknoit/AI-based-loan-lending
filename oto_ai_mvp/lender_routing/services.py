import random

LENDER_PROFILES = {
    'northern_arc':   {'grades': ['A+', 'A', 'B'], 'yield': 3.2},
    'idfc_first':     {'grades': ['A+', 'A'],       'yield': 2.8},
    'ujjivan_sfb':    {'grades': ['B', 'C'],         'yield': 4.1},
    'suryoday_sfb':   {'grades': ['B', 'C', 'D'],   'yield': 4.5},
    'trillion_loans': {'grades': ['A', 'B', 'C'],   'yield': 3.6},
    'grow_money':     {'grades': ['C', 'D'],         'yield': 5.0},
    'uco_bank':       {'grades': ['A+', 'A'],        'yield': 2.5},
    'indian_bank':    {'grades': ['A+', 'A', 'B'],  'yield': 2.7},
}


def route_applicant(applicant, risk_grade: str) -> dict:
    """Thompson Sampling mock — score each lender for this risk grade."""
    random.seed(applicant.id * 53)
    scores = {}
    for lender, profile in LENDER_PROFILES.items():
        p_approval = 0.85 if risk_grade in profile['grades'] else 0.30
        p_approval += random.uniform(-0.05, 0.05)
        objective = p_approval * profile['yield']
        scores[lender] = {
            'p': round(p_approval, 3),
            'yield': profile['yield'],
            'objective': round(objective, 4),
        }
    ranked = sorted(scores.items(), key=lambda x: x[1]['objective'], reverse=True)
    primary = ranked[0]
    fallback = ranked[1]
    return {
        'selected_lender': primary[0],
        'approval_probability': primary[1]['p'],
        'expected_yield': primary[1]['yield'],
        'objective_score': primary[1]['objective'],
        'fallback_lender': fallback[0],
        'all_scores': scores,
    }
