from django.core.management.base import BaseCommand
from faker import Faker
import random as rnd
import json
import datetime

from core.models import Applicant
from lead_scoring.models import LeadScore
from lead_scoring.services import compute_propensity, get_band
from document_kyc.models import KYCRecord
from document_kyc.services import mock_ocr_extract, name_match_score, mock_bureau_pull, determine_kyc_status
from credit_engine.models import CreditAssessment
from credit_engine.services import compute_pd, get_risk_grade, get_decision, mock_shap
from lender_routing.models import LenderRoute
from lender_routing.services import route_applicant
from fraud_detection.models import FraudAssessment
from fraud_detection.services import compute_fraud_score
from loan_collections.models import LoanRepayment, CollectionsAlert
from loan_collections.services import compute_delinquency_risk
from retention.models import RetentionScore
from retention.services import compute_upgrade_score

fake = Faker('en_IN')
rnd.seed(42)

BIKE_PRICES_MAP = {
    'hero_splendor': 80000, 'honda_activa': 95000, 'suzuki_access': 100000,
    're_meteor': 195000, 'ola_s1x': 110000, 'ather_450x': 148000,
    'bajaj_pulsar': 135000, 'tvs_ntorq': 88000,
}


class Command(BaseCommand):
    help = 'Seed 200 dummy applicants through the full AI pipeline'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        RetentionScore.objects.all().delete()
        CollectionsAlert.objects.all().delete()
        LoanRepayment.objects.all().delete()
        FraudAssessment.objects.all().delete()
        LenderRoute.objects.all().delete()
        CreditAssessment.objects.all().delete()
        KYCRecord.objects.all().delete()
        LeadScore.objects.all().delete()
        Applicant.objects.all().delete()

        self.stdout.write('Seeding 200 applicants...')
        bikes = list(BIKE_PRICES_MAP.keys())
        cities = ['BLR', 'DEL', 'PUN', 'HYD', 'MUM', 'CHN', 'IND', 'JPR']
        emp_types = ['salaried', 'self_employed', 'gig', 'student']
        emp_weights = [0.45, 0.25, 0.20, 0.10]

        for i in range(200):
            rnd.seed(i * 3)
            bike = rnd.choice(bikes)
            price = BIKE_PRICES_MAP[bike]
            down_pct = rnd.choice([0.10, 0.15, 0.20, 0.25, 0.30])
            loan_amt = int(price * (1 - down_pct))
            tenure = rnd.choice([12, 24, 36, 48])
            city = rnd.choice(cities)
            emp = rnd.choices(emp_types, weights=emp_weights)[0]
            income_base = {'salaried': 35000, 'self_employed': 45000,
                           'gig': 22000, 'student': 12000}[emp]
            income = int(income_base * rnd.uniform(0.7, 2.2))

            applicant = Applicant.objects.create(
                name=fake.name(), age=rnd.randint(21, 45), city=city,
                employment_type=emp, monthly_income=income,
                bike_model=bike, bike_price=price,
                loan_amount=loan_amt, tenure_months=tenure,
                down_payment_pct=down_pct,
                phone=fake.phone_number()[:12],
                email=fake.email(),
            )

            # Layer 1: Lead Score
            session = {
                'emi_calc_used': rnd.random() < 0.60,
                'return_visit': rnd.random() < 0.35,
                'minutes': rnd.uniform(2, 18),
                'models_viewed': rnd.randint(1, 7),
            }
            score = compute_propensity(applicant, session)
            band = get_band(score)
            LeadScore.objects.create(
                applicant=applicant,
                session_minutes=session['minutes'],
                emi_calc_used=session['emi_calc_used'],
                models_viewed=session['models_viewed'],
                return_visit=session['return_visit'],
                utm_source=rnd.choice(['organic', 'paid_search', 'paid_search', 'referral']),
                propensity_score=score,
                score_band=band,
                rank=i + 1,
            )
            applicant.lead_scored = True

            # Layer 2: KYC
            ocr = mock_ocr_extract(applicant)
            bureau = mock_bureau_pull(applicant)
            nm_score = name_match_score(ocr['name_extracted'], applicant.name)
            dob_match = rnd.random() > 0.08
            kyc_status = determine_kyc_status(nm_score, dob_match, bureau['score'])
            KYCRecord.objects.create(
                applicant=applicant,
                aadhaar_number=ocr['aadhaar'].replace(' ', ''),
                pan_number=ocr['pan'],
                dob_extracted=fake.date_of_birth(minimum_age=21, maximum_age=45),
                name_extracted=ocr['name_extracted'],
                address_extracted=fake.address(),
                name_match_score=nm_score,
                dob_match=dob_match,
                bureau_pulled=True,
                bureau_score=bureau['score'],
                bureau_source=bureau['source'],
                kyc_status=kyc_status,
            )
            applicant.kyc_done = True

            # Layer 3: Credit
            alt_data = {
                'upi_monthly_avg': int(income * rnd.uniform(0.8, 1.4)),
                'upi_volatility': round(rnd.uniform(0.05, 0.55), 3),
                'telecom_tenure_yrs': round(rnd.uniform(0.5, 10), 1),
                'gst_filed': emp == 'self_employed' and rnd.random() < 0.6,
            }
            pd_score = compute_pd(applicant, bureau['score'], alt_data)
            grade = get_risk_grade(pd_score)
            decision = get_decision(pd_score, bureau['score'])
            shap = mock_shap(applicant, pd_score, bureau['score'], alt_data)
            rate = {'A+': 8.99, 'A': 10.5, 'B': 13.0, 'C': 16.5, 'D': 20.0}[grade]
            CreditAssessment.objects.create(
                applicant=applicant,
                upi_monthly_avg=alt_data['upi_monthly_avg'],
                upi_volatility=alt_data['upi_volatility'],
                telecom_tenure_yrs=alt_data['telecom_tenure_yrs'],
                gst_filed=alt_data['gst_filed'],
                pd_score=pd_score,
                risk_grade=grade,
                recommended_ltv=round(1 - down_pct, 2),
                recommended_rate=rate,
                decision=decision,
                shap_json=json.dumps(shap),
            )
            applicant.underwritten = True

            # Layer 4: Routing
            route = route_applicant(applicant, grade)
            lender_response = ('approved' if decision == 'approve'
                               else ('pending' if decision == 'review' else 'declined'))
            LenderRoute.objects.create(
                applicant=applicant,
                selected_lender=route['selected_lender'],
                approval_probability=route['approval_probability'],
                expected_yield=route['expected_yield'],
                objective_score=route['objective_score'],
                fallback_lender=route['fallback_lender'],
                lender_response=lender_response,
                actual_rate=rate if lender_response == 'approved' else None,
            )
            applicant.routed = True

            # Layer 5: Fraud
            fraud = compute_fraud_score(applicant)
            if i in [42, 43, 44]:
                fraud['device_id'] = 'DEV-0294'
                fraud['device_reuse_count'] = 3
                fraud['velocity_flag'] = True
                fraud['fraud_risk_score'] = round(rnd.uniform(0.78, 0.92), 3)
                fraud['fraud_risk_label'] = 'high'
                fraud['recommended_action'] = 'reject'
            FraudAssessment.objects.create(applicant=applicant, **fraud)
            applicant.fraud_checked = True

            # Layer 6 + 7: Collections & Retention (disbursed only)
            if decision == 'approve':
                applicant.disbursed = True
                months_paid = rnd.randint(1, min(tenure, 18))
                emi_amt = loan_amt // tenure
                repayments = []
                for m in range(1, months_paid + 1):
                    late = rnd.random() < (0.05 + (0.15 if i % 7 == 0 else 0))
                    dpd = rnd.randint(5, 45) if late else 0
                    rep = LoanRepayment.objects.create(
                        applicant=applicant, month_number=m,
                        emi_amount=emi_amt, paid_on_time=not late, days_past_due=dpd,
                        paid_date=datetime.date.today() - datetime.timedelta(
                            days=(months_paid - m) * 30),
                    )
                    repayments.append(rep)

                delinquency = compute_delinquency_risk(applicant, repayments)
                CollectionsAlert.objects.create(applicant=applicant, **delinquency)

                browse = rnd.randint(0, 15)
                on_time_rate = round(
                    sum(1 for r in repayments if r.paid_on_time) / len(repayments), 3)
                upgrade = compute_upgrade_score(applicant, months_paid, on_time_rate, browse)
                RetentionScore.objects.create(
                    applicant=applicant,
                    months_completed=months_paid,
                    on_time_payment_rate=on_time_rate,
                    browse_events_last_30d=browse,
                    **upgrade,
                )

            applicant.save()
            if i % 20 == 0:
                self.stdout.write(f'  Seeded {i + 1}/200...')

        self.stdout.write(self.style.SUCCESS(
            'Done. 200 applicants seeded through all 7 AI layers.'))
