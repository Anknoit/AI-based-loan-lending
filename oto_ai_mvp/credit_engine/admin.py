from django.contrib import admin
from .models import CreditAssessment

@admin.register(CreditAssessment)
class CreditAssessmentAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'risk_grade', 'pd_score', 'decision', 'recommended_rate']
    list_filter = ['risk_grade', 'decision']
