from django.urls import path
from django.conf import settings
from . import views
from django.conf.urls.static import static

app_name = 'equipments'
urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_equipment, name='add'),
    path('processaddequipment/', views.processaddequipment, name='processaddequipment'),
    path('edit/<int:id>/', views.edit_equipment, name='edit'),
    path('delete/<int:id>/', views.delete_equipment, name='delete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user/', views.user, name='user'),
    path('users/add/', views.add_user, name='add_user'),
    path('categories/', views.category_list, name='category'),
    path('categories/edit/<int:id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:id>/', views.delete_category, name='delete_category'),
    path('statuses/', views.status_list, name='status'),
    path('statuses/add/', views.add_status, name='add_status'),
    path('statuses/edit/<int:id>/', views.edit_status, name='edit_status'),
    path('statuses/delete/<int:id>/', views.delete_status, name='delete_status'),
    path('export/csv/', views.export_csv, name='export_csv'),

    
] + static(settings.MEDIA_URL, 
    document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, 
    document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)