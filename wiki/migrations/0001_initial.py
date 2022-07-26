# Generated by Django 4.0.6 on 2022-07-23 21:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(blank=True, choices=[('00', 'Economics / Finance / Investment'), ('01', 'Econometrics / Statistics'), ('02', 'Computer Engineering / Data Science'), ('99', 'etc')], max_length=2, null=True)),
                ('fieldname', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Headword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('is_published', models.BooleanField(default=False)),
                ('is_banned', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_draft', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('cancelled_why', models.CharField(blank=True, max_length=2, null=True)),
                ('cancelled_why_detail', models.TextField(blank=True, null=True)),
                ('abstract', models.TextField()),
                ('definition', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='wiki.article')),
                ('cancelled_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cancel', to=settings.AUTH_USER_MODEL)),
                ('editor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='update', to=settings.AUTH_USER_MODEL)),
                ('keywords', models.ManyToManyField(blank=True, related_name='tagged_by', to='wiki.headword')),
            ],
            options={
                'get_latest_by': 'updated_at',
            },
        ),
        migrations.AddField(
            model_name='article',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article', to='wiki.headword'),
        ),
        migrations.AddConstraint(
            model_name='article',
            constraint=models.UniqueConstraint(fields=('title', 'fieldname'), name='unique article'),
        ),
    ]