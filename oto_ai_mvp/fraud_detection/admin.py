from django.contrib import admin
from .models import FraudAssessment

@admin.register(FraudAssessment)
class FraudAssessmentAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'fraud_risk_label', 'fraud_risk_score', 'recommended_action', 'velocity_flag']
    list_filter = ['fraud_risk_label', 'recommended_action', 'velocity_flag']
