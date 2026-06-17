from django.db import models


class RetentionScore(models.Model):
    applicant              = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    months_completed       = models.IntegerField()
    on_time_payment_rate   = models.FloatField()
    browse_events_last_30d = models.IntegerField()
    upgrade_probability    = models.FloatField()
    upgrade_score_band     = models.CharField(max_length=10)
    recommended_bike       = models.CharField(max_length=30)
    estimated_new_emi      = models.IntegerField()
    emi_delta              = models.IntegerField()
    trigger_channel        = models.CharField(max_length=20)
    offer_message          = models.TextField()
    scored_at              = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.upgrade_score_band} ({self.upgrade_probability})"
