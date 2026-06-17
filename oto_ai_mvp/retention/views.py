from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404
from .models import RetentionScore
from .services import BIKE_DISPLAY, BIKE_PRICES


@login_required
def retention_list(request):
    scores = RetentionScore.objects.select_related('applicant').order_by('-upgrade_probability')

    hot = RetentionScore.objects.filter(upgrade_score_band='Hot').count()
    warm = RetentionScore.objects.filter(upgrade_score_band='Warm').count()
    cold = RetentionScore.objects.filter(upgrade_score_band='Cold').count()

    # Bike upgrade distribution (what are hot scores being targeted for)
    bike_counts = {}
    for s in RetentionScore.objects.filter(upgrade_score_band='Hot'):
        b = BIKE_DISPLAY.get(s.recommended_bike, s.recommended_bike)
        bike_counts[b] = bike_counts.get(b, 0) + 1

    # Estimated incremental loan book if all Hot convert
    hot_scores = RetentionScore.objects.filter(upgrade_score_band='Hot').select_related('applicant')
    incremental_book = sum(
        BIKE_PRICES.get(s.recommended_bike, 100000) * 0.85 for s in hot_scores
    )

    context = {
        'scores': scores,
        'hot': hot, 'warm': warm, 'cold': cold,
        'incremental_book': round(incremental_book),
        'bike_counts': json.dumps(bike_counts),
    }
    return render(request, 'retention/retention_list.html', context)


@login_required
def retention_detail(request, pk):
    score = get_object_or_404(
        RetentionScore.objects.select_related('applicant'), applicant_id=pk)
    applicant = score.applicant

    current_emi = applicant.loan_amount // applicant.tenure_months
    bike_display = BIKE_DISPLAY.get(score.recommended_bike, score.recommended_bike)
    current_bike_display = BIKE_DISPLAY.get(applicant.bike_model, applicant.bike_model)

    context = {
        'score': score,
        'applicant': applicant,
        'current_emi': current_emi,
        'bike_display': bike_display,
        'current_bike_display': current_bike_display,
        'prob_pct': round(score.upgrade_probability * 100, 1),
    }
    return render(request, 'retention/retention_detail.html', context)


# from lifelines import CoxPHFitter
# import pandas as pd

# df = pd.DataFrame({
#     'duration': months_until_upgrade_or_last_observation,
#     'event_observed': did_upgrade,            # 1=upgraded, 0=still active
#     'on_time_rate': ...,
#     'browse_events_last_30d': ...,
#     'months_completed': ...,
#     'income_to_emi_ratio': ...,
#     'city_enc': ...,
# })

# cph = CoxPHFitter()
# cph.fit(df, duration_col='duration', event_col='event_observed')

# # Predict P(upgrade within 90 days) for new customer
# upgrade_prob = 1 - cph.predict_survival_function(
#     new_customer_df, times=[90]
# ).values[0][0]