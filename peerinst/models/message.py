from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from .admin import UserType


class SaltiseMember(models.Model):
    name = models.CharField(max_length=64)
    picture = models.ImageField(blank=True, null=True, upload_to="images")
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, blank=True, null=True
    )
    expert = models.BooleanField(_("SALTISE fellow"), default=False)

    def __str__(self):
        return self.name


class MessageType(models.Model):
    type = models.CharField(max_length=32)
    removable = models.BooleanField(default=True)
    colour = models.CharField(max_length=7)

    def __str__(self):
        return self.type


class Message(models.Model):
    type = models.ForeignKey(MessageType, on_delete=models.CASCADE)
    authors = models.ManyToManyField(SaltiseMember, blank=True)
    title = models.CharField(max_length=128)
    text = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    link = models.URLField(blank=True, null=True)
    for_users = models.ManyToManyField(UserType)

    def __str__(self):
        return self.title


class UserMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    showing = models.BooleanField(default=True)
