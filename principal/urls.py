# principal/urls.py
from django.urls import path
from . import views

app_name = 'principal'  # opcional, pero recomendable
urlpatterns = [
    path('', views.home, name='home'),
]
