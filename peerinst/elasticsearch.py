import logging
import pprint
import time

from elasticsearch_dsl import Q

from peerinst.documents import QuestionDocument

logger = logging.getLogger("performance")
pp = pprint.PrettyPrinter()


def question_search(search_string, filters=None, flagged=None):

    if filters is None:
        filters = []
    if flagged is None:
        flagged = []

    start = time.perf_counter()

    q = (
        Q(
            "multi_match",
            query=search_string,
            fields=[
                "discipline.title",
                "pk",
                "text^2",
                "title^3",
                "user.username",
            ],
        )
        | Q(
            "nested",
            path="category",
            query=Q("match", category__title=search_string),
        )
        | Q(
            "nested",
            path="collaborators",
            query=Q("match", collaborators__username=search_string),
        )
        | Q(
            "nested",
            path="answerchoice_set",
            query=Q("match", answerchoice_set__text=search_string),
        )
    )

    s = (
        QuestionDocument.search()
        .sort("_score")
        .query(
            "function_score",
            **{
                "query": q,
                "functions": [
                    {
                        "field_value_factor": {
                            "field": "assignment_count",
                            "modifier": "log1p",
                        }
                    },
                    {
                        "field_value_factor": {
                            "field": "featured",
                            "modifier": "none",
                            "factor": 1.1,
                        }
                    },
                ],
            },
        )
        .exclude("term", valid=False)
        .exclude("term", deleted=True)
        .exclude("terms", pk=flagged)
    )

    if filters:
        for f in filters:
            if "__" in f[0]:
                # Nested
                s = s.filter(
                    Q(
                        "nested",
                        path="category",
                        query=Q("match", **{f[0]: f[1]}),
                    )
                )
            else:
                s = s.filter("term", **{f[0]: f[1]})

    end = time.perf_counter()

    logger.info(
        f"ElasticSearch time to query '{search_string}' with filters '{filters}': {end - start:E}s"  # noqa E501
    )
    logger.info(f"Hit count: {s.count()}")

    for i, hit in enumerate(s):
        if i == 0:
            logger.debug(f"Top result: \n{pp.pformat(hit.to_dict())}")

        logger.debug(f"Score {i+1}: {hit.meta.score} | #{hit.pk}")

    return s
