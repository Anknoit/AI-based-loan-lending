from django.db import models

CITY_CHOICES = [
    ('BLR', 'Bangalore'), ('DEL', 'Delhi'), ('PUN', 'Pune'),
    ('HYD', 'Hyderabad'), ('MUM', 'Mumbai'), ('CHN', 'Chennai'),
    ('IND', 'Indore'), ('JPR', 'Jaipur'),
]

BIKE_CHOICES = [
    ('hero_splendor', 'Hero Splendor Plus XTEC'),
    ('honda_activa', 'Honda Activa 125'),
    ('suzuki_access', 'Suzuki Access 125'),
    ('re_meteor', 'Royal Enfield Meteor 350'),
    ('ola_s1x', 'Ola S1 X 2kWh'),
    ('ather_450x', 'Ather 450X'),
    ('bajaj_pulsar', 'Bajaj Pulsar N160'),
    ('tvs_ntorq', 'TVS NTorq 125'),
]


class Applicant(models.Model):
    name             = models.CharField(max_length=120)
    age              = models.IntegerField()
    city             = models.CharField(max_length=3, choices=CITY_CHOICES)
    employment_type  = models.CharField(max_length=20, choices=[
                           ('salaried', 'Salaried'), ('self_employed', 'Self-Employed'),
                           ('gig', 'Gig Worker'), ('student', 'Student')])
    monthly_income   = models.IntegerField()
    bike_model       = models.CharField(max_length=30, choices=BIKE_CHOICES)
    bike_price       = models.IntegerField()
    loan_amount      = models.IntegerField()
    tenure_months    = models.IntegerField()
    down_payment_pct = models.FloatField()
    created_at       = models.DateTimeField(auto_now_add=True)
    phone            = models.CharField(max_length=12)
    email            = models.EmailField()

    lead_scored      = models.BooleanField(default=False)
    kyc_done         = models.BooleanField(default=False)
    underwritten     = models.BooleanField(default=False)
    routed           = models.BooleanField(default=False)
    fraud_checked    = models.BooleanField(default=False)
    disbursed        = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.get_bike_model_display()}"
