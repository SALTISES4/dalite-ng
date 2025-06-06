import logging
import operator
import smtplib

from celery import shared_task
from django.core.mail import mail_managers, send_mail
from django.core.management import call_command

from dalite.celery import app, try_async

logger = logging.getLogger(__name__)


@shared_task
def update_question_meta_search_difficulty():
    # Prevent circular import
    from peerinst.models import MetaFeature, MetaSearch, Question

    qs = Question.objects.all()
    difficulty_levels = qs[0].get_matrix().keys()
    for d in difficulty_levels:
        f, created = MetaFeature.objects.get_or_create(
            key="difficulty", value=d, type="S"
        )
        if created:
            logger.info(f"New difficulty level created: {f}")

    for q in qs:
        level = max(q.get_matrix().iteritems(), key=operator.itemgetter(1))[0]
        f = MetaFeature.objects.get(key="difficulty", value=level, type="S")
        s = MetaSearch.objects.create(meta_feature=f, content_object=q)
        q.meta_search.add(s)

        logger.info(f"Updating difficulty of '{q}''")
        logger.info(f"Feature: {f}")
        logger.info(f"Search object: {s}")

        assert (
            q.meta_search.filter(meta_feature__key="difficulty").count() == 1
        )


@shared_task
def elasticsearch_reindex():
    logger.info("start rebuild elasticsearch index")
    call_command("search_index", "--rebuild", "-f")
    logger.info("rebuilt elasticsearch index")
    return


@try_async
@shared_task
def send_mail_async(*args, **kwargs):
    try:
        send_mail(*args, **kwargs)
    except smtplib.SMTPException:
        err = "There was an error sending the email."
        logger.error(err)


# @try_async
# @shared_task
# def mail_managers_async(*args, **kwargs):
#     try:
#         logger.info(f"Sending email:")
#         result = mail_managers(*args, **kwargs)
#         logger.info(f"Email send result: {result}")
#     except Exception as e:
#         logger.error("Failed to send email", exc_info=True)
#         raise

@shared_task
def mail_managers_async(*args, **kwargs):
    import time
    logger.warning(f"[TASK STARTED] args={args}, kwargs={kwargs}")
    time.sleep(2)
    try:
        result = mail_managers(*args, **kwargs)
        logger.warning(f"[TASK COMPLETED] result={result}")
        return result
    except Exception as e:
        logger.error("[TASK FAILED]", exc_info=True)
        raise


@try_async
@shared_task
def distribute_assignment_to_students_async(student_group_assignment_pk):
    # Prevent circular import
    from peerinst.models import StudentGroupAssignment

    student_group_assignment = StudentGroupAssignment.objects.get(
        pk=student_group_assignment_pk
    )
    for student in student_group_assignment.group.students.all():
        logger.info(
            "Adding assignment %d for student %d",
            student_group_assignment.pk,
            student.pk,
        )
        student.add_assignment(student_group_assignment)


@try_async
@shared_task
def compute_gradebook_async(group_pk, assignment_pk):
    """
    Sends the compute_gradebook task to celery returning the task id.

    Parameters
    ----------
    group_pk : int
        Primary key of the group for which to compute the gradebook
    assignment_pk : Optional[int] (default : None)
        Primary key of the assignment for which to compute the gradebook

    Returns
    -------
    Either
        str
            Task id if run asynchronously
        Either
            If run synchronously and group gradebook wanted
                {
                    assignments: List[str]
                        Assignment identifier
                    school_id_needed: bool
                        If a school id is needed
                    results: [{
                        school_id: Optional[str]
                            School id if needed
                        email: str
                            Student email
                        assignments: [{
                            n_completed: int
                                Number of completed questions
                            n_correct: int
                                Number of correct questions
                        }]
                    }]
                }
            If run synchronously and assignment gradebook wanted
                {
                    questions: List[str]
                        Question title
                    school_id_needed: bool
                        If a school id is needed
                    results: [{
                        school_id: Optional[str]
                            School id if needed
                        email: str
                            Student email
                        questions: List[float]
                            Grade for each question
                    }]
                }
    """
    # Prevent circular import
    from .gradebooks import compute_gradebook

    return compute_gradebook(group_pk, assignment_pk)


@shared_task
def populate_answer_start_time_from_ltievent_logs_task(
    day_of_logs, event_type
):
    from .util import populate_answer_start_time_from_ltievent_logs

    populate_answer_start_time_from_ltievent_logs(day_of_logs, event_type)


@app.task
def clean_notifications():
    from .models import StudentNotification

    StudentNotification.clean()
