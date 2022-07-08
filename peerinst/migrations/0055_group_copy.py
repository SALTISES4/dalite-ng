from django.db import migrations


def copy_over_student_groups_to_field_with_through(apps, _):
    Student = apps.get_model("peerinst", "Student")
    StudentGroupMembership = apps.get_model(
        "peerinst", "StudentGroupMembership"
    )

    for student in Student.objects.all():
        for group in student.groups.all():
            StudentGroupMembership.objects.create(
                student=student, group=group, current_member=True
            )


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0054_auto_20181116_1727")]

    operations = [
        migrations.RunPython(copy_over_student_groups_to_field_with_through)
    ]
