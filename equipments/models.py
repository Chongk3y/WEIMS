from django.db import models
from datetime import datetime
import os
import random
from django.contrib.auth.models import User
from django.utils.html import mark_safe
from django.conf import settings
from django.utils import timezone
from django import forms

now = datetime.now

def image_path(instance, filename):
    basefilename, file_extension = os.path.splitext(filename)
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    randomstring = ''.join((random.choice(chars)) for x in range(10))
    now = datetime.now()
    return 'equipment_pic/{year}-{month}-{imageid}-{basename}{randomstring}{ext}'.format(
        imageid=instance,
        basename=basefilename,
        randomstring=randomstring,
        ext=file_extension,
        year=now.strftime('%Y'),
        month=now.strftime('%m'),
        day=now.strftime('%d')
    )

class Status(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Status Name")

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statuses"

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Category Name")

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Equipment(models.Model):
    user_image = models.ImageField(
        upload_to=image_path,
        default='equipment_pic/default.jpg',
        verbose_name="Equipment Image"
    )

    item_propertynum = models.CharField(max_length=50, blank=True, null=True, verbose_name="Property Number")
    item_name = models.CharField(max_length=50, verbose_name="Item Name")
    item_desc = models.CharField(max_length=50, blank=True, null=True, verbose_name="Item Description")
    additional_info = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Additional Info")

    item_purdate = models.DateField(blank=True, null=True, verbose_name="Purchase Date")
    po_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="PO Number")
    fund_source = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fund Source")
    supplier = models.CharField(max_length=100, blank=True, null=True, verbose_name="Supplier")

    item_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")

    project_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Project Name")
    assigned_to = models.CharField(max_length=100, blank=True, null=True, verbose_name="Assigned To")
    end_user = models.CharField(max_length=100, blank=True, null=True, verbose_name="End User")

    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Location")
    current_location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Current Location")

    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category", default=1)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, verbose_name="Status", default=1)

    emp = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Employee")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='equipment_created',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Created By"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='equipment_updated',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Updated By"
    )
    order_receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    return_document = models.FileField(upload_to='return_docs/', null=True, blank=True, verbose_name="Return Document")
    return_remarks = models.TextField(blank=True, null=True, verbose_name="Return Remarks")
    return_condition = models.CharField(max_length=50, blank=True, null=True, verbose_name="Condition Upon Return")
    return_type = models.CharField(max_length=30, blank=True, null=True, verbose_name="Return Type")
    returned_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Returned By")
    received_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Received By")
    is_archived = models.BooleanField(default=False)
    date_archived = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name='archived_equipments',
        on_delete=models.SET_NULL
    )

    class Meta: 
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment Records"

    def __str__(self):
        return self.item_name
    
    def image_tag(self):
        return mark_safe('<img src="/equipments/media/%s" width="50" height="50" />' % self.user_image)   
    
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = '__all__'  # Or explicitly list your fields
    def image_tag(self):
        return mark_safe('<img src="/equipments/media/%s" width="50" height="50" />' % self.user_image)   

class EquipmentHistory(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='history')
    field_changed = models.CharField(max_length=255)  # e.g. 'assigned_to', 'item_name', etc.
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=50, default='Edited')  # e.g. 'Edited', 'Reassigned', etc.
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} {self.field_changed} from {self.old_value} to {self.new_value}"

class EquipmentActionLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('archive', 'Archived'),
        ('unarchive', 'Unarchived'),
        # Add more as needed
    ]
    equipment = models.ForeignKey('Equipment', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class ReportTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    columns = models.JSONField()
    filters = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
