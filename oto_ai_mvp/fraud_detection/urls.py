from django.urls import path
from . import views

urlpatterns = [
    path('', views.fraud_list, name='fraud_list'),
    path('<int:pk>/', views.fraud_detail, name='fraud_detail'),
]
