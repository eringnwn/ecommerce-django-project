# Generated by Django 4.2 on 2023-06-07 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0025_merge_20230607_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produkitem',
            name='harga',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='produkitem',
            name='harga_diskon',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
