from django.urls import path
from . import views

urlpatterns = [
    path('', views.collections_list, name='collections_list'),
    path('<int:pk>/', views.collections_detail, name='collections_detail'),
]
