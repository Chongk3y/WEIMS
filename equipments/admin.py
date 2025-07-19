from django.contrib import admin
from .models import Category, Status, Equipment, ReturnDocument

admin.site.site_header = "WEIMS Admin" 
admin.site.site_title = "WEIMS Admin Portal"

class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'image_tag','item_propertynum', 'item_name', 'item_desc', 'item_purdate', 'po_number',
        'fund_source', 'supplier', 'item_amount', 'assigned_to', 'location',
        'end_user', 'emp', 'category', 'status', 'created_at', 'updated_at'
    )
    search_fields = ('item_name', 'supplier')
    list_filter = ('status', 'category')

class ReturnDocumentAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'original_filename', 'uploaded_at', 'uploaded_by')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('equipment__item_name', 'original_filename')

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Category) 
admin.site.register(Status) 
admin.site.register(ReturnDocument, ReturnDocumentAdmin) 
