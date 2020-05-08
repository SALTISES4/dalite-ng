from typing import List

from django.conf.urls import include
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import user_passes_test
from django.urls import URLPattern, path
from django.views.decorators.cache import cache_page

# testing
from django.views.decorators.clickjacking import xframe_options_sameorigin

from . import admin_views, views
from .forms import NonStudentPasswordResetForm
from .mixins import student_check


def not_authenticated(user):
    return not user.is_authenticated


def old_patterns():
    return [
        # DALITE
        # Assignment table of contents - Enforce sameorigin to prevent access from LMS  # noqa
        path(
            "browse/",
            xframe_options_sameorigin(views.browse_database),
            name="browse-database",
        ),
        path(
            "assignment-list/",
            xframe_options_sameorigin(views.AssignmentListView.as_view()),
            name="assignment-list",
        ),
        path(
            "question/create",
            views.QuestionCreateView.as_view(),
            name="question-create",
        ),
        path(
            "question/clone/<int:pk>",
            views.QuestionCloneView.as_view(),
            name="question-clone",
        ),
        path(
            "question/update/<int:pk>",
            views.QuestionUpdateView.as_view(),
            name="question-update",
        ),
        path("question/delete", views.question_delete, name="question-delete"),
        path(
            "discipline/create",
            views.DisciplineCreateView.as_view(),
            name="discipline-create",
        ),
        path(
            "discipline/form/<int:pk>",
            views.discipline_select_form,
            name="discipline-form",
        ),
        path(
            "discipline/form",
            views.discipline_select_form,
            name="discipline-form",
        ),
        path(
            "disciplines/form/<int:pk>",
            views.disciplines_select_form,
            name="disciplines-form",
        ),
        path(
            "disciplines/form",
            views.disciplines_select_form,
            name="disciplines-form",
        ),
        path(
            "category/create",
            views.CategoryCreateView.as_view(),
            name="category-create",
        ),
        path(
            "category/form/<int:pk>",
            views.category_select_form,
            name="category-form",
        ),
        path(
            "category/form", views.category_select_form, name="category-form",
        ),
        path(
            "answer-choice/form/<int:question_id>",
            views.answer_choice_form,
            name="answer-choice-form",
        ),
        path(
            "sample-answer/form/<int:question_id>",
            admin_views.QuestionPreviewViewBase.as_view(),
            name="sample-answer-form",
        ),
        path(
            "sample-answer/form/<int:question_id>/done",
            views.sample_answer_form_done,
            name="sample-answer-form-done",
        ),
        path(
            "assignment/copy/<assignment_id>",
            views.AssignmentCopyView.as_view(),
            name="assignment-copy",
        ),
        path(
            "assignment/edit",
            views.update_assignment_question_list,
            name="assignment-edit-ajax",
        ),
        path(
            "assignment/edit/<assignment_id>",
            views.AssignmentEditView.as_view(),
            name="assignment-edit",
        ),
        path(
            "question-search/", views.question_search, name="question-search",
        ),
        path(
            "collection-search/",
            views.collection_search,
            name="collection-search",
        ),
        # Standalone
        path(
            "live/access/<token>/<assignment_hash>",  # noqa
            views.live,
            name="live",
        ),
        path(
            "live/navigate/<assignment_id>/<question_id>/<direction>/<index>",  # noqa
            views.navigate_assignment,
            name="navigate-assignment",
        ),
        path(
            "live/signup/form/<group_hash>",
            views.signup_through_link,
            name="signup-through-link",
        ),
        path(
            "live/studentgroupassignment/create/<assignment_id>",
            views.StudentGroupAssignmentCreateView.as_view(),
            name="student-group-assignment-create",
        ),
        # Teachers
        path(
            "teacher-account/<int:pk>/",
            views.TeacherDetailView.as_view(),
            name="teacher",
        ),
        path(
            "teacher/<int:pk>/",
            views.TeacherUpdate.as_view(),
            name="teacher-update",
        ),
        path(
            "teacher/<int:pk>/assignments/",
            views.TeacherAssignments.as_view(),
            name="teacher-assignments",
        ),
        path(
            "teacher/<int:pk>/blinks/",
            views.TeacherBlinks.as_view(),
            name="teacher-blinks",
        ),
        path(
            "teacher/favourite",
            views.teacher_toggle_favourite,
            name="teacher-toggle-favourite",
        ),
        path(
            "teacher/<int:pk>/groups/",
            views.TeacherGroups.as_view(),
            name="teacher-groups",
        ),
        path(
            "teacher/<int:pk>/group/<group_hash>/share",  # noqa
            views.TeacherGroupShare.as_view(),
            name="group-share",
        ),
        path(
            "teacher/<int:teacher_id>/group_assignments/",
            views.StudentGroupAssignmentListView.as_view(),
            name="group-assignments",
        ),
        path(
            "teacher/student_activity/",
            views.student_activity,
            name="student-activity",
        ),
        path(
            "teacher/report/all_groups/<assignment_id>/",
            views.report,
            name="report-all-groups",
        ),
        path(
            "teacher/report/all_assignments/<int:group_id>/",
            views.report,
            name="report-all-assignments",
        ),
        path(
            "teacher/report_selector",
            views.report_selector,
            name="report_selector",
        ),
        path("teacher/custom_report/", views.report, name="report-custom"),
        path(
            "report_rationales_chosen",
            views.report_assignment_aggregates,
            name="report_rationales_chosen",
        ),
        # Auth
        path("", views.landing_page, name="landing_page"),
        path("signup/", views.sign_up, name="sign_up"),
        path(
            "login/",
            user_passes_test(not_authenticated, login_url="/welcome/")(
                auth_views.LoginView.as_view()
            ),
            name="login",
        ),
        path("logout/", views.logout_view, name="logout"),
        path("welcome/", views.welcome, name="welcome"),
        # Only non-students can change their password
        path(
            "password_change/",
            user_passes_test(student_check)(
                auth_views.PasswordChangeView.as_view()
            ),
            name="password_change",
        ),
        path(
            "password_change/done/",
            auth_views.PasswordChangeDoneView.as_view(),
            name="password_change_done",
        ),
        path(
            "password_reset/",
            auth_views.PasswordResetView.as_view(),
            {
                "html_email_template_name": "registration/password_reset_email_html.html",  # noqa
                "password_reset_form": NonStudentPasswordResetForm,
            },
            name="password_reset",
        ),
        path(
            "password_reset/done/",
            auth_views.PasswordResetDoneView.as_view(),
            name="password_reset_done",
        ),
        path(
            "reset/<uidb64>/<token>/",  # noqa
            auth_views.PasswordResetConfirmView.as_view(),
            name="password_reset_confirm",
        ),
        path(
            "reset/done/",
            auth_views.PasswordResetCompleteView.as_view(),
            name="password_reset_complete",
        ),
        path(
            "terms_of_service/teachers/",
            views.terms_teacher,
            name="terms_teacher",
        ),
        path("access_denied/", views.access_denied, name="access_denied"),
        path(
            "access_denied_and_logout/",
            views.access_denied_and_logout,
            name="access_denied_and_logout",
        ),
        # Blink
        path(
            "blink/<int:pk>/",
            views.BlinkQuestionFormView.as_view(),
            name="blink-question",
        ),
        path(
            "blink/<int:pk>/summary/",
            views.BlinkQuestionDetailView.as_view(),
            name="blink-summary",
        ),
        path("blink/<int:pk>/count/", views.blink_count, name="blink-count",),
        path("blink/<int:pk>/close/", views.blink_close, name="blink-close",),
        path(
            "blink/<int:pk>/latest_results/",
            views.blink_latest_results,
            name="blink-results",
        ),
        path("blink/<int:pk>/reset/", views.blink_reset, name="blink-reset",),
        path(
            "blink/<int:pk>/status/", views.blink_status, name="blink-status",
        ),
        path(
            "blink/<username>/",
            views.blink_get_current,
            name="blink-get-current",
        ),
        path(
            "blink/<username>/url/",
            cache_page(1)(views.blink_get_current_url),
            name="blink-get-current-url",
        ),
        path(
            "blink/<int:pk>/get_next/",
            views.blink_get_next,
            name="blink-get-next",
        ),
        path(
            "blink/waiting/<username>/",
            views.blink_waiting,
            name="blink-waiting",
        ),
        path(
            "blink/waiting/<username>/<int:assignment>/",
            views.blink_waiting,
            name="blink-waiting",
        ),
        path(
            "blinkAssignment/create/",
            views.BlinkAssignmentCreate.as_view(),
            name="blinkAssignment-create",
        ),
        path(
            "blinkAssignment/<int:pk>/delete/",
            views.blink_assignment_delete,
            name="blinkAssignment-delete",
        ),
        path(
            "blinkAssignment/<int:pk>/set_time/",
            views.blink_assignment_set_time,
            name="blinkAssignment-set-time",
        ),
        path(
            "blinkAssignment/<int:pk>/start/",
            views.blink_assignment_start,
            name="blinkAssignment-start",
        ),
        path(
            "blinkAssignment/<int:pk>/update/",
            views.BlinkAssignmentUpdate.as_view(),
            name="blinkAssignment-update",
        ),
    ]


