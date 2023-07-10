__all__ = [
    "AssignmentSerializer",
    "AnswerSerializer",
    "CollectionSerializer",
    "DisciplineSerializer",
    "FeedbackReadSerialzer",
    "FeedbackWriteSerialzer",
    "QuestionSerializer",
    "RankSerializer",
    "StudentGroupAssignmentAnswerSerializer",
    "StudentGroupAssignmentSerializer",
    "StudentGroupSerializer",
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
    CollectionSerializer,
    DisciplineSerializer,
    QuestionSerializer,
    RankSerializer,
    StudentGroupAssignmentSerializer,
)
from .student_group import StudentGroupSerializer
from .teacher import TeacherSerializer
