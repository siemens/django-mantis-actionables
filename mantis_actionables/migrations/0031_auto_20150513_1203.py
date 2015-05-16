# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0030_source_outdated'),
    ]

    operations = [
        migrations.CreateModel(
            name='IDSSignatureRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ids_signature', models.ForeignKey(related_name='singleton_thru', to='mantis_actionables.IDSSignature')),
                ('singleton', models.ForeignKey(related_name='ids_signature_thru', to='mantis_actionables.SingletonObservable')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='idssignature',
            name='content',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='idssignature',
            name='import_list',
            field=models.ManyToManyField(to='mantis_actionables.SingletonObservable', through='mantis_actionables.IDSSignatureRevision'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='singletonobservable',
            name='ids_signature',
            field=models.ForeignKey(to='mantis_actionables.IDSSignature', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='idssignature',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='idssignature',
            name='value',
        ),
        migrations.RemoveField(
            model_name='idssignature',
            name='type',
        ),
    ]
