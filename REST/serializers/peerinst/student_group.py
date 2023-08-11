from rest_framework import serializers

from peerinst.models import StudentGroup, Teacher

from .dynamic_serializer import DynamicFieldsModelSerializer


class StudentGroupSerializer(DynamicFieldsModelSerializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        return obj.get_absolute_url()

    def create(self, validated_data):
        """Attach group to teacher"""
        group = super().create(validated_data)
        teacher = Teacher.objects.get(user=self.context["request"].user)
        teacher.current_groups.add(group)
        teacher.save()
        group.teacher.add(teacher)
        group.save()
        return group

    class Meta:
        model = StudentGroup
        fields = ["pk", "name", "semester", "teacher", "title", "url", "year"]
