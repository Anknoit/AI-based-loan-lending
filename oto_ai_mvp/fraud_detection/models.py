from django.db import models


class FraudAssessment(models.Model):
    applicant            = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    device_id            = models.CharField(max_length=40)
    ip_address           = models.GenericIPAddressField()
    device_reuse_count   = models.IntegerField()
    ip_reuse_count       = models.IntegerField()
    address_cluster_size = models.IntegerField()
    shared_phone_count   = models.IntegerField()
    velocity_flag        = models.BooleanField()
    synthetic_id_flag    = models.BooleanField()
    fraud_risk_score     = models.FloatField()
    fraud_risk_label     = models.CharField(max_length=10,
                              choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    recommended_action   = models.CharField(max_length=20,
                              choices=[('pass', 'Pass'), ('manual_review', 'Manual Review'),
                                       ('reject', 'Reject'), ('watchlist', 'Watchlist')])
    checked_at           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.fraud_risk_label} ({self.fraud_risk_score})"
