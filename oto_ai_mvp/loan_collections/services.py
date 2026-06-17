import random

COLLECTIONS_MESSAGES = {
    'green': {
        'en': "Hi {name}, your EMI of ₹{emi} is due on {date}. Pay via UPI: otocapital@ybl. Thank you!",
        'hi': "नमस्ते {name}, आपकी EMI ₹{emi} {date} को देय है। UPI से भुगतान करें: otocapital@ybl।",
        'kn': "ಹಲೋ {name}, ನಿಮ್ಮ EMI ₹{emi} {date} ರಂದು ಬರಬೇಕು. UPI ಮೂಲಕ ಪಾವತಿಸಿ: otocapital@ybl.",
        'ta': "வணக்கம் {name}, உங்கள் ₹{emi} EMI {date} அன்று செலுத்த வேண்டும். UPI வழியாக செலுத்துங்கள்: otocapital@ybl. நன்றி!",
        'te': "హలో {name}, మీ ₹{emi} EMI {date} న చెల్లించాలి. UPI ద్వారా చెల్లించండి: otocapital@ybl. ధన్యవాదాలు!",
    },
    'amber': {
        'en': "Hi {name}, we noticed your EMI of ₹{emi} hasn't been received. Please pay within 3 days to avoid late fees. Need help? Call 1800-XXX-XXXX.",
        'hi': "नमस्ते {name}, आपकी ₹{emi} की EMI अभी तक प्राप्त नहीं हुई। देर से बचने के लिए 3 दिन में भुगतान करें।",
        'kn': "ಹಲೋ {name}, ನಿಮ್ಮ ₹{emi} EMI ಇನ್ನೂ ಸ್ವೀಕರಿಸಿಲ್ಲ. ತಡ ಶುಲ್ಕ ತಪ್ಪಿಸಲು 3 ದಿನಗಳಲ್ಲಿ ಪಾವತಿಸಿ. ಸಹಾಯಕ್ಕೆ: 1800-XXX-XXXX.",
        'ta': "வணக்கம் {name}, உங்கள் ₹{emi} EMI இன்னும் பெறப்படவில்லை. தாமதக் கட்டணத்தை தவிர்க்க 3 நாட்களுக்குள் செலுத்துங்கள். உதவிக்கு அழைக்கவும்: 1800-XXX-XXXX.",
        'te': "హలో {name}, మీ ₹{emi} EMI ఇంకా అందలేదు. ఆలస్య రుసుమును నివారించడానికి 3 రోజుల్లోపు చెల్లించండి. సహాయానికి: 1800-XXX-XXXX.",
    },
    'red': {
        'en': "Dear {name}, your account has {dpd} days past due. Immediate payment of ₹{emi} is required. Our agent will contact you shortly.",
        'hi': "प्रिय {name}, आपका खाता {dpd} दिन बकाया है। तुरंत ₹{emi} का भुगतान करें।",
        'kn': "ಪ್ರಿಯ {name}, ನಿಮ್ಮ ಖಾತೆ {dpd} ದಿನಗಳ ಬಾಕಿ ಇದೆ. ತಕ್ಷಣ ₹{emi} ಪಾವತಿಸಿ. ನಮ್ಮ ಏಜೆಂಟ್ ಶೀಘ್ರದಲ್ಲಿ ಸಂಪರ್ಕಿಸುತ್ತಾರೆ.",
        'ta': "அன்புள்ள {name}, உங்கள் கணக்கு {dpd} நாட்கள் நிலுவையில் உள்ளது. உடனடியாக ₹{emi} செலுத்துங்கள். எங்கள் முகவர் விரைவில் தொடர்பு கொள்வார்.",
        'te': "ప్రియమైన {name}, మీ ఖాతా {dpd} రోజులు బకాయి ఉంది. వెంటనే ₹{emi} చెల్లించండి. మా ఏజెంట్ త్వరలో సంప్రదిస్తారు.",
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

    if dpd_30 < 0.20:
        bucket = 'green'
    elif dpd_30 < 0.50:
        bucket = 'amber'
    else:
        bucket = 'red'

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
        'dpd_30_prob': dpd_30,
        'dpd_60_prob': dpd_60,
        'dpd_90_prob': dpd_90,
        'risk_bucket': bucket,
        'recommended_channel': 'WhatsApp' if bucket == 'green' else 'Call',
        'generated_message': message,
        'language': lang,
    }
