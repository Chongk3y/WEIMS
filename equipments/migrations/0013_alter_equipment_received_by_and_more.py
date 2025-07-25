# Generated by Django 5.2.3 on 2025-07-02 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipments', '0012_equipment_returned_by_alter_equipment_received_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='received_by',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Received By'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='returned_by',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Returned By'),
        ),
    ]
