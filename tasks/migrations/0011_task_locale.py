# Generated by Django 5.1.1 on 2024-09-15 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_task_appellant_alter_task_full_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='locale',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
