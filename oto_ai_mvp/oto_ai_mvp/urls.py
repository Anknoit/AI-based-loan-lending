from django.contrib import admin
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import path, include


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', logout_view, name='logout'),  # override before auth.urls
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    path('leads/', include('lead_scoring.urls')),
    path('kyc/', include('document_kyc.urls')),
    path('credit/', include('credit_engine.urls')),
    path('routing/', include('lender_routing.urls')),
    path('fraud/', include('fraud_detection.urls')),
    path('collections/', include('loan_collections.urls')),
    path('retention/', include('retention.urls')),
]
