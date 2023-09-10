from elasticsearch_dsl import analyzer, token_filter, tokenizer

html_strip = analyzer(
    "html_strip",
    tokenizer="whitespace",
    filter=["lowercase", "stop", "snowball"],
    char_filter=["html_strip"],
)

full_term = analyzer("full_term", tokenizer="keyword", filter=["lowercase"])

autocomplete = analyzer(
    "autocomplete",
    tokenizer=tokenizer("autocomplete", "edge_ngram", min_gram=3, max_gram=50),
    filter=["lowercase"],
)

trigram_filter = token_filter("ngram", "ngram", min_gram=3, max_gram=5)
trigram = analyzer(
    "trigram", tokenizer="whitespace", filter=["lowercase", trigram_filter]
)
