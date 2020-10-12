# Generated by Django 3.1.2 on 2020-10-08 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('chat', models.IntegerField()),
                ('key', models.CharField(max_length=200)),
                ('val', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('key', models.CharField(max_length=200)),
                ('val', models.CharField(max_length=200)),
            ],
        ),
    ]