from django.contrib import admin
from .models import Category, Status, Equipment

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

admin.site.register(Equipment, EquipmentAdmin)
admin.site.register(Category) 
admin.site.register(Status) 
