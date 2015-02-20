# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0006_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='singletonobservable',
            name='subtype',
            field=models.ForeignKey(to='mantis_actionables.SingletonObservableSubtype'),
        ),
    ]
