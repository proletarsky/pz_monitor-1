# Generated by Django 3.0 on 2020-11-18 06:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Наименование')),
            ],
        ),
        migrations.CreateModel(
            name='Connection_data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='Дата/Время')),
                ('ip', models.CharField(max_length=20, verbose_name='IP адрес')),
                ('active_status', models.BooleanField(verbose_name='Текущий статус')),
            ],
        ),
        migrations.CreateModel(
            name='Object_list',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.CharField(max_length=20, verbose_name='IP адрес')),
                ('name', models.CharField(max_length=100, verbose_name='Наименование')),
                ('description', models.CharField(max_length=50, verbose_name='Обозначение')),
                ('active_status', models.BooleanField(choices=[(True, 'Соединение установлено'), (False, 'Соединение разорвано')], default=True, verbose_name='Текущий статус')),
                ('catalog', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sanctuary.Catalog', verbose_name='Каталог')),
            ],
        ),
        migrations.CreateModel(
            name='Sidebar_statistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Дата начала периода')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='Дата конца периода')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='Время начала периода')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='Время конца периода')),
                ('de_facto', models.DurationField(blank=True, null=True, verbose_name='Время работы с учетом расписания')),
                ('status', models.BooleanField(blank=True, null=True, verbose_name='Текущий статус')),
                ('ip_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sanctuary.Object_list', verbose_name='Обьект отслеживания')),
            ],
        ),
        migrations.CreateModel(
            name='IP_rawdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Дата/Время')),
                ('status', models.BooleanField(verbose_name='Текущий статус')),
                ('ip_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sanctuary.Object_list', verbose_name='Обьект отслеживания')),
            ],
        ),
    ]