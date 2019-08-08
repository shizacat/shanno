# Generated by Django 2.2.3 on 2019-08-05 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('annotation', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta', models.TextField(default='{}')),
                ('file_name', models.CharField(max_length=100, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterField(
            model_name='projects',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='Sequence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('meta', models.TextField(default='{}')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sequences', to='annotation.Documents')),
            ],
        ),
        migrations.AddField(
            model_name='documents',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='annotation.Projects'),
        ),
    ]