def group_patterns():
    return [
        path(
            "group/student-information/",
            views.group.get_student_reputation,
            name="group-details--student-information",
        ),
        path(
            "group/<group_hash>/",
            views.group_details_page,
            name="group-details",
        ),
        path(
            "group/<group_hash>/update/",
            views.group_details_update,
            name="group-details-update",
        ),
        path(
            "group/connect-course",
            views.connect_group_to_course,
            name="connect-group-course",
        ),
        path(
            "group/disconnect-course",
            views.disconnect_group_from_course,
            name="disconnect-group-course",
        ),
        path(
            "group-assignment/<assignment_hash>/",
            views.group_assignment_page,
            name="group-assignment",
        ),
        path(
            "group-assignment/<assignment_hash>/remove/",
            views.group_assignment_remove,
            name="group-assignment-remove",
        ),
        path(
            "group-assignment/<assignment_hash>/update/",
            views.group_assignment_update,
            name="group-assignment-update",
        ),
        path(
            "group-assignment/<assignment_hash>/send/",
            views.send_student_assignment,
            name="send-student-assignment",
        ),
        path(
            "group-assignment/<assignment_hash>/student-progress/",  # noqa
            views.get_assignment_student_progress,
            name="get-assignment-student-progress",
        ),
        path(
            "group-assignment/<assignment_hash>/distribute/",
            views.distribute_assignment,
            name="distribute-assignment",
        ),
        path(
            "group/review/<int:pk>",
            views.student.StudentGroupReviewDetailView.as_view(),
            name="group-review",
        ),
    ]


