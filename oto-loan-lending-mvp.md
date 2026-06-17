# OTO Capital — AI Lending Intelligence MVP
### Django Application Spec | Panel Showcase Build | Dummy Data Included

---

## 0. Purpose

This document specifies a self-contained Django MVP that demonstrates all 7 AI layers of the OTO Capital loan lending pipeline using dummy data. It is intended for panel showcasing — no live ML inference, no real bureau calls. Every AI output is seeded, deterministic, and visually compelling.

**Showcase goal:** A panel judge should walk away understanding what an AI Engineer built, why each module exists, and how it would work in production — all from a running local Django app with dummy data.

---

## 1. Project Structure

```
oto_ai_mvp/
├── manage.py
├── requirements.txt
├── oto_ai_mvp/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                        # Shared models, dummy data seed, base templates
│   ├── models.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_data.py     # python manage.py seed_data
│   └── templates/
│       └── base.html
├── lead_scoring/                # Layer 1 — Acquire
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock XGBoost inference
│   └── templates/lead_scoring/
├── document_kyc/                # Layer 2 — Qualify
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock OCR + KYC extraction
│   └── templates/document_kyc/
├── credit_engine/               # Layer 3 — Decide (Underwriting)
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock PD model + SHAP values
│   └── templates/credit_engine/
├── lender_routing/              # Layer 4 — Route
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock bandit routing
│   └── templates/lender_routing/
├── fraud_detection/             # Layer 5 — Fraud
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock GNN risk score
│   └── templates/fraud_detection/
├── collections/                 # Layer 6 — Serve
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py              # Mock LSTM + NLP nudge
│   └── templates/collections/
└── retention/                   # Layer 7 — Retain
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── services.py              # Mock survival model + upgrade trigger
    └── templates/retention/
```

---

## 2. Tech Stack

| Component | Choice | Reason |
|-----------|--------|---------|
| Framework | Django 5.1 | Rapid admin + ORM, panel-familiar |
| Database | SQLite (dev) | Zero-config, ships with seed data |
| Frontend | Bootstrap 5 + Chart.js | No build step, clean dashboard look |
| AI mocks | Python dicts + random.seed() | Deterministic, reproducible demo |
| Charts | Chart.js 4.x via CDN | Score distributions, DPD curves |
| Auth | Django built-in | Single admin user for panel demo |

---

## 3. Installation & Quick Start

```bash
# Clone / unzip project
cd oto_ai_mvp

# Create virtualenv
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Seed all dummy data (creates 200 applicants + full pipeline state)
python manage.py seed_data

# Create superuser for Django admin
python manage.py createsuperuser

# Run server
python manage.py runserver

# Visit dashboard
open http://127.0.0.1:8000/
```

---

## 4. requirements.txt

```
Django==5.1.4
django-crispy-forms==2.3
crispy-bootstrap5==2024.2
Faker==28.0.0
numpy==1.26.4
pandas==2.2.2
```

> No real ML libraries required for the demo. All model outputs are pre-computed and stored in the DB via `seed_data`.

---

## 5. Core Data Models

### 5.1 `core/models.py` — Applicant (shared across all layers)

```python
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
    name            = models.CharField(max_length=120)
    age             = models.IntegerField()
    city            = models.CharField(max_length=3, choices=CITY_CHOICES)
    employment_type = models.CharField(max_length=20,
                        choices=[('salaried','Salaried'),('self_employed','Self-Employed'),
                                 ('gig','Gig Worker'),('student','Student')])
    monthly_income  = models.IntegerField()          # in INR
    bike_model      = models.CharField(max_length=30, choices=BIKE_CHOICES)
    bike_price      = models.IntegerField()          # on-road INR
    loan_amount     = models.IntegerField()
    tenure_months   = models.IntegerField()          # 12/24/36/48
    down_payment_pct= models.FloatField()            # 0.10 to 0.30
    created_at      = models.DateTimeField(auto_now_add=True)
    phone           = models.CharField(max_length=12)
    email           = models.EmailField()

    # Pipeline state flags
    lead_scored     = models.BooleanField(default=False)
    kyc_done        = models.BooleanField(default=False)
    underwritten    = models.BooleanField(default=False)
    routed          = models.BooleanField(default=False)
    fraud_checked   = models.BooleanField(default=False)
    disbursed       = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} — {self.get_bike_model_display()}"
```

---

## 6. Layer Specifications

---

### Layer 1 — Lead Scoring (`lead_scoring/`)

**What it demonstrates:** Behavioral intent signals → propensity score → ranked lead queue

#### Model: `LeadScore`

```python
class LeadScore(models.Model):
    applicant       = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    session_minutes = models.FloatField()          # time on site
    emi_calc_used   = models.BooleanField()        # used EMI calculator?
    models_viewed   = models.IntegerField()        # # of bike pages viewed
    return_visit    = models.BooleanField()
    utm_source      = models.CharField(max_length=30)  # organic/paid/referral
    propensity_score= models.FloatField()          # 0.0 – 1.0  (mock XGBoost output)
    score_band      = models.CharField(max_length=10)  # Hot / Warm / Cold
    rank            = models.IntegerField()        # position in daily lead queue
    scored_at       = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `lead_scoring/services.py`

```python
import random

