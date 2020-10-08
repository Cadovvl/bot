from django.db import models
from django.db.models import UniqueConstraint


class IntConstants(models.Model):
    name = models.CharField(max_length=200)
    value = models.IntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['name'], name='Only one constant per name')
        ]


class Subscription(models.Model):
    name = models.CharField(max_length=200)
    chat = models.IntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['name', 'chat'], name='Only one subscription')
        ]


class Config(models.Model):
    name = models.CharField(max_length=200)
    key = models.CharField(max_length=200)
    val = models.CharField(max_length=200)
    constraints = [
        UniqueConstraint(fields=['name', 'key'], name='Unique param key')
    ]


class ChatConfig(models.Model):
    name = models.CharField(max_length=200)
    chat = models.IntegerField()
    key = models.CharField(max_length=200)
    val = models.CharField(max_length=200)
    constraints = [
        UniqueConstraint(fields=['name', 'chat', 'key'],
                         name='Unique param key per chat')
    ]
