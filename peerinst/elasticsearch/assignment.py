import logging
import pprint
import time

from elasticsearch_dsl import Q

from peerinst.documents import AssignmentDocument

logger = logging.getLogger("performance")
pp = pprint.PrettyPrinter()


def assignment_search(search_string, filters=None):
    start = time.perf_counter()

    q = Q(
        "multi_match",
        query=search_string,
        fields=[
            "title^2",
            "description",
        ],
    ) | Q(
        "nested",
        path="owner",
        query=Q("match", owner__username=search_string),
    )

    s = (
        AssignmentDocument.search()
        .sort("_score", "-answer_count")
        .query("function_score", **{"query": q})
    )

    end = time.perf_counter()

    logger.info(
        f"Assignment ElasticSearch time to query '{search_string}': {end - start:E}s"  # noqa E501
    )
    logger.info(f"Hit count: {s.count()}")

    for i, hit in enumerate(s):
        if i == 0:
            logger.debug(f"Top result: \n{pp.pformat(hit.to_dict())}")

        logger.debug(f"Score {i+1}: {hit.meta.score} | #{hit.pk}")

    return s