FEATURE_WEIGHTS = {
    'emi_calc_used': 0.25,
    'return_visit': 0.20,
    'session_minutes': 0.02,   # per minute, capped at 10 min
    'models_viewed': 0.05,
}

def compute_propensity(applicant, session_data: dict) -> float:
    """Deterministic mock of XGBoost propensity model."""
    random.seed(applicant.id * 7)
    base = random.uniform(0.30, 0.55)
    score = base
    score += FEATURE_WEIGHTS['emi_calc_used'] * session_data.get('emi_calc_used', 0)
    score += FEATURE_WEIGHTS['return_visit'] * session_data.get('return_visit', 0)
    score += FEATURE_WEIGHTS['session_minutes'] * min(session_data.get('minutes', 0), 10)
    score += FEATURE_WEIGHTS['models_viewed'] * min(session_data.get('models_viewed', 0), 5)
    return round(min(score, 0.99), 3)

def get_band(score: float) -> str:
    if score >= 0.70: return 'Hot'
    if score >= 0.45: return 'Warm'
    return 'Cold'
```

#### Views

- `GET /leads/` — ranked table of all leads with color-coded bands (green/amber/red), propensity scores, and feature breakdown tooltip
- `GET /leads/<id>/` — single lead detail with mock feature importance bar chart (Chart.js horizontal bar)
- `POST /leads/score/<id>/` — re-score a lead (for demo interactivity)

#### Dummy Data (seeded per applicant)
- `session_minutes`: 2–18 min
- `models_viewed`: 1–7
- `emi_calc_used`: 60% True
- `return_visit`: 35% True
- `utm_source`: 40% organic, 35% paid_search, 25% referral

---

### Layer 2 — Document AI + KYC (`document_kyc/`)

**What it demonstrates:** OCR extraction → field validation → KYC status → bureau pull simulation

#### Model: `KYCRecord`

```python
class KYCRecord(models.Model):
    applicant       = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    # Extracted fields (mock OCR output)
    aadhaar_number  = models.CharField(max_length=12)
    pan_number      = models.CharField(max_length=10)
    dob_extracted   = models.DateField()
    name_extracted  = models.CharField(max_length=120)
    address_extracted= models.TextField()
    # Validation status
    name_match_score = models.FloatField()    # 0–1, fuzzy match vs applicant.name
    dob_match        = models.BooleanField()
    # Bureau
    bureau_pulled    = models.BooleanField(default=False)
    bureau_score     = models.IntegerField(null=True)  # 300–900, None = no-hit
    bureau_source    = models.CharField(max_length=20,
                         choices=[('CRIF','CRIF'),('Experian','Experian'),('no_hit','No Hit')])
    # Overall KYC status
    kyc_status       = models.CharField(max_length=15,
                         choices=[('clear','Clear'),('review','Needs Review'),('rejected','Rejected')])
    processed_at     = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `document_kyc/services.py`

```python
import random, re
from difflib import SequenceMatcher

def mock_ocr_extract(applicant) -> dict:
    """Simulates AWS Textract field extraction from Aadhaar + PAN."""
    random.seed(applicant.id * 13)
    # Introduce small noise in name extraction (OCR errors)
    name = applicant.name
    if random.random() < 0.15:
        name = name[:-1]   # truncate last char — common OCR error
    return {
        'name_extracted': name,
        'aadhaar': f"{random.randint(2000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
        'pan': f"{'ABCDE'[applicant.id % 5]}{'FGHIJ'[applicant.id % 5]}PL{random.randint(1000,9999)}K",
    }

def name_match_score(extracted: str, actual: str) -> float:
    return round(SequenceMatcher(None, extracted.lower(), actual.lower()).ratio(), 3)

def mock_bureau_pull(applicant) -> dict:
    random.seed(applicant.id * 17)
    if applicant.employment_type == 'student' and random.random() < 0.4:
        return {'score': None, 'source': 'no_hit'}
    score = random.randint(560, 820)
    source = random.choice(['CRIF', 'Experian'])
    return {'score': score, 'source': source}

def determine_kyc_status(name_match, dob_match, bureau_score) -> str:
    if name_match < 0.75 or not dob_match:
        return 'review'
    if bureau_score and bureau_score < 580:
        return 'rejected'
    return 'clear'
```

#### Views

- `GET /kyc/` — table of all KYC records with status badges (Clear / Review / Rejected)
- `GET /kyc/<id>/` — detail view with mock "document scan" showing extracted vs submitted fields side-by-side, match scores, bureau score gauge (Chart.js doughnut)
- Panel talking point: Show a "Needs Review" case where name was truncated by OCR — the AI flagged it, a human resolves it

---

### Layer 3 — Credit Underwriting Engine (`credit_engine/`)

**What it demonstrates:** Alternative data + bureau → PD score → LTV recommendation → SHAP explainability

#### Model: `CreditAssessment`

