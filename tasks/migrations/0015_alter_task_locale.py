# Generated by Django 5.1.1 on 2024-09-19 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_task_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='locale',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
