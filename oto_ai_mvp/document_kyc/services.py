import random
from difflib import SequenceMatcher


def mock_ocr_extract(applicant) -> dict:
    """Simulates AWS Textract field extraction from Aadhaar + PAN."""
    random.seed(applicant.id * 13)
    name = applicant.name
    if random.random() < 0.15:
        name = name[:-1]
    return {
        'name_extracted': name,
        'aadhaar': f"{random.randint(2000, 9999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
        'pan': f"{'ABCDE'[applicant.id % 5]}{'FGHIJ'[applicant.id % 5]}PL{random.randint(1000, 9999)}K",
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
