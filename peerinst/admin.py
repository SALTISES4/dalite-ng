from datetime import datetime

from django import forms
from django.contrib import admin
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.auth.models import User
from django.core import exceptions
from django.urls import reverse
from django.utils.html import escape, format_html
from django.utils.translation import ugettext_lazy as _

from . import models
from .models import (
    Answer,
    AnswerChoice,
    Assignment,
    Category,
    Collection,
    Discipline,
    Institution,
    InstitutionalLMS,
    LastLogout,
    LtiEvent,
    Question,
    QuestionFlag,
    QuestionFlagReason,
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupMembership,
    StudentNotification,
    StudentNotificationType,
    Subject,
    Teacher,
    TeacherNotification,
)


class AnswerChoiceInlineForm(forms.ModelForm):
    class Meta:
        widgets = {"text": forms.Textarea(attrs={"style": "width: 500px"})}


class AnswerChoiceInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        forms = [
            f
            for f in self.forms
            if getattr(f, "cleaned_data", None)
            and not f.cleaned_data.get("DELETE", False)
        ]
        errors = []
        if len(forms) < 2:
            errors.append(_("There must be at least two answer choices."))
        correct_answers = sum(
            f.cleaned_data.get("correct", False) for f in forms
        )
        if not correct_answers:
            errors.append(
                _("At least one of the answers must be marked as correct.")
            )
        if errors:
            raise exceptions.ValidationError(errors)


class AnswerChoiceInline(admin.TabularInline):
    model = AnswerChoice
    form = AnswerChoiceInlineForm
    formset = AnswerChoiceInlineFormSet
    max_num = 5
    extra = 5
    ordering = ["id"]


class AnswerModelForm(forms.ModelForm):
    class Meta:
        labels = {"first_answer_choice": _("Associated answer")}
        help_texts = {
            "rationale": _(
                "An example rationale that will be shown to students during the\
                 answer review."
            ),
            "first_answer_choice": _(
                "The number of the associated answer; 1 = first answer, 2 =\
                 second answer etc."
            ),
        }


class AnswerInline(admin.StackedInline):
    model = Answer
    form = AnswerModelForm
    verbose_name = _("example answer")
    verbose_name_plural = _("example answers")
    extra = 0
    fields = ["hint", "rationale", "first_answer_choice"]
    inline_classes = ["grp-collapse", "grp-open"]
    readonly_fields = ["hint"]

    def hint(self, obj):
        return _(
            'You can add example answers more comfortably by using the\
             "Preview" button in the top right corner.  The button appears\
             after saving the question for the first time.'
        )

    def get_queryset(self, request):
        # Only include example answers not belonging to any student
        qs = admin.StackedInline.get_queryset(self, request)
        return qs.filter(user_token="", show_to_others=True)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    pass


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "title",
                    "difficulty",
                    "user",
                    "collaborators",
                    "text",
                    "created_on",
                    "last_modified",
                    "discipline",
                    "category",
                    "id",
                    "parent",
                    "type",
                ]
            },
        ),
        (
            _("Question image or video"),
            {"fields": ["image", "image_alt_text", "video_url"]},
        ),
        (
            None,
            {
                "fields": [
                    "answer_style",
                    "fake_attributions",
                    "sequential_review",
                    "rationale_selection_algorithm",
                    "grading_scheme",
                ]
            },
        ),
    ]
    radio_fields = {
        "answer_style": admin.HORIZONTAL,
        "rationale_selection_algorithm": admin.HORIZONTAL,
        "grading_scheme": admin.HORIZONTAL,
    }
    readonly_fields = [
        "id",
        "user",
        "parent",
        "created_on",
        "last_modified",
        "difficulty",
    ]
    inlines = [AnswerChoiceInline, AnswerInline]

    def answer_count(self):
        return self.answer_set.all().count()

    def created_on_date(self):
        return datetime.strftime(self.created_on, "%Y-%m-%d")

    list_display = [
        created_on_date,
        "discipline",
        "type",
        "user",
        "title",
        answer_count,
    ]
    list_display_links = ("title",)
    list_filter = ["type", "discipline"]
    ordering = ["-created_on"]
    search_fields = ["title", "text", "category__title"]

    def difficulty(self, obj):
        try:
            difficulty = obj.meta_search.get(
                meta_feature__key="difficulty", meta_feature__type="S"
            ).meta_feature.value
        except exceptions.ObjectDoesNotExist:
            difficulty = None

        return difficulty


@admin.register(QuestionFlagReason)
class QuestionFlagReasonAdmin(admin.ModelAdmin):
    pass


@admin.register(QuestionFlag)
class QuestionFlagAdmin(admin.ModelAdmin):
    list_display = ["question_link", "flag_reason_list", "user", "comment"]
    exclude = [
        "user",
    ]

    def question_link(self, obj):
        link = reverse(
            "admin:peerinst_question_change", args=[obj.question.pk]
        )
        return format_html('<a href="{}">{}</a>', link, obj.question.title)

    def flag_reason_list(self, obj):
        return "; ".join(obj.flag_reason.all().values_list("title", flat=True))

    question_link.short_description = "Question"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    pass


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    filter_horizontal = ["categories"]


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    pass


