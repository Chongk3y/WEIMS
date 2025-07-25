# Generated by Django 5.2.3 on 2025-06-13 03:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipments', '0002_category_remove_equipment_cat_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Status Name')),
            ],
            options={
                'verbose_name': 'Status',
            },
        ),
        migrations.RemoveField(
            model_name='equipment',
            name='status_id',
        ),
        migrations.AddField(
            model_name='equipment',
            name='status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='equipments.status', verbose_name='Status'),
        ),
    ]
