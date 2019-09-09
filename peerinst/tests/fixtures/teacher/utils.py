# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def login_teacher(client, teacher):
    return client.login(username=teacher.user.username, password="test")
