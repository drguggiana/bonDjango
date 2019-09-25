# Generated by Django 2.1.3 on 2019-07-02 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loggers', '0002_intrinsicimaging_mappath'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mouseset',
            name='id',
        ),
        migrations.AddField(
            model_name='mouseset',
            name='mouse_set_name',
            field=models.CharField(default='N/A', max_length=200, primary_key=True, serialize=False),
        ),
    ]
