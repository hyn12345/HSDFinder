# Generated by Django 2.2.9 on 2020-10-10 00:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0003_genes_species_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kegg',
            name='species',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='database.Files'),
        ),
    ]
