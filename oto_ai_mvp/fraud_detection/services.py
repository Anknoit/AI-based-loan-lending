import random


def compute_fraud_score(applicant) -> dict:
    random.seed(applicant.id * 67)
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
        'ip_address': f"103.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
    }
