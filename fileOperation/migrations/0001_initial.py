# Generated by Django 2.2.9 on 2020-08-20 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KO',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category1', models.TextField()),
                ('category2', models.TextField()),
                ('ko_number', models.CharField(max_length=50)),
                ('description', models.TextField()),
            ],
        ),
    ]
