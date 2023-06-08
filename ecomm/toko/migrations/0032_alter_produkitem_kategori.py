# Generated by Django 4.2 on 2023-06-08 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0031_alter_produkitem_kategori'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produkitem',
            name='kategori',
            field=models.CharField(choices=[('PC', 'Pakaian'), ('SC', 'Sepatu'), ('TC', 'Tas'), ('AC', 'Aksesoris')], max_length=20),
        ),
    ]