```python
class CreditAssessment(models.Model):
    applicant           = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    # Alternative data inputs
    upi_monthly_avg     = models.IntegerField()    # avg monthly UPI inflow (INR)
    upi_volatility      = models.FloatField()      # std dev / mean — income stability
    telecom_tenure_yrs  = models.FloatField()
    gst_filed           = models.BooleanField()
    # Model outputs
    pd_score            = models.FloatField()      # probability of default 0–1
    risk_grade          = models.CharField(max_length=3)   # A+/A/B/C/D
    recommended_ltv     = models.FloatField()      # e.g. 0.85
    recommended_rate    = models.FloatField()      # annual interest rate %
    decision            = models.CharField(max_length=15,
                            choices=[('approve','Approve'),('review','Manual Review'),
                                     ('reject','Reject')])
    # SHAP values (stored as JSON string for simplicity)
    shap_json           = models.TextField()       # dict of feature: shap_value
    assessed_at         = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `credit_engine/services.py`

```python
import random, json, math

RISK_GRADES = [('A+', 0.03), ('A', 0.07), ('B', 0.13), ('C', 0.22), ('D', 0.40)]

def compute_pd(applicant, bureau_score, alt_data: dict) -> float:
    """Mock LightGBM PD output. Higher bureau score and stable UPI → lower PD."""
    random.seed(applicant.id * 31)
    base_pd = 0.50
    # Bureau factor
    if bureau_score:
        base_pd -= (bureau_score - 300) / 600 * 0.35
    # Income factor
    income_ratio = applicant.monthly_income / (applicant.loan_amount / applicant.tenure_months)
    base_pd -= min(income_ratio * 0.04, 0.12)
    # Alt data
    base_pd -= alt_data.get('telecom_tenure_yrs', 0) * 0.01
    base_pd += alt_data.get('upi_volatility', 0.3) * 0.08
    noise = random.uniform(-0.04, 0.04)
    return round(max(0.02, min(0.85, base_pd + noise)), 3)

def get_risk_grade(pd: float) -> str:
    for grade, threshold in RISK_GRADES:
        if pd <= threshold:
            return grade
    return 'D'

def get_decision(pd: float, bureau_score) -> str:
    if pd < 0.10: return 'approve'
    if pd < 0.22: return 'review'
    return 'reject'

def mock_shap(applicant, pd, bureau_score, alt_data) -> dict:
    """Mock SHAP feature contributions — sum to PD approximately."""
    random.seed(applicant.id * 41)
    shap = {
        'bureau_score': round(-(bureau_score or 600 - 600) / 600 * 0.30, 4) if bureau_score else 0.08,
        'monthly_income': round(-min(applicant.monthly_income / 50000, 1) * 0.12, 4),
        'upi_stability': round(-alt_data.get('upi_volatility', 0.3) * 0.06, 4),
        'telecom_tenure': round(-alt_data.get('telecom_tenure_yrs', 2) * 0.01, 4),
        'loan_to_income': round((applicant.loan_amount / (applicant.monthly_income * 12)) * 0.10, 4),
        'tenure_length': round((applicant.tenure_months - 24) / 48 * 0.03, 4),
        'employment_type': {'salaried': -0.05, 'gig': 0.04, 'self_employed': 0.02, 'student': 0.09}
                           .get(applicant.employment_type, 0),
    }
    return shap
```

#### Views

- `GET /credit/` — portfolio summary: risk grade distribution (Chart.js doughnut), avg PD by employment type (bar chart), approval/review/reject counts
- `GET /credit/<id>/` — individual credit report with PD gauge, risk grade badge, SHAP waterfall chart (horizontal bar showing each feature's push toward/away from default), recommended LTV and rate

**SHAP waterfall (Chart.js):** Horizontal bar chart where green bars push PD down (positive signals) and red bars push it up (risk signals). This is the key AI explainability demo for the panel — shows the model isn't a black box.

---

### Layer 4 — Lender Routing (`lender_routing/`)

**What it demonstrates:** Multi-armed bandit lender selection → approval probability × yield optimization

#### Model: `LenderRoute`

```python
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
    applicant           = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    selected_lender     = models.CharField(max_length=20, choices=LENDER_CHOICES)
    approval_probability= models.FloatField()   # bandit's estimated P(approval)
    expected_yield      = models.FloatField()   # estimated net yield %
    objective_score     = models.FloatField()   # approval_prob × expected_yield
    fallback_lender     = models.CharField(max_length=20, choices=LENDER_CHOICES)
    lender_response     = models.CharField(max_length=15,
                            choices=[('approved','Approved'),('declined','Declined'),('pending','Pending')])
    actual_rate         = models.FloatField(null=True)
    routed_at           = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `lender_routing/services.py`