def student_patterns():
    return [
        path(
            "assignment-complete/",
            views.finish_assignment,
            name="finish-assignment",
        ),
        path("student/", views.student.index_page, name="student-page"),
        path(
            "student/join-group/",
            views.student.join_group,
            name="student-join-group",
        ),
        path(
            "student/leave-group/",
            views.student.leave_group,
            name="student-leave-group",
        ),
        path(
            "student/toggle-group-notifications/",
            views.student.toggle_group_notifications,
            name="student-toggle-group-notifications",
        ),
        path("student/login/", views.student.login_page, name="student-login"),
        path(
            "student/login-confirm/",
            views.student.send_signin_link,
            name="student-send-signin-link",
        ),
        path(
            "student/remove-notification/",
            views.student.remove_notification,
            name="student-remove-notification",
        ),
        path(
            "student/remove-notifications/",
            views.student.remove_notifications,
            name="student-remove-notifications",
        ),
        path(
            "student/get-notifications/",
            views.student.get_notifications,
            name="student-get-notifications",
        ),
        path(
            "student/update/student-id/",
            views.student.update_student_id,
            name="student-change-id",
        ),
    ]


def search_patterns():
    return [
        path("search/user", views.search_users, name="search-users"),
        path(
            "search/category",
            views.search_categories,
            name="search-categories",
        ),
        path(
            "search/username", views.search_usernames, name="search-usernames",
        ),
        path("search/subject", views.search_subjects, name="search-subjects",),
        path(
            "search/discipline",
            views.search_disciplines,
            name="search-disciplines",
        ),
    ]


def researcher_patterns():
    return [
        path("research/", views.research_index, name="research-index"),
        path(
            "research/discipline/<discipline_title>",
            views.research_discipline_question_index,
            name="research-discipline-question-index-by-discipline",
        ),
        path(
            "research/assignment/<assignment_id>",
            views.research_discipline_question_index,
            name="research-assignment-question-index-by-assignment",
        ),
        path(
            "research/all_scores/discipline/<discipline_title>/<int:question_pk>",  # noqa
            views.research_all_annotations_for_question,
            name="research-all-annotations-for-question-by-discipline",
        ),
        path(
            "research/all_scores/assignment/<assignment_id>/<int:question_pk>",  # noqa
            views.research_all_annotations_for_question,
            name="research-all-annotations-for-question-by-assignment",
        ),
        path(
            "research/discipline/<discipline_title>/<int:question_pk>/<answerchoice_value>",  # noqa
            views.research_question_answer_list,
            name="research-question-answer-list-by-discipline",
        ),
        path(
            "research/assignment/<assignment_id>/<int:question_pk>/<answerchoice_value>",  # noqa
            views.research_question_answer_list,
            name="research-question-answer-list-by-assignment",
        ),
        path(
            "research/question/flag/discipline/<discipline_title>/<int:question_pk>",  # noqa
            views.flag_question_form,
            name="research-flag-question-by-discipline",
        ),
        path(
            "research/question/flag/assignment/<assignment_id>/<int:question_pk>",  # noqa
            views.flag_question_form,
            name="research-flag-question-by-assignment",
        ),
        path(
            "expert/rationales/<int:question_id>",
            admin_views.QuestionExpertRationaleView.as_view(),
            name="research-fix-expert-rationale",
        ),
        path(
            "research/assignment/<assignment_id>/expert/rationale/<int:question_id>",  # noqa
            admin_views.QuestionExpertRationaleView.as_view(),
            name="research-fix-expert-rationale",
        ),
        path(
            "research/expert/rationale/fix/<int:pk>",
            views.AnswerExpertUpdateView.as_view(),
            name="research-rationale-update-expert",
        ),
    ]


