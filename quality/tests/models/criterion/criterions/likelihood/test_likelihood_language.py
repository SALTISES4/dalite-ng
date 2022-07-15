from quality.models.criterion import LikelihoodLanguage


def test_str():
    for language in ("english", "french"):
        assert (
            str(LikelihoodLanguage.objects.get(language=language)) == language
        )
