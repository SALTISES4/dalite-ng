import logging
import time

from elasticsearch_dsl import Q

from peerinst.documents import QuestionDocument

logger = logging.getLogger("performance")


def question_search(search_string):

    start = time.perf_counter()

    q = (
        Q(
            "multi_match",
            query=search_string,
            fields=[
                "discipline.title",
                "id",
                "text",
                "title",
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
        .query(q)
        .exclude("term", questionflag_set=True)
        .exclude("term", valid=False)
    )
    end = time.perf_counter()

    logger.info(
        f"ElasticSearch time to query '{search_string}': {end - start:E}s"
    )
    logger.info(f"Hit count: {s.count()}")

    for hit in s:
        logger.info(f"Score: {hit.meta.score} | #{hit.id}")

    return s
