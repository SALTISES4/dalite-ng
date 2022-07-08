from django.db import models
from django.utils.translation import ugettext_lazy as _

from peerinst.models import Question, Teacher


class BlinkQuestion(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.CASCADE)
    current = models.BooleanField(default=True)
    active = models.BooleanField(default=False)
    time_limit = models.PositiveSmallIntegerField(_("Time limit"), null=True)
    key = models.CharField(unique=True, max_length=8, primary_key=True)

    def __str__(self):
        return self.question.text

    def save(self, *args, **kwargs):
        self.question.second_answer_needed = False
        self.question.save()
        super().save(*args, **kwargs)


class BlinkRound(models.Model):
    question = models.ForeignKey(BlinkQuestion, on_delete=models.CASCADE)
    activate_time = models.DateTimeField()
    deactivate_time = models.DateTimeField(null=True)


class BlinkAnswer(models.Model):
    question = models.ForeignKey(BlinkQuestion, on_delete=models.CASCADE)
    answer_choice = models.PositiveSmallIntegerField(_("Answer choice"))
    vote_time = models.DateTimeField()
    voting_round = models.ForeignKey(BlinkRound, on_delete=models.CASCADE)


class BlinkAssignment(models.Model):
    title = models.CharField(_("Title"), max_length=200)
    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.CASCADE)
    blinkquestions = models.ManyToManyField(
        BlinkQuestion, through="BlinkAssignmentQuestion"
    )
    key = models.CharField(unique=True, max_length=8)
    active = models.BooleanField(default=False)

    def __str__(self):
        return "{} < {} >".format(
            self.title,
            " ; ".join(
                f"rank {q.rank} - {q.blinkquestion.question.title}"
                for q in self.blinkassignmentquestion_set.all()
            ),
        )

    class Meta:
        verbose_name = _("blink assignment")
        verbose_name_plural = _("blink assignments")


class BlinkAssignmentQuestion(models.Model):
    blinkassignment = models.ForeignKey(
        BlinkAssignment, on_delete=models.CASCADE
    )
    blinkquestion = models.ForeignKey(BlinkQuestion, on_delete=models.CASCADE)
    rank = models.IntegerField()

    # https://djangosnippets.org/snippets/998/
    def move_down_rank(self):
        try:
            next_q = (
                BlinkAssignmentQuestion.objects.filter(
                    blinkassignment__title=self.blinkassignment.title
                )
                .filter(rank__gt=self.rank)
                .first()
            )

            next_rank = next_q.rank
            next_q.rank = self.rank
            next_q.save()
            self.rank = next_rank
            self.save()

        except IndexError:
            pass

        return

    def move_up_rank(self):
        try:
            previous_q = (
                BlinkAssignmentQuestion.objects.filter(
                    blinkassignment__title=self.blinkassignment.title
                )
                .filter(rank__lt=self.rank)
                .last()
            )

            previous_rank = previous_q.rank
            previous_q.rank = self.rank
            previous_q.save()
            self.rank = previous_rank
            self.save()

        except IndexError:
            pass

        return

    def renumber(self):
        try:
            all_q = BlinkAssignmentQuestion.objects.filter(
                blinkassignment__title=self.blinkassignment.title
            ).order_by("rank")

            r = 0
            for q in all_q:
                q.rank = r
                q.save()
                r = r + 1

        except IndexError:
            pass

        return

    def __str__(self):
        return "{} : rank {} - {}-{}".format(
            self.blinkassignment.title,
            self.rank,
            self.blinkquestion.question.id,
            self.blinkquestion.question.title,
        )

    class Meta:
        ordering = ["rank"]
