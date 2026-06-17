from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import LeadScore
from .services import compute_propensity, get_band
from core.models import Applicant


@login_required
def lead_list(request):
    band_filter = request.GET.get('band', '')
    leads = LeadScore.objects.select_related('applicant').order_by('rank')
    if band_filter:
        leads = leads.filter(score_band=band_filter)

    hot = LeadScore.objects.filter(score_band='Hot').count()
    warm = LeadScore.objects.filter(score_band='Warm').count()
    cold = LeadScore.objects.filter(score_band='Cold').count()

    context = {
        'leads': leads,
        'band_filter': band_filter,
        'hot': hot, 'warm': warm, 'cold': cold,
    }
    return render(request, 'lead_scoring/lead_list.html', context)


@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(LeadScore.objects.select_related('applicant'), applicant_id=pk)
    applicant = lead.applicant

    features = {
        'EMI Calc Used': FEATURE_WEIGHTS_DISPLAY(lead.emi_calc_used, 0.25),
        'Return Visit': FEATURE_WEIGHTS_DISPLAY(lead.return_visit, 0.20),
        'Session Minutes': round(min(lead.session_minutes, 10) * 0.02, 4),
        'Models Viewed': round(min(lead.models_viewed, 5) * 0.05, 4),
    }

    chart_data = {
        'labels': list(features.keys()),
        'values': list(features.values()),
    }

    context = {
        'lead': lead,
        'applicant': applicant,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'lead_scoring/lead_detail.html', context)


def FEATURE_WEIGHTS_DISPLAY(val, weight):
    return round(int(val) * weight, 4)


@login_required
def rescore_lead(request, pk):
    if request.method == 'POST':
        applicant = get_object_or_404(Applicant, pk=pk)
        lead = get_object_or_404(LeadScore, applicant=applicant)
        session = {
            'emi_calc_used': lead.emi_calc_used,
            'return_visit': lead.return_visit,
            'minutes': lead.session_minutes,
            'models_viewed': lead.models_viewed,
        }
        score = compute_propensity(applicant, session)
        band = get_band(score)
        lead.propensity_score = score
        lead.score_band = band
        lead.save()
        messages.success(request, f'Lead re-scored: {score} ({band})')
    return redirect('lead_detail', pk=pk)



# example xgboost implementation
# import xgboost as xgb
# from sklearn.model_selection import train_test_split

# df = []

# X = df[['emi_calc_used','return_visit','session_minutes',
#         'models_viewed','utm_source_enc','bike_price','city_enc']]
# y = df['converted']

# X_train = []
# y_train = []
# model = xgb.XGBClassifier(
#     n_estimators=100,
#     max_depth=4,
#     learning_rate=0.1,
#     use_label_encoder=False,
#     eval_metric='logloss'
# )
# model.fit(X_train, y_train)
# propensity_score = model.predict_proba(X_new)[:, 1]  # P(convert)