from django import forms
from .models import Equipment, Status, Category
from django.contrib.auth.models import User

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'item_name', 'item_desc', 'item_propertynum', 'additional_info',
            'item_purdate', 'po_number', 'fund_source', 'supplier',
            'item_amount', 'project_name', 'assigned_to', 'end_user',
            'location', 'current_location', 'category', 'status', 'emp',
            'created_by', 'updated_by', 'order_receipt', 'is_returned',
            'return_document', 'return_remarks', 'return_condition',
            'return_type', 'returned_by', 'received_by', 'is_archived',
            'date_archived', 'archived_by', 'user_image'
        ]

class ReportFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    status = forms.ModelChoiceField(queryset=Status.objects.all(), required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    assigned_to = forms.CharField(max_length=100, required=False, label='Assigned To')
    
    COLUMN_CHOICES = [
        ('General', [
            ('item_name', 'Item Name'),
            ('item_propertynum', 'Property Number'),
            ('item_desc', 'Item Description'),
            ('additional_info', 'Additional Info'),
            ('user_image', 'Equipment Image'),
        ]),
        ('Assignment', [
            ('assigned_to', 'Assigned To'),
            ('end_user', 'End User'),
            ('emp', 'Employee'),
            ('location', 'Location'),
            ('current_location', 'Current Location'),
            ('project_name', 'Project Name'),
        ]),
        ('Financial', [
            ('item_purdate', 'Purchase Date'),
            ('po_number', 'PO Number'),
            ('fund_source', 'Fund Source'),
            ('supplier', 'Supplier'),
            ('item_amount', 'Amount'),
        ]),
        ('Status', [
            ('category', 'Category'),
            ('status', 'Status'),
            ('created_by', 'Created By'),
            ('updated_by', 'Updated By'),
            ('created_at', 'Created At'),
            ('updated_at', 'Updated At'),
        ]),
        ('Return', [
            ('is_returned', 'Is Returned'),
            ('return_document', 'Return Document'),
            ('return_remarks', 'Return Remarks'),
            ('return_condition', 'Condition Upon Return'),
            ('return_type', 'Return Type'),
            ('returned_by', 'Returned By'),
            ('received_by', 'Received By'),
        ]),
        ('Archive', [
            ('is_archived', 'Is Archived'),
            ('date_archived', 'Date Archived'),
            ('archived_by', 'Archived By'),
        ]),
        ('Other', [
            ('order_receipt', 'Order Receipt'),
        ]),
    ]
    columns = forms.MultipleChoiceField(
        choices=COLUMN_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        initial=['item_name', 'category', 'status', 'assigned_to', 'created_at']
    )
    # Add more filters as needed