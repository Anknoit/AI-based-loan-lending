from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from .models import CreditAssessment
from core.models import Applicant


@login_required
def credit_list(request):
    grade_counts = {g: CreditAssessment.objects.filter(risk_grade=g).count()
                    for g in ['A+', 'A', 'B', 'C', 'D']}
    decision_counts = {d: CreditAssessment.objects.filter(decision=d).count()
                       for d in ['approve', 'review', 'reject']}

    emp_pd = []
    for emp, label in [('salaried', 'Salaried'), ('self_employed', 'Self-Employed'),
                        ('gig', 'Gig'), ('student', 'Student')]:
        avg = CreditAssessment.objects.filter(
            applicant__employment_type=emp).aggregate(avg=Avg('pd_score'))['avg'] or 0
        emp_pd.append({'label': label, 'avg_pd': round(avg, 3)})

    assessments = CreditAssessment.objects.select_related('applicant').order_by('-assessed_at')[:50]

    context = {
        'grade_counts': grade_counts,
        'grade_counts_json': json.dumps(grade_counts),
        'decision_counts': decision_counts,
        'emp_pd': json.dumps(emp_pd),
        'assessments': assessments,
    }
    return render(request, 'credit_engine/credit_list.html', context)


@login_required
def credit_detail(request, pk):
    assessment = get_object_or_404(
        CreditAssessment.objects.select_related('applicant'), applicant_id=pk)
    applicant = assessment.applicant

    shap = json.loads(assessment.shap_json)
    shap_labels = []
    shap_values = []
    shap_colors = []
    friendly = {
        'bureau_score': 'Bureau Score',
        'monthly_income': 'Monthly Income',
        'upi_stability': 'UPI Stability',
        'telecom_tenure': 'Telecom Tenure',
        'loan_to_income': 'Loan-to-Income',
        'tenure_length': 'Loan Tenure',
        'employment_type': 'Employment Type',
    }
    for k, v in sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True):
        shap_labels.append(friendly.get(k, k))
        shap_values.append(v)
        shap_colors.append('#198754' if v < 0 else '#dc3545')

    pd_pct = round(assessment.pd_score * 100, 1)

    context = {
        'assessment': assessment,
        'applicant': applicant,
        'shap_labels': json.dumps(shap_labels),
        'shap_values': json.dumps(shap_values),
        'shap_colors': json.dumps(shap_colors),
        'pd_pct': pd_pct,
    }
    return render(request, 'credit_engine/credit_detail.html', context)


# import lightgbm as lgb
# import catboost as cb
# import numpy as np

# # LightGBM
# lgb_model = lgb.LGBMClassifier(
#     n_estimators=300, learning_rate=0.05,
#     num_leaves=31, min_child_samples=20
# )
# lgb_model.fit(X_train, y_train,
#               eval_set=[(X_val, y_val)],
#               callbacks=[lgb.early_stopping(50)])

# # CatBoost
# cat_features = ['employment_type', 'city', 'bike_model']
# cb_model = cb.CatBoostClassifier(
#     iterations=300, learning_rate=0.05,
#     depth=6, cat_features=cat_features, verbose=0
# )
# cb_model.fit(X_train, y_train, eval_set=(X_val, y_val))

# # Ensemble: simple average
# pd_score = (lgb_model.predict_proba(X_new)[:, 1] +
#             cb_model.predict_proba(X_new)[:, 1]) / 2


# import shap

# explainer = shap.TreeExplainer(lgb_model)
# shap_values = explainer.shap_values(X_new)
# # shap_values[1] = SHAP values for class=1 (default)
# # Each value tells you: how much did this feature push PD up or down?