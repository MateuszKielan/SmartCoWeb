from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('convert/', views.convert_screen_view, name='convert_screen'),
]