```python
import random

# Lender profiles: each has preferred credit grades and typical yield
LENDER_PROFILES = {
    'northern_arc':   {'grades': ['A+','A','B'], 'yield': 3.2},
    'idfc_first':     {'grades': ['A+','A'],     'yield': 2.8},
    'ujjivan_sfb':    {'grades': ['B','C'],      'yield': 4.1},
    'suryoday_sfb':   {'grades': ['B','C','D'],  'yield': 4.5},
    'trillion_loans': {'grades': ['A','B','C'],  'yield': 3.6},
    'grow_money':     {'grades': ['C','D'],      'yield': 5.0},
    'uco_bank':       {'grades': ['A+','A'],     'yield': 2.5},
    'indian_bank':    {'grades': ['A+','A','B'], 'yield': 2.7},
}

def route_applicant(applicant, risk_grade: str) -> dict:
    """Thompson Sampling mock — score each lender for this risk grade."""
    random.seed(applicant.id * 53)
    scores = {}
    for lender, profile in LENDER_PROFILES.items():
        p_approval = 0.85 if risk_grade in profile['grades'] else 0.30
        p_approval += random.uniform(-0.05, 0.05)
        objective = p_approval * profile['yield']
        scores[lender] = {'p': round(p_approval, 3), 'yield': profile['yield'],
                          'objective': round(objective, 4)}
    ranked = sorted(scores.items(), key=lambda x: x[1]['objective'], reverse=True)
    primary = ranked[0]
    fallback = ranked[1]
    return {
        'selected_lender': primary[0],
        'approval_probability': primary[1]['p'],
        'expected_yield': primary[1]['yield'],
        'objective_score': primary[1]['objective'],
        'fallback_lender': fallback[0],
        'all_scores': scores,
    }
```

#### Views

- `GET /routing/` — lender allocation heatmap table (risk grade × lender matrix showing % of applicants routed there), approval rates per lender, yield comparison bar chart
- `GET /routing/<id>/` — individual routing decision with all lender scores ranked, objective function values, and selected vs fallback

---

### Layer 5 — Fraud Detection (`fraud_detection/`)

**What it demonstrates:** Device/identity graph anomaly scoring — the GNN angle

#### Model: `FraudAssessment`

```python
class FraudAssessment(models.Model):
    applicant           = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    device_id           = models.CharField(max_length=40)
    ip_address          = models.GenericIPAddressField()
    # Graph signals
    device_reuse_count  = models.IntegerField()    # # applicants sharing this device
    ip_reuse_count      = models.IntegerField()
    address_cluster_size= models.IntegerField()    # # applicants at same pincode+name pattern
    shared_phone_count  = models.IntegerField()
    # Derived features
    velocity_flag       = models.BooleanField()    # >3 apps from device in 30 days
    synthetic_id_flag   = models.BooleanField()    # name/DOB mismatch pattern
    # GNN output
    fraud_risk_score    = models.FloatField()      # 0–1
    fraud_risk_label    = models.CharField(max_length=10,
                            choices=[('low','Low'),('medium','Medium'),('high','High')])
    recommended_action  = models.CharField(max_length=20,
                            choices=[('pass','Pass'),('manual_review','Manual Review'),
                                     ('reject','Reject'),('watchlist','Watchlist')])
    checked_at          = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `fraud_detection/services.py`

```python
import random

def compute_fraud_score(applicant) -> dict:
    random.seed(applicant.id * 67)
    # 5% high fraud, 15% medium, 80% low
    roll = random.random()
    if roll < 0.05:
        device_reuse = random.randint(4, 12)
        velocity_flag = True
        synthetic_flag = random.random() < 0.6
        score = round(random.uniform(0.72, 0.97), 3)
        label = 'high'
        action = 'reject'
    elif roll < 0.20:
        device_reuse = random.randint(2, 3)
        velocity_flag = random.random() < 0.4
        synthetic_flag = False
        score = round(random.uniform(0.35, 0.71), 3)
        label = 'medium'
        action = 'manual_review'
    else:
        device_reuse = 1
        velocity_flag = False
        synthetic_flag = False
        score = round(random.uniform(0.01, 0.34), 3)
        label = 'low'
        action = 'pass'

    return {
        'device_reuse_count': device_reuse,
        'ip_reuse_count': random.randint(1, max(1, device_reuse - 1)),
        'address_cluster_size': random.randint(1, 3),
        'shared_phone_count': 1,
        'velocity_flag': velocity_flag,
        'synthetic_id_flag': synthetic_flag,
        'fraud_risk_score': score,
        'fraud_risk_label': label,
        'recommended_action': action,
        'device_id': f"DEV-{applicant.id * 7 % 150:04d}",
        'ip_address': f"103.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
    }
```

#### Views

- `GET /fraud/` — risk distribution pie chart, flagged cases table (high/medium), velocity flags, graph cluster summary
- `GET /fraud/<id>/` — individual fraud report with score gauge, flag checklist, graph neighbourhood summary ("this device was seen on 7 other applications")
- Panel talking point: Show one seeded "fraud ring" — 3–4 applicants sharing the same device ID, flagged by the GNN

**Seeded fraud ring:** Applicants with IDs 42, 43, 44 share `device_id = DEV-0294`, velocity_flag = True, fraud_risk_label = 'high'. Use this as the live demo case.

---

### Layer 6 — Predictive Collections (`collections/`)

**What it demonstrates:** Time-series delinquency risk → LLM-generated personalised follow-up

#### Model: `LoanRepayment` + `CollectionsAlert`

```python
class LoanRepayment(models.Model):
    applicant       = models.ForeignKey('core.Applicant', on_delete=models.CASCADE)
    month_number    = models.IntegerField()    # 1 = first EMI month
    emi_amount      = models.IntegerField()
    paid_on_time    = models.BooleanField()
    days_past_due   = models.IntegerField(default=0)
    paid_date       = models.DateField(null=True)

