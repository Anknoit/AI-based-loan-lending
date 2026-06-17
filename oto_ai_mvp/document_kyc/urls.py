from django.urls import path
from . import views

urlpatterns = [
    path('', views.kyc_list, name='kyc_list'),
    path('<int:pk>/', views.kyc_detail, name='kyc_detail'),
]
