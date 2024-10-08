# Generated by Django 5.1.1 on 2024-09-14 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_oauthtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='oauthtoken',
            name='access_token',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='client_id',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='client_secret',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='expires_at',
            field=models.DateTimeField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='refreshh_token',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='scope',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='token_uri',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='universe_domain',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='oauthtoken',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
