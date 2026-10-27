from django.urls import path
from . import views

app_name = 'crops'

urlpatterns = [
    path('', views.crop_list_page, name='crop_list'),
    path('<int:pk>/', views.crop_detail, name='crop_detail'),
    path('ajax/get/<int:pk>/', views.crop_get_ajax, name='crop_get_ajax'),
    path('ajax/save/', views.crop_save_ajax, name='crop_save_ajax'),
    path('ajax/delete/<int:pk>/', views.crop_delete_ajax, name='crop_delete_ajax'),
    path('logs/', views.activity_logs_page, name='activity_logs'),
    path('logs/add/', views.activity_log_save_ajax, name='activity_log_save_ajax'),
    path('<int:crop_id>/logs/add/', views.log_save_ajax, name='log_save_ajax'),
    path('logs/delete/<int:pk>/', views.log_delete_ajax, name='log_delete_ajax'),
    path('<int:crop_id>/diagnosis/add/', views.diagnosis_save_ajax, name='diagnosis_save_ajax'),
    path('diagnosis/delete/<int:pk>/', views.diagnosis_delete_ajax, name='diagnosis_delete_ajax'),
    path('<int:crop_id>/ai-diagnose/', views.generate_ai_diagnosis, name='generate_ai_diagnosis'),
]

