# Generated by Django 4.2 on 2023-06-05 00:47

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0012_rename_produk_item_produkreview_produk_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='produkreview',
            options={'ordering': ('publish',)},
        ),
        migrations.AddField(
            model_name='produkreview',
            name='name',
            field=models.CharField(default='Anonymous', max_length=50),
        ),
        migrations.AddField(
            model_name='produkreview',
            name='publish',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AddField(
            model_name='produkreview',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='produkreview',
            name='produk',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Comments', to='toko.produkitem'),
        ),
    ]
