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

from .answer import (  # noqa
    AnswerSerializer,
    FeedbackReadSerialzer,
    FeedbackWriteSerialzer,
    StudentGroupAssignmentAnswerSerializer,
)
from .assignment import (  # noqa
    AssignmentSerializer,
    DisciplineSerializer,
    QuestionSerializer,
    RankSerializer,
)
from .student_group import StudentGroupSerializer
from .teacher import TeacherSerializer
