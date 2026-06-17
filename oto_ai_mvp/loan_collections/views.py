from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404
from .models import CollectionsAlert, LoanRepayment
from core.models import Applicant


@login_required
def collections_list(request):
    alerts = CollectionsAlert.objects.select_related('applicant').order_by('-dpd_30_prob')

    green = CollectionsAlert.objects.filter(risk_bucket='green').count()
    amber = CollectionsAlert.objects.filter(risk_bucket='amber').count()
    red = CollectionsAlert.objects.filter(risk_bucket='red').count()

    # EMI at risk (amber + red)
    at_risk = CollectionsAlert.objects.filter(risk_bucket__in=['amber', 'red'])
    emi_at_risk = sum(
        a.applicant.loan_amount // a.applicant.tenure_months for a in at_risk
    )

    # City breakdown
    cities = ['BLR', 'DEL', 'PUN', 'HYD', 'MUM', 'CHN', 'IND', 'JPR']
    city_labels = {'BLR': 'BLR', 'DEL': 'DEL', 'PUN': 'PUN', 'HYD': 'HYD',
                   'MUM': 'MUM', 'CHN': 'CHN', 'IND': 'IND', 'JPR': 'JPR'}
    city_data = []
    for c in cities:
        applicant_ids = Applicant.objects.filter(city=c).values_list('id', flat=True)
        g = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='green').count()
        a = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='amber').count()
        r = CollectionsAlert.objects.filter(applicant_id__in=applicant_ids, risk_bucket='red').count()
        city_data.append({'city': city_labels[c], 'green': g, 'amber': a, 'red': r})

    context = {
        'alerts': alerts,
        'green': green, 'amber': amber, 'red': red,
        'emi_at_risk': emi_at_risk,
        'city_data': json.dumps(city_data),
    }
    return render(request, 'collections/collections_list.html', context)


@login_required
def collections_detail(request, pk):
    alert = get_object_or_404(
        CollectionsAlert.objects.select_related('applicant'), applicant_id=pk)
    applicant = alert.applicant

    repayments = LoanRepayment.objects.filter(
        applicant=applicant).order_by('month_number')

    timeline_labels = [f"M{r.month_number}" for r in repayments]
    timeline_dpd = [r.days_past_due for r in repayments]
    timeline_colors = ['#dc3545' if r.days_past_due > 0 else '#198754' for r in repayments]

    lang_display = {
        'en': 'English', 'hi': 'Hindi', 'kn': 'Kannada',
        'ta': 'Tamil', 'te': 'Telugu',
    }

    context = {
        'alert': alert,
        'applicant': applicant,
        'repayments': repayments,
        'timeline_labels': json.dumps(timeline_labels),
        'timeline_dpd': json.dumps(timeline_dpd),
        'timeline_colors': json.dumps(timeline_colors),
        'lang_display': lang_display.get(alert.language, alert.language),
        'emi': applicant.loan_amount // applicant.tenure_months,
    }
    return render(request, 'collections/collections_detail.html', context)



# [days_past_due, paid_on_time, emi_amount, 
#  outstanding_principal, month_number]

# import torch
# import torch.nn as nn

# class DelinquencyLSTM(nn.Module):
#     def __init__(self, input_size=5, hidden_size=64, num_layers=2):
#         super().__init__()
#         self.lstm = nn.LSTM(input_size, hidden_size,
#                             num_layers=num_layers, batch_first=True,
#                             dropout=0.2)
#         self.fc = nn.Linear(hidden_size, 3)   # P(30DPD), P(60DPD), P(90DPD)
#         self.sigmoid = nn.Sigmoid()

#     def forward(self, x):
#         # x shape: (batch, sequence_length, features)
#         out, _ = self.lstm(x)
#         out = self.fc(out[:, -1, :])   # last timestep
#         return self.sigmoid(out)


# i wikl use Langchains chatprompt template for geneerating custome empathatic message - not a problem ye easy hai
SYSTEM = """You are a collections assistant for OTO Capital, 
an Indian two-wheeler loan company. Write a short, 
empathetic payment reminder. Language: {language}. 
Tone: {tone}. Max 2 sentences. No threats."""

USER = """Customer: {name}, EMI: ₹{emi}, 
Days overdue: {dpd}, Risk bucket: {bucket}"""