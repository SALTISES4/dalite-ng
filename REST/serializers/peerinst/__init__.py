__all__ = [
    "AssignmentSerializer",
    "AnswerSerializer",
    "DisciplineSerializer",
    "FeedbackReadSerialzer",
    "FeedbackWriteSerialzer",
    "GroupAssignmentSerializer",
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
    GroupAssignmentSerializer,
    QuestionSerializer,
    RankSerializer,
)
from .student_group import StudentGroupSerializer
from .teacher import TeacherSerializer