def collection_patterns():
    return [
        path(
            "collection-paginate/",
            views.collection_paginate,
            name="collection-paginate",
        ),
        path(
            "collection/create/",
            views.CollectionCreateView.as_view(),
            name="collection-create",
        ),
        path(
            "collection/<int:pk>",
            views.CollectionDetailView.as_view(),
            name="collection-detail",
        ),
        path(
            "collection/update/<int:pk>",
            views.CollectionUpdateView.as_view(),
            name="collection-update",
        ),
        path(
            "collection/delete/<int:pk>",
            views.CollectionDeleteView.as_view(),
            name="collection-delete",
        ),
        path(
            "collection/list/",
            views.CollectionListView.as_view(),
            name="collection-list",
        ),
        path(
            "collection/personal/",
            views.PersonalCollectionListView.as_view(),
            name="personal-collection-list",
        ),
        path(
            "collection/followed/",
            views.FollowedCollectionListView.as_view(),
            name="followed-collection-list",
        ),
        path(
            "collection/featured/",
            views.FeaturedCollectionListView.as_view(),
            name="featured-collection-list",
        ),
        path(
            "collection/distribute/<int:pk>",
            views.CollectionDistributeDetailView.as_view(),
            name="collection-distribute",
        ),
        path(
            "collection/follower",
            views.teacher_toggle_follower,
            name="teacher-toggle-follower",
        ),
        path(
            "collection/assignment",
            views.collection_toggle_assignment,
            name="collection-toggle-assignment",
        ),
        path(
            "collection/add/assignment",
            views.collection_add_assignment,
            name="collection-add-assignment",
        ),
        path(
            "collection/assign",
            views.collection_assign,
            name="collection-assign",
        ),
        path(
            "collection/unassign",
            views.collection_unassign,
            name="collection-unassign",
        ),
        path(
            "collection/collection-statistics",
            views.collection_statistics,
            name="collection-statistics",
        ),
        path(
            "collection/featured-data/",
            views.featured_collections,
            name="collection-featured-data",
        ),
    ]


def teacher_patterns():
    return [
        path(
            "teacher/dashboard/",
            views.teacher.dashboard,
            name="teacher-dashboard",
        ),
        path(
            "teacher/dashboard/new-questions/",
            views.teacher.new_questions,
            name="teacher-dashboard--new-questions",
        ),
        path(
            "teacher/dashboard/rationales/evaluate",
            views.teacher.evaluate_rationale,
            name="teacher-dashboard--evaluate-rationale",
        ),
        path(
            "teacher/dashboard/rationales/",
            views.teacher.rationales_to_score,
            name="teacher-dashboard--rationales",
        ),
        path(
            "teacher/dashboard/collections/",
            views.teacher.collections,
            name="teacher-dashboard--collections",
        ),
        path(
            "teacher/dashboard/messages/",
            views.teacher.messages,
            name="teacher-dashboard--messages",
        ),
        path(
            "teacher/dashboard/dalite-messages/",
            views.teacher.dalite_messages,
            name="teacher-dashboard--dalite-messages",
        ),
        path(
            "teacher/dashboard/dalite-messages/remove",
            views.teacher.remove_dalite_message,
            name="teacher-dashboard--dalite-messages--remove",
        ),
        path(
            "teacher/dashboard/messages/read",
            views.teacher.mark_message_read,
            name="teacher-dashboard--messages--read",
        ),
        path(
            "teacher/dashboard/unsubscribe-thread/",
            views.teacher.unsubscribe_from_thread,
            name="teacher-dashboard--unsubscribe-thread",
        ),
        path(
            "teacher/gradebook/request/",
            views.teacher.request_gradebook,
            name="teacher-gradebook--request",
        ),
        path(
            "teacher/gradebook/result/",
            views.teacher.get_gradebook_task_result,
            name="teacher-gradebook--result",
        ),
        path(
            "teacher/gradebook/remove/",
            views.teacher.remove_gradebook_task,
            name="teacher-gradebook--remove",
        ),
        path(
            "teacher/gradebook/download/",
            views.teacher.download_gradebook,
            name="teacher-gradebook--download",
        ),
        path("teacher/tasks/", views.teacher.get_tasks, name="teacher-tasks"),
    ]


