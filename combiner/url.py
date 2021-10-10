from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='Combiner'),
    path('submit/', views.submit, name='Submit'),
]