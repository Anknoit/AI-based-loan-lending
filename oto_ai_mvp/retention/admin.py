from django.contrib import admin
from .models import RetentionScore

@admin.register(RetentionScore)
class RetentionScoreAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'upgrade_score_band', 'upgrade_probability', 'recommended_bike', 'trigger_channel']
    list_filter = ['upgrade_score_band', 'trigger_channel']
