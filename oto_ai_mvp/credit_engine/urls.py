from django.urls import path
from . import views

urlpatterns = [
    path('', views.credit_list, name='credit_list'),
    path('<int:pk>/', views.credit_detail, name='credit_detail'),
]
