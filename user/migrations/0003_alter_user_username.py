# Generated by Django 4.0.6 on 2022-08-22 10:42

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0002_alter_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(default=uuid.UUID('d012bd12-f43e-43c0-8bb9-ceac8d53e128'), max_length=128, unique=True),
        ),
    ]