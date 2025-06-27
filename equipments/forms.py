from django import forms
from .models import Equipment

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'description']  # Add other fields as needed