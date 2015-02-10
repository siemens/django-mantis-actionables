# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0004_singletonobservable_mantis_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionabletagginghistory',
            name='user',
            field=models.ForeignKey(related_name=b'actionable_tagging_history', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
