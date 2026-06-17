from django.db import models

LENDER_CHOICES = [
    ('northern_arc', 'Northern Arc'),
    ('idfc_first', 'IDFC First Bank'),
    ('ujjivan_sfb', 'Ujjivan Small Finance Bank'),
    ('suryoday_sfb', 'Suryoday Small Finance Bank'),
    ('trillion_loans', 'Trillion Loans'),
    ('grow_money', 'Grow Money Capital'),
    ('uco_bank', 'UCO Bank'),
    ('indian_bank', 'Indian Bank'),
]


class LenderRoute(models.Model):
    applicant            = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    selected_lender      = models.CharField(max_length=20, choices=LENDER_CHOICES)
    approval_probability = models.FloatField()
    expected_yield       = models.FloatField()
    objective_score      = models.FloatField()
    fallback_lender      = models.CharField(max_length=20, choices=LENDER_CHOICES)
    lender_response      = models.CharField(max_length=15,
                             choices=[('approved', 'Approved'), ('declined', 'Declined'),
                                      ('pending', 'Pending')])
    actual_rate          = models.FloatField(null=True)
    routed_at            = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.applicant.name} → {self.selected_lender} ({self.lender_response})"
