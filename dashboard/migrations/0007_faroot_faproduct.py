# Generated by Django 4.0.6 on 2022-10-04 12:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ggdb', '0013_fsdetail_allowmatch'),
        ('dashboard', '0006_facrosssection'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaRoot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fa', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ggdb.fsaccount')),
                ('nstdVal', models.ManyToManyField(related_name='faroot_nstd', to='ggdb.fsdetail')),
                ('stdVal', models.ManyToManyField(related_name='faroot_std', to='ggdb.fsdetail')),
            ],
            options={
                'db_table': 'fa_root',
            },
        ),
        migrations.CreateModel(
            name='FaProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('lk', models.CharField(max_length=256)),
                ('oc', models.CharField(max_length=3)),
                ('root', models.ManyToManyField(to='dashboard.faroot')),
            ],
            options={
                'db_table': 'fa_value',
            },
        ),
    ]
