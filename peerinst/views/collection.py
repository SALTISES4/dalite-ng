import collections

from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.forms import ModelForm
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView

from dalite.views.utils import get_json_params
from peerinst.admin_views import get_assignment_aggregates

from ..mixins import (
    LoginRequiredMixin,
    NoStudentsMixin,
    TOSAcceptanceRequiredMixin,
    student_check,
)
from ..models import (
    Assignment,
    Collection,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from .decorators import teacher_required


class CollectionForm(ModelForm):
    class Meta:
        model = Collection
        fields = [
            "title",
            "description",
            "image",
            "assignments",
            "discipline",
            "private",
        ]

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher")
        super(CollectionForm, self).__init__(*args, **kwargs)
        self.fields["private"].initial = True
        self.fields["discipline"].queryset = teacher.disciplines.all()


class CollectionCopyForm(forms.Form):
    pk = forms.ModelChoiceField(
        queryset=Collection.objects.filter(private=False)
    )


@require_POST
@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def collection_copy(request):

    form = CollectionCopyForm(request.POST)
    if form.is_valid():
        # Get the collection to copy
        collection_to_copy = Collection.objects.get(
            pk=form.cleaned_data["pk"].pk,
        )
        # Make the copy
        new_collection = Collection.objects.create(
            discipline=collection_to_copy.discipline,
            title=collection_to_copy.title,
            owner=request.user.teacher,
        )

        return HttpResponseRedirect(
            reverse("collection-detail", args=(new_collection.pk,))
        )

    return HttpResponseBadRequest("")


class CollectionCreateView(
    LoginRequiredMixin, NoStudentsMixin, TOSAcceptanceRequiredMixin, CreateView
):

    template_name = "peerinst/collection/collection_form.html"
    form_class = CollectionForm

    def get_success_url(self):
        return reverse("collection-update", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super(CollectionCreateView, self).get_form_kwargs()
        kwargs["teacher"] = Teacher.objects.get(user=self.request.user)
        return kwargs

    def form_valid(self, form):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        form.instance.owner = teacher
        return super(CollectionCreateView, self).form_valid(form)


class CollectionDetailView(LoginRequiredMixin, NoStudentsMixin, DetailView):
    model = Collection
    template_name = "peerinst/collection/collection_detail.html"

    def dispatch(self, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if (
            teacher == self.get_object().owner
            or self.get_object().private is False
        ):
            return super(CollectionDetailView, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        collection = self.get_object()
        context["collection_data"] = collection_data(collection=collection)
        return context


def assignment_data(assignment):
    """
    returns only question sums counter object from assignment aggregates method
    """
    q_sums, q_students = get_assignment_aggregates(assignment=assignment)
    return q_sums


def collection_paginate(request):

    if not Teacher.objects.filter(user=request.user).exists():
        return HttpResponse(
            _(
                "You must be logged in as a teacher to search the database. "
                "Log in again with a teacher account."
            )
        )

    if request.method == "GET" and request.user.is_authenticated:
        page = int(request.GET.get("page", default=1))
        id = int(request.GET.get("collection_pk"))
        assignments = Collection.objects.get(pk=id).assignments.all()

        paginator = Paginator(list(assignments), 3)

        try:
            page_assignments = paginator.get_page(page)
        except PageNotAnInteger:
            page_assignments = paginator.get_page(1)
        except EmptyPage:
            page_assignments = paginator.get_page(paginator.num_pages)

        if assignments.count() > 3:
            is_multiple_pages = True
        else:
            is_multiple_pages = False

        assignment_data = {}
        context = {
            "paginator": page_assignments,
            "is_multiple_pages": is_multiple_pages,
            "assignment_data": assignment_data,
        }

        for assignment in assignments:
            (
                context["assignment_data"][assignment.pk],
                q_students,
            ) = get_assignment_aggregates(assignment=assignment)

        return TemplateResponse(
            request,
            "peerinst/collection/collection_detail_page.html",
            context=context,
        )
    else:
        return HttpResponse(
            _("An error occurred.  Retry search after logging in again.")
        )


def collection_data(collection):
    """
    sums all of a collection's assignment's counter objects
    """
    assignments = collection.assignments.all()
    a_sums = collections.Counter(
        total_answers=0,
        correct_first_answers=0,
        correct_second_answers=0,
        switches=0,
    )
    for assignment in assignments:
        a_sums += assignment_data(assignment)
    return a_sums


class CollectionUpdateView(LoginRequiredMixin, NoStudentsMixin, UpdateView):
    template_name = "peerinst/collection/collection_update.html"
    model = Collection
    fields = ["title", "description", "image", "discipline", "private"]

    def dispatch(self, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if teacher == self.get_object().owner or self.request.user.is_staff:
            return super(CollectionUpdateView, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied

    def get_success_url(self):
        return reverse("collection-detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        context["teacher"] = get_object_or_404(Teacher, user=self.request.user)
        collection = self.get_object()
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context["collection_assignments"] = collection.assignments.all()
        context["owned_assignments"] = [
            a
            for a in list(Assignment.objects.filter(owner=self.request.user))
            if a not in self.get_object().assignments.all()
        ]
        context["followed_assignments"] = [
            a
            for a in teacher.assignments.exclude(owner=self.request.user)
            if a not in self.get_object().assignments.all()
        ]
        return context


class CollectionDeleteView(LoginRequiredMixin, NoStudentsMixin, DeleteView):
    model = Collection
    template_name = "peerinst/collection/collection_delete.html"

    def dispatch(self, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if teacher == self.get_object().owner or self.request.user.is_staff:
            return super(CollectionDeleteView, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied

    def get_success_url(self):
        return reverse("collection-list")


class CollectionListView(LoginRequiredMixin, NoStudentsMixin, ListView):
    """
    list for collections that are public or owned by teacher
    """

    model = Collection
    template_name = "peerinst/collection/collection_list.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return Collection.objects.filter(Q(private=False) | Q(owner=teacher))


class PersonalCollectionListView(
    LoginRequiredMixin, NoStudentsMixin, ListView
):
    """
    list for collections where teacher is the owner
    """

    model = Collection
    template_name = "peerinst/collection/personal_collection_list.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return Collection.objects.filter(owner=teacher)


class FollowedCollectionListView(
    LoginRequiredMixin, NoStudentsMixin, ListView
):
    """
    list for collections followed by teacher that are public
    or owned by teacher
    """

    model = Collection
    template_name = "peerinst/collection/followed_collection_list.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return Collection.objects.filter(
            Q(followers=teacher, private=False)
            | Q(followers=teacher, owner=teacher)
        )


class FeaturedCollectionListView(
    LoginRequiredMixin, NoStudentsMixin, ListView
):
    """
    list for featured collections that are public or owned by teacher
    """

    model = Collection
    template_name = "peerinst/collection/featured_collection_list.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return Collection.objects.filter(
            Q(featured=True, private=False) | Q(featured=True, owner=teacher)
        )


def featured_collections(request):
    data = serializers.serialize(
        "json", Collection.objects.filter(featured=True)
    )
    return JsonResponse(data, safe=False)


class CollectionDistributeDetailView(
    LoginRequiredMixin, NoStudentsMixin, DetailView
):
    """
    view to assign/unassign a collection's assignments from a student group
    """

    model = Collection
    template_name = "peerinst/collection/collection_distribute.html"

    def dispatch(self, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if (
            teacher == self.get_object().owner
            or self.get_object().private is False
        ):
            return super(CollectionDistributeDetailView, self).dispatch(
                *args, **kwargs
            )
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        collection = self.get_object()
        context["student_groups"] = teacher.current_groups.all()
        context["collection_data"] = collection_data(collection=collection)
        context["group_data"] = {}
        for group in teacher.current_groups.all():
            context["group_data"][group.pk] = True
            for assignment in collection.assignments.all():
                if not StudentGroupAssignment.objects.filter(
                    group=group, assignment=assignment
                ).exists():
                    context["group_data"][group.pk] = False
        return context


@login_required
@user_passes_test(student_check, login_url="/access_denied_and_logout/")
def collection_statistics(request):
    collection = get_object_or_404(Collection, pk=request.POST.get("pk"))
    collection_stats = collection_data(collection=collection)
    data = {
        "totalAnswers": collection_stats["total_answers"],
        "correctFirstAnswers": collection_stats["correct_first_answers"],
        "correctSecondAnswers": collection_stats["correct_second_answers"],
        "switches": collection_stats["switches"],
    }
    return JsonResponse(data)


@teacher_required
@require_POST
def collection_add_assignment(request, teacher):
    """
    creates a collection with assignments from a student group
    used in group detail view
    """
    args = get_json_params(request, args=["group_pk"])
    if isinstance(args, HttpResponse):
        return args
    (group_pk,), _ = args

    student_group = get_object_or_404(StudentGroup, pk=group_pk)

    title = (student_group.title + "'s curriculum")[:40]
    description = (
        "This collection contains all assignments that have been assigned to "
        + student_group.title
        + "'s students."
    )[:200]

    collection = Collection.objects.create(
        discipline=teacher.disciplines.first(),
        owner=teacher,
        title=title,
        description=description,
    )

    student_group_assignments = student_group.studentgroupassignment_set.all()
    for assignment in student_group_assignments:
        if assignment.assignment not in collection.assignments.all():
            collection.assignments.add(assignment.assignment)
    return JsonResponse({"pk": collection.pk})
