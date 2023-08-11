__all__ = [
    "AssignmentCreateView",
    "AssignmentDetailView",
    "AssignmentUpdateView",
    "DashboardView",
    "GroupCreateView",
    "GroupUpdateView",
    "LibraryView",
    "QuestionCreateView",
    "SearchView",
]

from .assignment import (  # noqa
    AssignmentCreateView,
    AssignmentDetailView,
    AssignmentUpdateView,
)
from .dashboard import DashboardView  # noqa
from .group import GroupCreateView, GroupUpdateView  # noqa
from .library import LibraryView  # noqa
from .question import QuestionCreateView  # noqa
from .search import SearchView  # noqa
