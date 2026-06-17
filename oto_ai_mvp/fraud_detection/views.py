from django.contrib.auth.decorators import login_required
import json
from django.shortcuts import render, get_object_or_404
from .models import FraudAssessment


@login_required
def fraud_list(request):
    assessments = FraudAssessment.objects.select_related('applicant').order_by('-fraud_risk_score')

    high = FraudAssessment.objects.filter(fraud_risk_label='high').count()
    medium = FraudAssessment.objects.filter(fraud_risk_label='medium').count()
    low = FraudAssessment.objects.filter(fraud_risk_label='low').count()

    # Fraud ring: shared device DEV-0294
    ring_cases = FraudAssessment.objects.filter(
        device_id='DEV-0294').select_related('applicant')

    flagged = assessments.filter(fraud_risk_label__in=['high', 'medium'])

    context = {
        'assessments': flagged[:50],
        'high': high, 'medium': medium, 'low': low,
        'ring_cases': ring_cases,
        'pie_data': json.dumps({'high': high, 'medium': medium, 'low': low}),
    }
    return render(request, 'fraud_detection/fraud_list.html', context)


@login_required
def fraud_detail(request, pk):
    assessment = get_object_or_404(
        FraudAssessment.objects.select_related('applicant'), applicant_id=pk)
    applicant = assessment.applicant

    # Other applicants sharing same device
    shared_device = FraudAssessment.objects.filter(
        device_id=assessment.device_id).exclude(applicant_id=pk).select_related('applicant')

    flags = [
        ('Device Reuse', assessment.device_reuse_count > 1,
         f"{assessment.device_reuse_count} applications from {assessment.device_id}"),
        ('IP Reuse', assessment.ip_reuse_count > 1,
         f"IP {assessment.ip_address} used {assessment.ip_reuse_count}×"),
        ('Velocity Flag', assessment.velocity_flag,
         ">3 applications from device in 30 days"),
        ('Synthetic ID', assessment.synthetic_id_flag,
         "Name/DOB mismatch pattern detected"),
        ('Address Cluster', assessment.address_cluster_size > 1,
         f"{assessment.address_cluster_size} applicants at same pincode pattern"),
    ]

    context = {
        'assessment': assessment,
        'applicant': applicant,
        'shared_device': shared_device,
        'flags': flags,
        'score_pct': round(assessment.fraud_risk_score * 100, 1),
    }
    return render(request, 'fraud_detection/fraud_detail.html', context)




# Nodes:  Applicants, Devices, Phone numbers, IP addresses, Addresses
# Edges:  applicant→device (used), applicant→phone, applicant→IP,
#         applicant→address (lives at)
# import torch
# from torch_geometric.nn import SAGEConv

# class FraudGNN(torch.nn.Module):
#     def __init__(self, in_channels, hidden, out_channels):
#         super().__init__()
#         self.conv1 = SAGEConv(in_channels, hidden)
#         self.conv2 = SAGEConv(hidden, out_channels)

#     def forward(self, x, edge_index):
#         x = self.conv1(x, edge_index).relu()
#         x = self.conv2(x, edge_index)
#         return torch.sigmoid(x)   # fraud probability per node