# Generated by Django 4.2 on 2023-06-05 00:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('toko', '0013_alter_produkreview_options_produkreview_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='produkreview',
            old_name='name',
            new_name='nama',
        ),
    ]
