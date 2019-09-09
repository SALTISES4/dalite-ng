import random

from peerinst import models
from ..question.test_question import QuestionTestCase


class MetaSearchTests(QuestionTestCase):
    N_questions = 10
    N_answers = 10
    N_choices = 5
    N_correct = 1

    def setUp(self):
        super(MetaSearchTests, self).setUp()
        """ Add meta features to objects """
        easy = models.MetaFeature.objects.create(
            key="difficulty", type="S", value="easy"
        )
        hard = models.MetaFeature.objects.create(
            key="difficulty", type="S", value="hard"
        )
        low = models.MetaFeature.objects.create(key="rank", type="I", value=1)
        high = models.MetaFeature.objects.create(key="rank", type="I", value=6)

        self.difficulty_choices = [easy, hard]
        self.rank_choices = [low, high]

        for q in models.Question.objects.all():
            s = models.MetaSearch.objects.create(
                meta_feature=random.choice(self.difficulty_choices),
                content_object=q,
            )
            q.meta_search.add(s)
            s = models.MetaSearch.objects.create(
                meta_feature=random.choice(self.rank_choices), content_object=q
            )
            q.meta_search.add(s)

    def test_meta_search(self):
        for q in models.Question.objects.all():
            for s in q.meta_search.all():
                print(s)

        easy_low_questions = models.Question.objects.filter(
            meta_search__meta_feature__key="difficulty",
            meta_search__meta_feature__value="easy",
        ).filter(
            meta_search__meta_feature__key="rank",
            meta_search__meta_feature__value__lt=2,
        )

        for q in easy_low_questions.all():
            print(q)
            assert (
                q.meta_search.get(
                    meta_feature__key="difficulty"
                ).meta_feature.get_value
                == "easy"
            )
            assert (
                q.meta_search.get(
                    meta_feature__key="rank"
                ).meta_feature.get_value
                < 2
            )

        # Update difficulty and check only latest kept
        tricky = models.MetaFeature.objects.create(
            key="difficulty", type="S", value="tricky"
        )
        for q in models.Question.objects.all():
            s = models.MetaSearch.objects.create(
                meta_feature=tricky, content_object=q
            )
            q.meta_search.add(s)

        for q in models.Question.objects.all():
            for s in q.meta_search.all():
                print(s)

        easy_low_questions = models.Question.objects.filter(
            meta_search__meta_feature__key="difficulty",
            meta_search__meta_feature__value="easy",
        ).filter(
            meta_search__meta_feature__key="rank",
            meta_search__meta_feature__value__lt=2,
        )

        tricky_high_questions = models.Question.objects.filter(
            meta_search__meta_feature__key="difficulty",
            meta_search__meta_feature__value="tricky",
        ).filter(
            meta_search__meta_feature__key="rank",
            meta_search__meta_feature__value__gt=3,
        )

        assert easy_low_questions.count() == 0
        assert models.MetaSearch.objects.count() == 2 * self.N_questions
        for q in tricky_high_questions.all():
            print(q)
            assert (
                q.meta_search.get(
                    meta_feature__key="difficulty"
                ).meta_feature.get_value
                == "tricky"
            )
            assert (
                q.meta_search.get(
                    meta_feature__key="rank"
                ).meta_feature.get_value
                > 3
            )
