from django.db import models


class CreditAssessment(models.Model):
    applicant           = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    upi_monthly_avg     = models.IntegerField()
    upi_volatility      = models.FloatField()
    telecom_tenure_yrs  = models.FloatField()
    gst_filed           = models.BooleanField()
    pd_score            = models.FloatField()
    risk_grade          = models.CharField(max_length=3)
    recommended_ltv     = models.FloatField()
    recommended_rate    = models.FloatField()
    decision            = models.CharField(max_length=15,
                            choices=[('approve', 'Approve'), ('review', 'Manual Review'),
                                     ('reject', 'Reject')])
    shap_json           = models.TextField()
    assessed_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.risk_grade} ({self.decision})"