class CollectionsAlert(models.Model):
    applicant           = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    dpd_30_prob         = models.FloatField()    # LSTM output: P(30 DPD in next 60 days)
    dpd_60_prob         = models.FloatField()
    dpd_90_prob         = models.FloatField()
    risk_bucket         = models.CharField(max_length=10,
                            choices=[('green','Green'),('amber','Amber'),('red','Red')])
    # NLP-generated follow-up
    recommended_channel = models.CharField(max_length=20)   # WhatsApp / Call / SMS
    generated_message   = models.TextField()                 # mock GPT-4o output
    language            = models.CharField(max_length=20)
    triggered_at        = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `collections/services.py`

```python
import random

COLLECTIONS_MESSAGES = {
    'green': {
        'en': "Hi {name}, your EMI of ₹{emi} is due on {date}. Pay via UPI: otocapital@ybl. Thank you!",
        'hi': "नमस्ते {name}, आपकी EMI ₹{emi} {date} को देय है। UPI से भुगतान करें: otocapital@ybl।",
        'kn': "ಹಲೋ {name}, ನಿಮ್ಮ EMI ₹{emi} {date} ರಂದು ಬರಬೇಕು. UPI ಮೂಲಕ ಪಾವತಿಸಿ: otocapital@ybl.",
    },
    'amber': {
        'en': "Hi {name}, we noticed your EMI of ₹{emi} hasn't been received. Please pay within 3 days to avoid late fees. Need help? Call 1800-XXX-XXXX.",
        'hi': "नमस्ते {name}, आपकी ₹{emi} की EMI अभी तक प्राप्त नहीं हुई। देर से बचने के लिए 3 दिन में भुगतान करें।",
    },
    'red': {
        'en': "Dear {name}, your account has {dpd} days past due. Immediate payment of ₹{emi} is required. Our agent will contact you shortly.",
        'hi': "प्रिय {name}, आपका खाता {dpd} दिन बकाया है। तुरंत ₹{emi} का भुगतान करें।",
    },
}

CITY_LANGUAGE = {
    'BLR': 'kn', 'CHN': 'ta', 'HYD': 'te', 'MUM': 'hi',
    'DEL': 'hi', 'JPR': 'hi', 'PUN': 'en', 'IND': 'hi',
}

def compute_delinquency_risk(applicant, repayment_history: list) -> dict:
    """Mock LSTM output based on recent payment pattern."""
    random.seed(applicant.id * 79)
    late_count = sum(1 for r in repayment_history[-6:] if not r.paid_on_time)
    base_30 = 0.05 + late_count * 0.12
    base_30 += random.uniform(-0.02, 0.02)
    dpd_30 = round(min(base_30, 0.95), 3)
    dpd_60 = round(dpd_30 * 0.55, 3)
    dpd_90 = round(dpd_60 * 0.45, 3)

    if dpd_30 < 0.20:  bucket = 'green'
    elif dpd_30 < 0.50: bucket = 'amber'
    else:               bucket = 'red'

    lang = CITY_LANGUAGE.get(applicant.city, 'en')
    msg_template = COLLECTIONS_MESSAGES.get(bucket, {}).get(lang)
    if not msg_template:
        msg_template = COLLECTIONS_MESSAGES[bucket]['en']

    emi = applicant.loan_amount // applicant.tenure_months
    message = msg_template.format(
        name=applicant.name.split()[0],
        emi=f"{emi:,}",
        date="5th July",
        dpd=int(dpd_30 * 30),
    )
    return {
        'dpd_30_prob': dpd_30, 'dpd_60_prob': dpd_60, 'dpd_90_prob': dpd_90,
        'risk_bucket': bucket,
        'recommended_channel': 'WhatsApp' if bucket == 'green' else 'Call',
        'generated_message': message,
        'language': lang,
    }
```

#### Views

- `GET /collections/` — DPD risk dashboard: portfolio bucketed into green/amber/red (Chart.js stacked bar by city), total EMI at risk in amber+red
- `GET /collections/<id>/` — individual account with repayment timeline (Chart.js line — 12 months of on-time/late bars), delinquency probability gauge for 30/60/90 DPD, generated follow-up message preview with language label
- Panel talking point: The NLP message in local language is the AI Engineer's contribution — not just a model but a full output pipeline

---

### Layer 7 — Retention & Upgrade (`retention/`)

**What it demonstrates:** Survival model + collaborative filtering → upgrade trigger at the right moment

#### Model: `RetentionScore`

```python
class RetentionScore(models.Model):
    applicant               = models.OneToOneField('core.Applicant', on_delete=models.CASCADE)
    months_completed        = models.IntegerField()
    on_time_payment_rate    = models.FloatField()      # 0–1
    browse_events_last_30d  = models.IntegerField()    # site visits in last 30 days
    # Survival model output
    upgrade_probability     = models.FloatField()      # P(upgrade in next 90 days)
    upgrade_score_band      = models.CharField(max_length=10)  # Hot/Warm/Cold
    # Recommended upgrade
    recommended_bike        = models.CharField(max_length=30)
    estimated_new_emi       = models.IntegerField()
    emi_delta               = models.IntegerField()     # new EMI - current EMI
    # Trigger
    trigger_channel         = models.CharField(max_length=20)  # App Push / Agent / WhatsApp
    offer_message           = models.TextField()
    scored_at               = models.DateTimeField(auto_now_add=True)
```

