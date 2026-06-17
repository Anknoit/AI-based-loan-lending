from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg
from .models import LenderRoute, LENDER_CHOICES
from .services import route_applicant, LENDER_PROFILES
from credit_engine.models import CreditAssessment


LENDER_DISPLAY = dict(LENDER_CHOICES)


@login_required
def routing_list(request):
    routes = LenderRoute.objects.select_related('applicant').order_by('-routed_at')

    # Lender allocation counts
    lender_counts = {}
    for lender, label in LENDER_CHOICES:
        count = LenderRoute.objects.filter(selected_lender=lender).count()
        approved = LenderRoute.objects.filter(selected_lender=lender, lender_response='approved').count()
        lender_counts[label] = {
            'count': count,
            'approved': approved,
            'rate': round(approved / count * 100, 1) if count else 0,
            'yield': LENDER_PROFILES.get(lender, {}).get('yield', 0),
        }

    # Yield comparison for chart
    yield_chart = {
        'labels': [v for _, v in LENDER_CHOICES],
        'yields': [LENDER_PROFILES[k]['yield'] for k, _ in LENDER_CHOICES],
    }

    context = {
        'routes': routes[:50],
        'lender_counts': lender_counts,
        'yield_chart': json.dumps(yield_chart),
    }
    return render(request, 'lender_routing/routing_list.html', context)


@login_required
def routing_detail(request, pk):
    route = get_object_or_404(LenderRoute.objects.select_related('applicant'), applicant_id=pk)
    applicant = route.applicant

    try:
        assessment = CreditAssessment.objects.get(applicant=applicant)
        risk_grade = assessment.risk_grade
    except CreditAssessment.DoesNotExist:
        risk_grade = 'B'

    # Recompute all lender scores for display
    from .services import route_applicant
    result = route_applicant(applicant, risk_grade)
    all_scores = result['all_scores']
    ranked = sorted(all_scores.items(), key=lambda x: x[1]['objective'], reverse=True)

    ranked_display = [
        {
            'lender': LENDER_DISPLAY.get(k, k),
            'key': k,
            'p': v['p'],
            'yield': v['yield'],
            'objective': v['objective'],
            'is_selected': k == route.selected_lender,
            'is_fallback': k == route.fallback_lender,
        }
        for k, v in ranked
    ]

    context = {
        'route': route,
        'applicant': applicant,
        'risk_grade': risk_grade,
        'ranked_display': ranked_display,
    }
    return render(request, 'lender_routing/routing_detail.html', context)


# import numpy as np

# class ThompsonSamplingRouter:
#     def __init__(self, lenders, grades):
#         # Alpha (approvals+1) and Beta (declines+1) per lender×grade
#         self.alpha = {(l, g): 1 for l in lenders for g in grades}
#         self.beta  = {(l, g): 1 for l in lenders for g in grades}

#     def route(self, risk_grade: str) -> str:
#         samples = {}
#         for lender in LENDERS:
#             a = self.alpha[(lender, risk_grade)]
#             b = self.beta[(lender, risk_grade)]
#             samples[lender] = np.random.beta(a, b)
#         return max(samples, key=samples.get)

#     def update(self, lender: str, grade: str, approved: bool):
#         if approved:
#             self.alpha[(lender, grade)] += 1
#         else:
#             self.beta[(lender, grade)] += 1

#in  production each callback will be serialized to redis and updated