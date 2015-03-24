# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0025_auto_20150312_1053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='context',
            name='type',
            field=models.SmallIntegerField(default=10, choices=[(10, b'INVES'), (20, b'IR')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='entitytype',
            name='name',
            field=models.CharField(unique=True, max_length=256),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='signaturetype',
            name='name',
            field=models.CharField(unique=True, max_length=255),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='action',
            unique_together=set([('user', 'comment')]),
        ),
        migrations.AlterUniqueTogether(
            name='actionabletag',
            unique_together=set([('context', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='status2x',
            unique_together=set([('action', 'status', 'timestamp')]),
        ),
    ]
