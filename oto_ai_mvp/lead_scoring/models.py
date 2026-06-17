from django.db import models


class LeadScore(models.Model):
    applicant        = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    session_minutes  = models.FloatField()
    emi_calc_used    = models.BooleanField()
    models_viewed    = models.IntegerField()
    return_visit     = models.BooleanField()
    utm_source       = models.CharField(max_length=30)
    propensity_score = models.FloatField()
    score_band       = models.CharField(max_length=10)
    rank             = models.IntegerField()
    scored_at        = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.score_band} ({self.propensity_score})"