def question_patterns():
    return [
        path(
            "question/flag/reasons",
            views.question_.get_flag_question_reasons,
            name="question--flag--reasons",
        ),
        path(
            "question/flag/flag",
            views.question_.flag_question,
            name="question--flag--flag",
        ),
    ]


def dev_admin_patterns() -> List[URLPattern]:
    return [
        path("admin/", views.admin_.index, name="index"),
        path(
            "admin/dev",
            include(
                [
                    path(
                        "",
                        admin_views.AdminIndexView.as_view(),
                        name="admin-index",
                    ),
                    path(
                        "peerinst/",
                        include(
                            [
                                path(
                                    "assignment_results/<assignment_id>/",
                                    include(
                                        [
                                            path(
                                                "",
                                                admin_views.AssignmentResultsView.as_view(),  # noqa
                                                name="assignment-results",
                                            ),
                                            path(
                                                "rationales/<int:question_id>",
                                                admin_views.QuestionRationaleView.as_view(),  # noqa
                                                name="question-rationales",
                                            ),
                                        ]
                                    ),
                                ),
                                path(
                                    "question_preview/<int:question_id>",
                                    admin_views.QuestionPreviewView.as_view(),
                                    name="question-preview",
                                ),
                                path(
                                    "fake_usernames/",
                                    admin_views.FakeUsernames.as_view(),
                                    name="fake-usernames",
                                ),
                                path(
                                    "fake_countries/",
                                    admin_views.FakeCountries.as_view(),
                                    name="fake-countries",
                                ),
                                path(
                                    "attribution_analysis/",
                                    admin_views.AttributionAnalysis.as_view(),
                                    name="attribution-analysis",
                                ),
                                path(
                                    "group_assignment_management/",
                                    admin_views.StudentGroupAssignmentManagement.as_view(),  # noqa
                                    name="group-assignment-management",
                                ),
                            ]
                        ),
                    ),
                ]
            ),
        ),
    ]


def saltise_admin_patterns() -> List[URLPattern]:
    return [
        path(
            "admin/saltise/",
            include(
                (
                    [
                        path(
                            "",
                            staff_member_required(views.admin_.saltise_index),
                            name="index",
                        ),
                        path(
                            "group-assignment-management/",
                            staff_member_required(
                                admin_views.StudentGroupAssignmentManagement.as_view()  # noqa
                            ),
                            name="group-assignment-management",
                        ),
                        path(
                            "new-user-approval",
                            staff_member_required(
                                views.admin_.new_user_approval_page
                            ),
                            name="new-user-approval",
                        ),
                        path(
                            "verify-user",
                            staff_member_required(views.admin_.verify_user),
                            name="verify-user",
                        ),
                        path(
                            "flagged-rationales",
                            staff_member_required(
                                views.admin_.flagged_rationales_page
                            ),
                            name="flagged-rationales",
                        ),
                        path(
                            "get-flagged-rationales",
                            staff_member_required(
                                views.admin_.get_flagged_rationales
                            ),
                            name="get-flagged-rationales",
                        ),
                        path(
                            "activity",
                            staff_member_required(views.admin_.activity_page),
                            name="activity",
                        ),
                        path(
                            "get-groups-activity",
                            staff_member_required(
                                views.admin_.get_groups_activity
                            ),
                            name="get-groups-activity",
                        ),
                    ],
                    "saltise-admin",
                ),
                namespace="saltise-admin",
            ),
        )
    ]


urlpatterns: List[URLPattern] = sum(
    [
        collection_patterns(),
        group_patterns(),
        old_patterns(),
        question_patterns(),
        researcher_patterns(),
        search_patterns(),
        student_patterns(),
        teacher_patterns(),
        dev_admin_patterns(),
        saltise_admin_patterns(),
    ],
    [],
)
