# Generated by Django 3.1.7 on 2022-03-06 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20220305_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialmediavariation',
            name='share_type',
            field=models.CharField(choices=[('username', 'Username'), ('telephone #', 'Telephone'), ('url', 'Url'), ('email', 'Email')], default='username', max_length=20),
        ),
        migrations.AlterField(
            model_name='socialmediavariation',
            name='share_type_display',
            field=models.CharField(choices=[('username', 'Username'), ('telephone #', 'Telephone'), ('url', 'Url'), ('email', 'Email'), ('username or telephone', 'Username or Telephone')], default='username', max_length=40),
        ),
    ]
