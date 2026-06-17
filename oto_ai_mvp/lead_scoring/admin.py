from django.contrib import admin
from .models import LeadScore

@admin.register(LeadScore)
class LeadScoreAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'score_band', 'propensity_score', 'rank', 'utm_source']
    list_filter = ['score_band', 'utm_source']
