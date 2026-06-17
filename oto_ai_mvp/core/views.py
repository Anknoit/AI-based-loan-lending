from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q
from core.models import Applicant


@login_required
def dashboard(request):
    total = Applicant.objects.count()

    # Import counts from each layer
    from lead_scoring.models import LeadScore
    from credit_engine.models import CreditAssessment
    from fraud_detection.models import FraudAssessment
    from loan_collections.models import CollectionsAlert
    from retention.models import RetentionScore

    hot_leads = LeadScore.objects.filter(score_band='Hot').count()
    approved = CreditAssessment.objects.filter(decision='approve').count()
    fraud_flagged = FraudAssessment.objects.filter(fraud_risk_label='high').count()
    amber_red = CollectionsAlert.objects.filter(risk_bucket__in=['amber', 'red']).count()
    upgrade_hot = RetentionScore.objects.filter(upgrade_score_band='Hot').count()

    # Risk grade distribution
    grade_counts = {g: CreditAssessment.objects.filter(risk_grade=g).count()
                    for g in ['A+', 'A', 'B', 'C', 'D']}

    # Lead funnel
    scored = Applicant.objects.filter(lead_scored=True).count()
    kyc_clear = Applicant.objects.filter(kyc_done=True).count()
    underwritten = Applicant.objects.filter(underwritten=True).count()
    disbursed = Applicant.objects.filter(disbursed=True).count()

    # Collections by city
    cities = ['BLR', 'DEL', 'PUN', 'HYD', 'MUM', 'CHN', 'IND', 'JPR']
    city_labels = {'BLR': 'Bangalore', 'DEL': 'Delhi', 'PUN': 'Pune', 'HYD': 'Hyderabad',
                   'MUM': 'Mumbai', 'CHN': 'Chennai', 'IND': 'Indore', 'JPR': 'Jaipur'}
    city_collections = []
    for c in cities:
        applicant_ids = Applicant.objects.filter(city=c).values_list('id', flat=True)
        green = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='green').count()
        amber = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='amber').count()
        red = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='red').count()
        city_collections.append({'city': city_labels[c], 'green': green, 'amber': amber, 'red': red})

    # Last 20 applicants
    recent = Applicant.objects.order_by('-created_at')[:20]

    cards = [
        {'label': 'Total Applicants', 'value': total,        'color': '#1a1d23', 'sub': 'All pipeline stages'},
        {'label': 'Hot Leads',        'value': hot_leads,    'color': '#dc3545', 'sub': 'Propensity ≥ 0.70'},
        {'label': 'AI Approved',      'value': approved,     'color': '#198754', 'sub': 'PD < 10%'},
        {'label': 'Fraud Flagged',    'value': fraud_flagged,'color': '#fd7e14', 'sub': 'High risk label'},
        {'label': 'Amber/Red',        'value': amber_red,    'color': '#e63946', 'sub': 'Collections at risk'},
        {'label': 'Upgrade Ready',    'value': upgrade_hot,  'color': '#2BB780', 'sub': 'Hot upgrade score'},
    ]

    import json
    context = {
        'cards': cards,
        'grade_counts': grade_counts,
        'grade_counts_json': json.dumps(grade_counts),
        'funnel': {
            'scored': scored,
            'kyc_clear': kyc_clear,
            'underwritten': underwritten,
            'approved': approved,
            'disbursed': disbursed,
        },
        'city_collections': json.dumps(city_collections),
        'recent': recent,
    }
    return render(request, 'dashboard.html', context)
