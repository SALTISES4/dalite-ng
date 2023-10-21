__all__ = [
    "AssignmentCreateView",
    "AssignmentDetailView",
    "AssignmentUpdateView",
    "DashboardView",
    "LibraryView",
    "QuestionCreateView",
    "QuestionUpdateView",
    "SearchView",
]

from .assignment import (  # noqa
    AssignmentCreateView,
    AssignmentDetailView,
    AssignmentUpdateView,
)
from .dashboard import DashboardView  # noqa
from .library import LibraryView  # noqa
from .question import QuestionCreateView, QuestionUpdateView  # noqa
from .search import SearchView  # noqa
