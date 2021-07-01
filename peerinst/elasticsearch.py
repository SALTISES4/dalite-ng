import logging
import pprint
import time

from elasticsearch_dsl import Q

from peerinst.documents import QuestionDocument

logger = logging.getLogger("performance")
pp = pprint.PrettyPrinter()


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
        .query(q)
        .exclude("term", questionflag_set=True)
        .exclude("term", valid=False)
        .exclude("term", deleted=True)
    )
    end = time.perf_counter()

    logger.info(
        f"ElasticSearch time to query '{search_string}': {end - start:E}s"
    )
    logger.info(f"Hit count: {s.count()}")

    for i, hit in enumerate(s):
        if i == 0:
            logger.debug(f"Top result: \n{pp.pformat(hit.to_dict())}")

        logger.debug(f"Score: {hit.meta.score} | #{hit.id}")

    return s
