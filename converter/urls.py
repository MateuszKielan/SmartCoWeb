from django.urls import path
from . import views
from .views import convert_to_nquads_view

urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('convert/', views.convert_screen_view, name='convert_screen'),
    path('convert/nquads/', convert_to_nquads_view, name='convert_nquads')
]