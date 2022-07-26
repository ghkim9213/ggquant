# Generated by Django 4.0.6 on 2022-10-05 18:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0015_delete_faproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='FaProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('div', models.CharField(choices=[('VALUE', '값'), ('RATIO', '비율')], max_length=5)),
                ('nm', models.CharField(max_length=256)),
                ('lk', models.CharField(max_length=256)),
                ('oc', models.CharField(max_length=3)),
                ('syntax', models.TextField()),
                ('item', models.ManyToManyField(to='dashboard.faitem')),
                ('item_self', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='dashboard.faproduct')),
            ],
            options={
                'db_table': 'fa_product',
            },
        ),
    ]
