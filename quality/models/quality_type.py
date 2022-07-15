from django.db import models


class QualityType(models.Model):
    type = models.CharField(max_length=32)

    def __str__(self):
        return self.type


class QualityUseType(models.Model):
    type = models.CharField(max_length=32)

    def __str__(self):
        return self.type
