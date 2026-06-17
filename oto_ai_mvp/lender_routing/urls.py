from django.urls import path
from . import views

urlpatterns = [
    path('', views.routing_list, name='routing_list'),
    path('<int:pk>/', views.routing_detail, name='routing_detail'),
]