@admin.register(InstitutionalLMS)
class InstitutionalLMSAdmin(admin.ModelAdmin):
    pass


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    filter_horizontal = ["questions"]
    search_fields = ["identifier"]
    fields = [
        "identifier",
        "title",
        "owner",
        "description",
        "intro_page",
        "conclusion_page",
    ]
    readonly_fields = ["identifier", "owner"]


def publish_answers(modeladmin, request, queryset):
    queryset.update(show_to_others=True)


publish_answers.short_description = _("Show selected answers to students")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "question",
        # "user_token",
        "first_answer_choice_label",
        "second_answer_choice_label",
        "rationale",
        "show_to_others",
        "expert",
        "show_chosen_rationale",
        # "upvotes",
        # "downvotes",
        # "datetime_start",
        # "datetime_first",
        "datetime_second",
    ]
    list_display_links = None
    list_editable = ["rationale", "show_to_others", "expert"]
    list_filter = ["expert", "show_to_others", "question"]
    actions = [publish_answers]
    search_fields = ["question__title", "rationale", "user_token", "id"]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    readonly_fields = [
        "user",
        "reputation",
        "quality",
    ]
    filter_horizontal = [
        "assignments",
        "current_groups",
    ]


@admin.register(TeacherNotification)
class TeacherNotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(LastLogout)
class LastLogoutAdmin(admin.ModelAdmin):
    list_display = ["user", "last_logout"]
    readonly_fields = ["user", "last_logout"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    def student_username(self):
        return self.student.username

    def student_email(self):
        return self.student.email

    list_display = [student_username, student_email]
    search_fields = ["student__email", "student__username"]
    readonly_fields = ["student"]
    exclude = ["reputation"]


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    def teacher(self):
        if self.teacher.first():
            return self.teacher.first().user.email
        else:
            return ""

    def num_students(self):
        return self.studentgroupmembership_set.all().count()

    list_display = [
        "id",
        "year",
        "semester",
        "name",
        "title",
        teacher,
        num_students,
        "discipline",
        "institution",
    ]
    search_fields = ["name", "institution"]
    list_filter = [
        "year",
        "semester",
        "mode_created",
        "institution",
        "discipline",
    ]
    readonly_fields = ["name", "title", "student_id_needed", num_students]
    exclude = [
        "quality",
    ]


@admin.register(StudentNotification)
class StudentNotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentNotificationType)
class StudentNotificationTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(StudentGroupAssignment)
class StudentGroupAssignmentAdmin(admin.ModelAdmin):
    list_display = ("group", "assignment")
    search_fields = [
        "assignment__title",
        "assignment__identifier",
        "group__name",
        "group__title",
        "group__teacher__user__username",
    ]


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("student", "group_assignment")
    search_fields = [
        "student__student__username",
        "group_assignment__assignment__title",
        "group_assignment__assignment__identifier",
        "group_assignment__group__name",
        "group_assignment__group__title",
    ]


@admin.register(StudentGroupMembership)
class StudentGroupMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "get_student_email",
        "group",
        "student_school_id",
    )
    search_fields = ["student__student__email"]

    def get_student_email(self, obj):
        return obj.student.student.email

    get_student_email.short_description = "Student"
    get_student_email.order_field = "student__student_email"


@admin.register(LtiEvent)
class LtiEventAdmin(admin.ModelAdmin):
    search_fields = ["username", "assignment_id"]
    list_display = (
        "timestamp",
        "username",
        "event_type",
        "question_id",
        "assignment_id",
    )
    list_filter = (("question_id"), ("timestamp", admin.DateFieldListFilter))
    readonly_fields = (
        "timestamp",
        "username",
        "event_type",
        "question_id",
        "assignment_id",
        "event_log",
    )


# https://djangosnippets.org/snippets/2484/
class LogEntryAdmin(admin.ModelAdmin):

    date_hierarchy = "action_time"

    readonly_fields = [f.name for f in LogEntry._meta.get_fields()]

    list_filter = ["user", "content_type", "action_flag"]

    search_fields = ["object_repr", "change_message"]

    list_display = [
        "action_time",
        "user",
        "content_type",
        "object_link",
        "action_flag",
        "change_message",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != "POST"

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse(
                    "admin:%s_%s_change" % (ct.app_label, ct.model),
                    args=[obj.object_id],
                ),
                escape(obj.object_repr),
            )
        return link

    object_link.allow_tags = True
    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"

    def queryset(self, request):
        return (
            super(LogEntryAdmin, self)
            .queryset(request)
            .prefetch_related("content_type")
        )


class MessageAdmin(admin.ModelAdmin):
    def save_related(self, req, form, *args, **kwargs):
        super(MessageAdmin, self).save_related(req, form, *args, **kwargs)
        for_users = [t.type for t in form.instance.for_users.all()]
        if "teacher" in for_users:
            for teacher in Teacher.objects.all():
                models.UserMessage.objects.get_or_create(
                    user=teacher.user, message=form.instance
                )
        if "student" in for_users:
            for student in Student.objects.all():
                models.UserMessage.objects.get_or_create(
                    user=student.student, message=form.instance
                )


admin.site.register(LogEntry, LogEntryAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.MessageType)


class SaltiseMemberAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            teachers = Teacher.objects.all().values_list("user", flat=True)
            kwargs["queryset"] = User.objects.filter(pk__in=teachers).order_by(
                "username"
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(models.SaltiseMember, SaltiseMemberAdmin)
admin.site.register(models.UserType)
