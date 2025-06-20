from django.urls import path
from . import views

app_name = 'astroapp'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about, name='about'),
    path('save_event/<int:event_id>/', views.save_event, name='save_event'),
    path('remove_event/<int:event_id>/', views.remove_event, name='remove_event'),
] 