# Generated by Django 4.0.6 on 2022-09-12 11:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ggdb', '0005_fs_fs_corp_id_46c8fb_idx'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='fs',
            name='cs_test',
        ),
    ]