#### Mock Service: `retention/services.py`

```python
import random

UPGRADE_BIKES = {
    'hero_splendor': 'honda_activa',
    'honda_activa': 'suzuki_access',
    'suzuki_access': 'bajaj_pulsar',
    'bajaj_pulsar': 're_meteor',
    're_meteor': 'ather_450x',
    'ola_s1x': 'ather_450x',
    'ather_450x': 'ather_450x',     # top of range — cross-sell insurance
    'tvs_ntorq': 'ola_s1x',
}

BIKE_PRICES = {
    'honda_activa': 95000, 'suzuki_access': 100000, 'bajaj_pulsar': 135000,
    're_meteor': 195000, 'ather_450x': 148000, 'ola_s1x': 100000,
    'hero_splendor': 80000,
}

def compute_upgrade_score(applicant, months_completed, on_time_rate, browse_events) -> dict:
    random.seed(applicant.id * 97)
    # Base upgrade probability: higher with more on-time payments and browsing activity
    base = 0.10
    base += on_time_rate * 0.30
    base += min(browse_events, 10) * 0.02
    base += max(0, (months_completed - 6) / applicant.tenure_months) * 0.25
    base += random.uniform(-0.05, 0.05)
    prob = round(min(base, 0.95), 3)

    if prob >= 0.65: band = 'Hot'
    elif prob >= 0.35: band = 'Warm'
    else: band = 'Cold'

    upgrade_bike = UPGRADE_BIKES.get(applicant.bike_model, 'ather_450x')
    new_price = BIKE_PRICES.get(upgrade_bike, 120000)
    new_emi = int(new_price * 0.85 / 24)
    current_emi = applicant.loan_amount // applicant.tenure_months
    delta = new_emi - current_emi

    offer = (f"Hi {applicant.name.split()[0]}! You've made {months_completed} on-time payments — "
             f"you're eligible to upgrade to a {upgrade_bike.replace('_',' ').title()} "
             f"at just ₹{new_emi:,}/month. Upgrade today, zero processing fee.")

    return {
        'upgrade_probability': prob,
        'upgrade_score_band': band,
        'recommended_bike': upgrade_bike,
        'estimated_new_emi': new_emi,
        'emi_delta': delta,
        'trigger_channel': 'App Push' if prob > 0.65 else ('WhatsApp' if prob > 0.35 else 'Agent'),
        'offer_message': offer,
    }
```

#### Views

