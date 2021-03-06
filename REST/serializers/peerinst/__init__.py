__all__ = [
    "AssignmentSerializer",
    "AnswerSerializer",
    "DisciplineSerializer",
    "FeedbackReadSerialzer",
    "FeedbackWriteSerialzer",
    "QuestionSerializer",
    "RankSerializer",
    "StudentGroupSerializer",
    "StudentGroupAssignmentAnswerSerializer",
    "TeacherSerializer",
]

from .assignment import (
    AssignmentSerializer,
    DisciplineSerializer,
    QuestionSerializer,
    RankSerializer,
)  # noqa
from .answer import (
    AnswerSerializer,
    FeedbackReadSerialzer,
    FeedbackWriteSerialzer,
    StudentGroupAssignmentAnswerSerializer,
)  # noqa
from .student_group import StudentGroupSerializer
from .teacher import TeacherSerializer
