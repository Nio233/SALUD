from django.urls import path
from . import views

app_name = "principal"

urlpatterns = [
    path('', views.home, name='home'),
    path('probar-dataset/', views.probar_dataset, name='probar_dataset'),
    path('dataset/', views.subir_dataset, name='subir_dataset'),
    path('prediccion/', views.prediccion, name='prediccion'),
    path('consejos/', views.consejos, name='consejos'),
    path('contacto/', views.contacto, name='contacto'),
]