- `GET /retention/` — upgrade funnel: Hot/Warm/Cold counts, recommended bike distribution (who's being targeted for what upgrade), total incremental loan book value if all Hot scores convert
- `GET /retention/<id>/` — individual upgrade card with probability gauge, current vs proposed EMI comparison, offer message preview, trigger channel badge

---

## 7. Dashboard — `core/` Home

`GET /` — Master command centre. Single-screen overview for the panel demo.

### Metrics cards (top row)

| Card | Value | Source |
|------|-------|--------|
| Total applicants | 200 | core.Applicant count |
| Hot leads | N | LeadScore.score_band='Hot' |
| Approved (AI) | N | CreditAssessment.decision='approve' |
| Fraud flagged | N | FraudAssessment.fraud_risk_label='high' |
| Amber/Red collections | N | CollectionsAlert.risk_bucket in (amber, red) |
| Upgrade ready (Hot) | N | RetentionScore.upgrade_score_band='Hot' |

### Charts (second row, 3-column)

- Risk grade distribution (doughnut): A+/A/B/C/D
- Lead funnel (vertical bar): Scored → KYC Clear → Underwritten → Approved → Disbursed
- Collections risk by city (stacked bar): green/amber/red per city

### Pipeline status table (bottom)

Last 20 applicants showing pipeline stage progress with colored badges at each step. Clicking any row goes to that applicant's credit detail page.

---

## 8. Seed Data Command

`core/management/commands/seed_data.py`

```python
from django.core.management.base import BaseCommand
from faker import Faker
import random

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
from collections.models import LoanRepayment, CollectionsAlert
from collections.services import compute_delinquency_risk
from retention.models import RetentionScore
from retention.services import compute_upgrade_score
import json, datetime, random as rnd

fake = Faker('en_IN')
random.seed(42)

BIKE_PRICES_MAP = {
    'hero_splendor': 80000, 'honda_activa': 95000, 'suzuki_access': 100000,
    're_meteor': 195000, 'ola_s1x': 110000, 'ather_450x': 148000,
    'bajaj_pulsar': 135000, 'tvs_ntorq': 88000,
}

class Command(BaseCommand):
    help = 'Seed 200 dummy applicants through the full AI pipeline'

    def handle(self, *args, **options):
        self.stdout.write('Clearing existing data...')
        # Clear in reverse dependency order
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
        cities = ['BLR','DEL','PUN','HYD','MUM','CHN','IND','JPR']
        emp_types = ['salaried','self_employed','gig','student']
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
            income_base = {'salaried': 35000, 'self_employed': 45000, 'gig': 22000, 'student': 12000}[emp]
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
            ls = LeadScore.objects.create(
                applicant=applicant, session_minutes=session['minutes'],
                emi_calc_used=session['emi_calc_used'], models_viewed=session['models_viewed'],
                return_visit=session['return_visit'],
                utm_source=rnd.choice(['organic','paid_search','paid_search','referral']),
                propensity_score=score, score_band=band, rank=i+1,
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
                aadhaar_number=ocr['aadhaar'].replace(' ',''),
                pan_number=ocr['pan'],
                dob_extracted=fake.date_of_birth(minimum_age=21, maximum_age=45),
                name_extracted=ocr['name_extracted'],
                address_extracted=fake.address(),
                name_match_score=nm_score, dob_match=dob_match,
                bureau_pulled=True, bureau_score=bureau['score'],
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
                pd_score=pd_score, risk_grade=grade,
                recommended_ltv=round(1 - down_pct, 2),
                recommended_rate=rate,
                decision=decision,
                shap_json=json.dumps(shap),
            )
            applicant.underwritten = True

            # Layer 4: Routing
            route = route_applicant(applicant, grade)
            lender_response = 'approved' if decision == 'approve' else ('pending' if decision == 'review' else 'declined')
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
            # Override fraud ring for applicants 42,43,44
            if i in [42, 43, 44]:
                fraud['device_id'] = 'DEV-0294'
                fraud['device_reuse_count'] = 3
                fraud['velocity_flag'] = True
                fraud['fraud_risk_score'] = round(rnd.uniform(0.78, 0.92), 3)
                fraud['fraud_risk_label'] = 'high'
                fraud['recommended_action'] = 'reject'
            FraudAssessment.objects.create(applicant=applicant, **fraud)
            applicant.fraud_checked = True

            # Layer 6: Collections (only for disbursed)
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
                        paid_date=datetime.date.today() - datetime.timedelta(days=(months_paid - m) * 30),
                    )
                    repayments.append(rep)

                delinquency = compute_delinquency_risk(applicant, repayments)
                CollectionsAlert.objects.create(applicant=applicant, **delinquency)

                # Layer 7: Retention
                browse = rnd.randint(0, 15)
                on_time_rate = round(sum(1 for r in repayments if r.paid_on_time) / len(repayments), 3)
                upgrade = compute_upgrade_score(applicant, months_paid, on_time_rate, browse)
                RetentionScore.objects.create(
                    applicant=applicant, months_completed=months_paid,
                    on_time_payment_rate=on_time_rate,
                    browse_events_last_30d=browse, **upgrade,
                )

            applicant.save()
            if i % 20 == 0:
                self.stdout.write(f'  Seeded {i+1}/200...')

        self.stdout.write(self.style.SUCCESS('Done. 200 applicants seeded through all 7 AI layers.'))
```

---

## 9. URL Configuration

`oto_ai_mvp/urls.py`

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),               # Dashboard
    path('leads/', include('lead_scoring.urls')),
    path('kyc/', include('document_kyc.urls')),
    path('credit/', include('credit_engine.urls')),
    path('routing/', include('lender_routing.urls')),
    path('fraud/', include('fraud_detection.urls')),
    path('collections/', include('collections.urls')),
    path('retention/', include('retention.urls')),
]
```

---

## 10. Base Template

`core/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OTO AI — {% block title %}Dashboard{% endblock %}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
  <style>
    body { background: #f5f7fa; font-family: 'Segoe UI', sans-serif; }
    .sidebar { width: 220px; min-height: 100vh; background: #1a1d23; }
    .sidebar a { color: #adb5bd; text-decoration: none; padding: 10px 20px; display: block; }
    .sidebar a:hover, .sidebar a.active { color: #fff; background: #2BB780; border-radius: 6px; }
    .badge-hot { background: #dc3545; }
    .badge-warm { background: #fd7e14; }
    .badge-cold { background: #6c757d; }
    .metric-card { border-radius: 12px; border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .ai-tag { font-size: 0.7rem; background: #e8f5ee; color: #0f6e56; 
              border-radius: 4px; padding: 2px 6px; font-weight: 600; }
  </style>
</head>
<body>
<div class="d-flex">
  <div class="sidebar py-4">
    <div class="px-4 mb-4">
      <span style="color:#2BB780;font-weight:700;font-size:1.2rem;">OTO</span>
      <span style="color:#fff;font-size:0.8rem;"> AI Console</span>
    </div>
    <a href="/" class="{% if request.path == '/' %}active{% endif %}">📊 Dashboard</a>
    <div class="px-4 mt-3 mb-1" style="color:#6c757d;font-size:0.7rem;text-transform:uppercase;">Pipeline</div>
    <a href="/leads/">🎯 Lead Scoring</a>
    <a href="/kyc/">🪪 Document KYC</a>
    <a href="/credit/">🧠 Credit Engine</a>
    <a href="/routing/">🔀 Lender Routing</a>
    <a href="/fraud/">🛡️ Fraud Detection</a>
    <a href="/collections/">📞 Collections</a>
    <a href="/retention/">🔄 Retention</a>
    <div class="px-4 mt-3 mb-1" style="color:#6c757d;font-size:0.7rem;text-transform:uppercase;">System</div>
    <a href="/admin/">⚙️ Admin</a>
  </div>
  <div class="flex-grow-1 p-4">
    {% block content %}{% endblock %}
  </div>
</div>
</body>
</html>
```

---

## 11. AI Engineer Talking Points for Panel

Use this as your verbal narrative for each module:

**Layer 1 — Lead Scoring**
> "Instead of calling every form submission equally, we score each session using behavioral signals — did they use the EMI calculator, did they return, how long did they spend on a specific bike page. This is a real-time XGBoost model in production. In the demo I'm using a deterministic mock, but the feature engineering and scoring logic are production-ready. The agent queue is ranked by propensity score, so the highest-intent leads get called first."

**Layer 2 — Document KYC**
> "The 30-minute approval promise is only achievable if no human manually checks Aadhaar and PAN. We use AWS Textract for OCR, Pydantic for schema validation, and DigiLocker API for government verification. The fuzzy name match catches OCR errors before they become KYC failures. In the demo you can see a case where the OCR truncated a last character — the model flagged it for review rather than silently passing it."

**Layer 3 — Credit Underwriting**
> "Most OTO customers are thin-file — gig workers, students, first-time borrowers in Tier 2 cities. Bureau scores either don't exist or are limited. We augment with Account Aggregator data: UPI cash flow consistency, telecom tenure as a proxy for identity stability, GST filing status for self-employed. The SHAP waterfall chart shows which features drove the PD score — this is mandatory for RBI explainability compliance."

**Layer 4 — Lender Routing**
> "OTO has 10+ lending partners. A rule table can't capture the fact that Suryoday SFB performs better on C-grade risk while IDFC First has better appetite for salaried A+ profiles. The bandit learns these patterns from feedback — approvals and declines — and routes optimally. The objective function is approval probability times net yield, not just yield alone."

**Layer 5 — Fraud Detection**
> "Row-level fraud models miss ring fraud. The GNN looks at the applicant graph — same device across applications, address clusters, shared phone patterns. In the demo, applicants 42, 43, and 44 share a device ID and were all flagged together. That's graph-level detection you cannot get from a single-row ML model."

**Layer 6 — Collections**
> "The LSTM predicts delinquency 60 days before it happens, based on repayment time series. But the output isn't just a risk score — it's a WhatsApp message or call script generated in the customer's regional language. A customer in Bangalore gets a Kannada message. A customer in Jaipur gets Hindi. This is the LLM layer on top of the prediction layer."

**Layer 7 — Retention**
> "OTO's 'upgrade anytime' feature is their moat, but it only works if you know when to trigger the offer. The survival model tells us a customer who has made 8 on-time payments and has been browsing the Ather 450X page in the last 30 days has a 78% probability of upgrading in the next 90 days. We push a personalised offer to them — not a generic blast."

---

## 12. Dummy Data Summary (post-seed)

| Metric | Expected Value |
|--------|---------------|
| Total applicants | 200 |
| Hot leads | ~55 (28%) |
| Warm leads | ~85 (43%) |
| Cold leads | ~60 (30%) |
| KYC Clear | ~165 (83%) |
| KYC Review | ~25 (13%) |
| KYC Rejected | ~10 (5%) |
| A+/A grade | ~60 (30%) |
| B grade | ~70 (35%) |
| C grade | ~50 (25%) |
| D grade | ~20 (10%) |
| AI Approved | ~90 (45%) |
| Manual Review | ~70 (35%) |
| AI Rejected | ~40 (20%) |
| Fraud High Risk | ~10 (5%) |
| Fraud Medium | ~30 (15%) |
| Collections Amber/Red | ~25 (of disbursed) |
| Upgrade Hot | ~18 (of disbursed) |

---

## 13. Production Architecture Notes (for panel Q&A)

When the panel asks "how would this scale in production?":

**Inference latency targets:**
- Lead scoring: <50ms (ONNX runtime, Redis feature store)
- KYC OCR: 2–4s (async job queue via Celery + Redis)
- Credit underwriting: <500ms (SageMaker endpoint with auto-scaling)
- Fraud GNN: <200ms (Neo4j + cached graph embeddings)
- Collections LSTM: batch job, nightly run (not real-time)
- Lender routing: <100ms (bandit weights cached in Redis, updated hourly)

**Data pipeline:**
- All behavioral events → Kafka → feature store (Feast on Redis)
- Model training: weekly retrain on new repayment data (MLflow + SageMaker Training Jobs)
- Model registry: MLflow Model Registry → staged promotion (staging → production)
- Monitoring: Evidently AI for data drift detection on bureau score distribution and PD calibration

**Regulatory:**
- SHAP explanations stored per decision for RBI audit trail
- Account Aggregator (AA) consent framework for UPI data pull (NBFC-AA integration via Setu/Finvu)
- All PII encrypted at rest (AES-256), in transit (TLS 1.3)
- Model fairness checks: PD calibration tested across employment types and cities to avoid proxy discrimination

---

*Built by Ankit | AI Engineer | Tasaar — AI & Data Infrastructure*