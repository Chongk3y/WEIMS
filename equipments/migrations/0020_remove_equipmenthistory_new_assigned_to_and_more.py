# Generated by Django 5.2.3 on 2025-07-03 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipments', '0019_equipmentactionlog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipmenthistory',
            name='new_assigned_to',
        ),
        migrations.RemoveField(
            model_name='equipmenthistory',
            name='new_end_user',
        ),
        migrations.RemoveField(
            model_name='equipmenthistory',
            name='previous_assigned_to',
        ),
        migrations.RemoveField(
            model_name='equipmenthistory',
            name='previous_end_user',
        ),
        migrations.AddField(
            model_name='equipmenthistory',
            name='action',
            field=models.CharField(default='Edited', max_length=50),
        ),
        migrations.AddField(
            model_name='equipmenthistory',
            name='field_changed',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='equipmenthistory',
            name='new_value',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='equipmenthistory',
            name='old_value',
            field=models.TextField(blank=True, null=True),
        ),
    ]
