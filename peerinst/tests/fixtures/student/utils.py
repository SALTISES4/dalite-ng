from peerinst.models import StudentGroupMembership
from peerinst.students import get_student_username_and_password


def add_to_group(students, groups):
    if not hasattr(students, "__iter__"):
        students = [students]
    if not hasattr(groups, "__iter__"):
        groups = [groups]
    for student in students:
        student.groups.add(*groups)
        for group in groups:
            StudentGroupMembership.objects.get_or_create(
                student=student, group=group
            )


def login_student(client, student):
    username, password = get_student_username_and_password(
        student.student.email
    )
    return client.login(username=username, password=password)
