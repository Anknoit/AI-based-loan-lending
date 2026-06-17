from django.db import models


class KYCRecord(models.Model):
    applicant         = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    aadhaar_number    = models.CharField(max_length=12)
    pan_number        = models.CharField(max_length=10)
    dob_extracted     = models.DateField()
    name_extracted    = models.CharField(max_length=120)
    address_extracted = models.TextField()
    name_match_score  = models.FloatField()
    dob_match         = models.BooleanField()
    bureau_pulled     = models.BooleanField(default=False)
    bureau_score      = models.IntegerField(null=True)
    bureau_source     = models.CharField(max_length=20,
                            choices=[('CRIF', 'CRIF'), ('Experian', 'Experian'),
                                     ('no_hit', 'No Hit')])
    kyc_status        = models.CharField(max_length=15,
                            choices=[('clear', 'Clear'), ('review', 'Needs Review'),
                                     ('rejected', 'Rejected')])
    processed_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} — {self.kyc_status}"
