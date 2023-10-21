import logging
import pprint
import time

from elasticsearch_dsl import Q

from peerinst.documents import CollectionDocument

logger = logging.getLogger("performance")
pp = pprint.PrettyPrinter()


def collection_search(search_string, filters=None):
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
        path="user",
        query=Q("match", user__username=search_string),
    )

    s = (
        CollectionDocument.search()
        .filter("term", public=True)
        .sort("_score")
        .query("function_score", **{"query": q})
    )

    end = time.perf_counter()

    logger.info(
        f"Collection ElasticSearch time to query '{search_string}': {end - start:E}s"  # noqa E501
    )
    logger.info(f"Hit count: {s.count()}")

    for i, hit in enumerate(s):
        if i == 0:
            logger.debug(f"Top result: \n{pp.pformat(hit.to_dict())}")

        logger.debug(f"Score {i+1}: {hit.meta.score} | #{hit.pk}")

    return s
