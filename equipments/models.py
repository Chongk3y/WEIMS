from django.db import models
from datetime import datetime
import os
import random
from django.contrib.auth.models import User
from django.utils.html import mark_safe


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
    user_image = models.ImageField(upload_to=image_path, default='equipment_pic/default.jpg', verbose_name="Equipment Image")
    item_propertynum = models.CharField(max_length=50, verbose_name="Property Number")
    item_name = models.CharField(max_length=50, verbose_name="Item Name")
    item_desc = models.CharField(max_length=50, verbose_name="Item Description")
    item_purdate = models.DateField(verbose_name="Purchase Date")
    po_number = models.CharField(max_length=50, verbose_name="PO Number")
    fund_source = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fund Source")
    supplier = models.CharField(max_length=100, verbose_name="Supplier")
    item_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")
    assigned_to = models.CharField(max_length=100, verbose_name="Assigned To")
    location = models.CharField(max_length=100, verbose_name="Location")
    end_user = models.CharField(max_length=100, verbose_name="End User")
    emp = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False, verbose_name="Employee")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Category", default=1)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, verbose_name="Status", default=1)
    created_at = models.DateField(default=now, verbose_name="Created")
    updated_at = models.DateField(default=now, verbose_name="Updated")  

    class Meta: 
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment Records"

    def __str__(self):
        return self.item_name
    
    def image_tag(self):
        return mark_safe('<img src="/equipments/media/%s" width="50" height="50" />' % self.user_image)   
    
    
    



    
     