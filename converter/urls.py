from django.urls import path
from . import views
from .views import convert_to_nquads_view

urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('convert/', views.convert_screen_view, name='convert_screen'),
    path('convert/nquads/', convert_to_nquads_view, name='convert_nquads'),
    path('replace_all/', views.replace_all, name='replace_all'),
    path('request_type/<str:request_type>', views.set_request_type, name='set_request_type')
]
