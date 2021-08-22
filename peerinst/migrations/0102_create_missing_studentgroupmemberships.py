from collections import Counter

from django.db import migrations, models


def forwards_func(apps, scheme_editor):
    """
    1. for all groups, ensure there is StudentGroupMembership object for each
    student in that group
    2. set mode_created, since groups with no studentgroupmeberships must
    have been formed via LTI
    3. Infer the institution of the group from LtiUserData for associated
    students
    """
    StudentGroupMembership = apps.get_model("peerinst", "StudentGroupMembership")
    StudentGroup = apps.get_model("peerinst", "StudentGroup")
    Institution = apps.get_model("peerinst", "Institution")
    InstitutionalLMS = apps.get_model("peerinst", "InstitutionalLMS")
    LtiUserData = apps.get_model("django_lti_tool_provider","LtiUserData")

    for group in StudentGroup.objects.all():
        # check if there are any students:
        if group.student_set.all().count()>0:
            print(group.name,group.title)
            # check if there are 0 studentgroupmemberships
            if group.studentgroupmembership_set.all().count() == 0:
                lti_event_urls = []
                # create studentgroupmemberships
                for student in group.student_set.all():
                    sgm, _ = StudentGroupMembership.objects.get_or_create(
                        student=student,
                        group = group,
                        current_member = True,
                        send_emails = False,
                    )
                    student_lti_event = LtiUserData.objects.filter(user=student.student).first()
                    # collect LtiUserData objects linked to the students in this group
                    lti_event_urls.append(
                        student_lti_event.edx_lti_parameters["tool_consumer_instance_guid"]
                    )
                # these groups must have been formed via LTI
                group.mode_created = "LTI"

                # use LtiUserData objects to infer institution of group
                c = Counter(lti_event_urls)
                most_common_url = c.most_common(1)[0][0]
                if most_common_url:
                    institutional_lms, created = InstitutionalLMS.objects.get_or_create(
                        url= most_common_url
                    )
                    if created:
                        institution = Institution.objects.create(
                            name=institutional_lms.url
                        )
                        institutional_lms.institution = institution

                        group.institution = institutional_lms.institution
                    print(f"**{group.institution}/{institutional_lms.url}**")

                group.save()

class Migration(migrations.Migration):

    dependencies =[('peerinst', '0101_institutionallms'),]

    operations = [
        migrations.RunPython(
        code = forwards_func, reverse_code = migrations.RunPython.noop
        )
    ]
