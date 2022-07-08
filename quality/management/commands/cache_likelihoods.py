import logging
from datetime import datetime
from itertools import chain, islice

from django.core.management.base import BaseCommand
from django.db.models.functions import Lower

from peerinst.models import Answer
from quality.models import LikelihoodCache, LikelihoodLanguage

logger = logging.getLogger("quality")


class Command(BaseCommand):
    help = (
        "Compute and cache the likelihood for all answer rationales in all "
        "languages."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-gram",
            type=int,
            default=3,
            help="Maximum size of n-grams to use.",
        )
        parser.add_argument(
            "-d", "--discipline", type=str, help="Only cache for discipline"
        )
        parser.add_argument(
            "-b",
            "--batch-size",
            type=int,
            default=64,
            help="Size of batches to use",
        )

    def handle(self, *args, **options):
        discipline = options.get("discipline")
        batch_size = options["batch_size"]

        if discipline is None:
            answers = Answer.objects.all()
        else:
            answers = Answer.objects.annotate(
                discipline_lower=Lower("question__discipline__title")
            ).filter(discipline_lower=discipline.lower())

        n = answers.count() * LikelihoodLanguage.objects.count()

        progress = 0
        current = 0

        for language in LikelihoodLanguage.objects.all().iterator():
            for _answers in batch(answers.iterator(), batch_size):
                likelihoods = LikelihoodCache.batch(
                    _answers, language, options["max_gram"]
                )
                progress = progress + float(len(likelihoods)) / n * 100
                if discipline is None:
                    print(
                        f"{datetime.now()} - ({progress:>6.2f}%) -"
                        + " Computing likelihood for all answers in "
                        + f"{language.language}..."
                    )
                else:
                    print(
                        f"{datetime.now()} - ({progress:>6.2f}%) -"
                        + " Computing likelihood for answers in "
                        + f"discipline {discipline} in {language}..."
                    )


def batch(iterable, size):
    source_iter = iter(iterable)
    while True:
        batch_iter = islice(source_iter, size)
        yield chain([next(batch_iter)], batch_iter)
