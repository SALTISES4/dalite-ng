from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class MetaFeature(models.Model):
    TYPES = (("S", "String"), ("F", "Float"), ("I", "Integer"))

    key = models.CharField(max_length=20)
    type = models.CharField(max_length=2, choices=TYPES, default="S")
    value = models.CharField(max_length=256)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def get_value(self):
        if self.type == "F":
            return float(self.value)
        if self.type == "I":
            return int(self.value)
        return self.value

    def __str__(self):
        return "{} = {}".format(self.key, self.get_value)

    class Meta:
        unique_together = (("key", "type", "value"),)


class MetaSearch(models.Model):
    meta_feature = models.ForeignKey(MetaFeature, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    last_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Enforce uniqueness on feature key for instance
        super(MetaSearch, self).save(*args, **kwargs)
        meta_search_list = self.content_object.meta_search.exclude(pk=self.pk)
        if self.meta_feature.key in [
            s.meta_feature.key for s in meta_search_list
        ]:
            for obj in meta_search_list:
                if obj.meta_feature.key == self.meta_feature.key:
                    obj.delete()

    def __str__(self):
        return "{}: {}".format(self.content_object, self.meta_feature)
