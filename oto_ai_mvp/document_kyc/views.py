from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import KYCRecord


@login_required
def kyc_list(request):
    status_filter = request.GET.get('status', '')
    records = KYCRecord.objects.select_related('applicant').order_by('-processed_at')
    if status_filter:
        records = records.filter(kyc_status=status_filter)

    clear = KYCRecord.objects.filter(kyc_status='clear').count()
    review = KYCRecord.objects.filter(kyc_status='review').count()
    rejected = KYCRecord.objects.filter(kyc_status='rejected').count()

    context = {
        'records': records,
        'status_filter': status_filter,
        'clear': clear, 'review': review, 'rejected': rejected,
    }
    return render(request, 'document_kyc/kyc_list.html', context)


@login_required
def kyc_detail(request, pk):
    record = get_object_or_404(KYCRecord.objects.select_related('applicant'), applicant_id=pk)
    applicant = record.applicant

    bureau_pct = 0
    if record.bureau_score:
        bureau_pct = round((record.bureau_score - 300) / 600 * 100, 1)

    context = {
        'record': record,
        'applicant': applicant,
        'bureau_pct': bureau_pct,
    }
    return render(request, 'document_kyc/kyc_detail.html', context)
