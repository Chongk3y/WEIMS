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
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('categories/', views.category_list, name='category'),
    path('categories/edit/<int:id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:id>/', views.delete_category, name='delete_category'),
    path('statuses/', views.status_list, name='status'),
    path('statuses/add/', views.add_status, name='add_status'),
    path('statuses/edit/<int:id>/', views.edit_status, name='edit_status'),
    path('statuses/delete/<int:id>/', views.delete_status, name='delete_status'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('import-excel/', views.import_excel, name='import_excel'),
    path('equipment/<int:pk>/json/', views.equipment_detail_json, name='equipment_detail_json'),
    path('equipment/table/json/', views.equipment_table_json, name='equipment_table_json'),
    path('bulk-update/', views.bulk_update_equipment, name='bulk_update'),
    path('returned/', views.returned, name='returned'),
    path('return-equipment/', views.return_equipment, name='return_equipment'),
    path('returned/json/', views.returned_equipment_table_json, name='returned_equipment_table_json'),
    path('archive/<int:pk>/', views.archive_equipment, name='archive_equipment'),
    path('archived/', views.archived_equipments, name='archived_equipments'),
    path('archived/json/', views.archived_equipment_table_json, name='archived_equipment_table_json'),
    path('unarchive/<int:pk>/', views.unarchive_equipment, name='unarchive_equipment'),
    path('<int:equipment_id>/history/', views.equipment_history_json, name='equipment_history_json'),
    path('history-logs/', views.history_logs, name='history_logs'),
    path('history/clear/', views.clear_history_logs, name='clear_history_logs'),




    
] + static(settings.MEDIA_URL, 
    document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, 
    document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)