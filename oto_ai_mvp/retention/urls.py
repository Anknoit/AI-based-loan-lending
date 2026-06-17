from django.urls import path
from . import views

urlpatterns = [
    path('', views.retention_list, name='retention_list'),
    path('<int:pk>/', views.retention_detail, name='retention_detail'),
]
