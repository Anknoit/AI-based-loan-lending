from django.db import models


class LoanRepayment(models.Model):
    applicant    = models.ForeignKey('core.Applicant', on_delete=models.CASCADE)
    month_number = models.IntegerField()
    emi_amount   = models.IntegerField()
    paid_on_time = models.BooleanField()
    days_past_due= models.IntegerField(default=0)
    paid_date    = models.DateField(null=True)

    def __str__(self):
        return f"{self.applicant.name} — Month {self.month_number}"


class CollectionsAlert(models.Model):
    applicant            = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    dpd_30_prob          = models.FloatField()
    dpd_60_prob          = models.FloatField()
    dpd_90_prob          = models.FloatField()
    risk_bucket          = models.CharField(max_length=10,
                             choices=[('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')])
    recommended_channel  = models.CharField(max_length=20)
    generated_message    = models.TextField()
    language             = models.CharField(max_length=20)
    triggered_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.risk_bucket}"
