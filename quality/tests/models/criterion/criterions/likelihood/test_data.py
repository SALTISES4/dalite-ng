from quality.models.criterion.criterions.likelihood.data import read_data


def test_read_data__english():
    urls = [
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "english_monograms.txt",
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "english_bigrams_1.txt",
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "english_trigrams.txt.zip",
    ]
    data = read_data("english", urls, True)
    assert len(data["n_grams"]) == 3
    assert 1 in data["n_grams"]
    assert 2 in data["n_grams"]
    assert 3 in data["n_grams"]
    assert len(data["n_grams"][1]) == 26
    assert len(data["n_grams"][2]) == 26**2
    assert len(data["n_grams"][3]) == 26**3
    assert abs(1 - sum(data["n_grams"][1].values())) < 1e-5
    assert abs(1 - sum(data["n_grams"][2].values())) < 1e-5
    assert abs(1 - sum(data["n_grams"][3].values())) < 1e-5
    assert data["left_to_right"]


def test_read_data__french():
    urls = [
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "french_monograms.txt",
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "french_bigrams.txt",
        "http://practicalcryptography.com/media/cryptanalysis/files/"
        "french_trigrams.txt.zip",
    ]
    data = read_data("french", urls, True)
    assert len(data["n_grams"]) == 3
    assert 1 in data["n_grams"]
    assert 2 in data["n_grams"]
    assert 3 in data["n_grams"]
    assert len(data["n_grams"][1]) == 42
    assert len(data["n_grams"][2]) == 42**2
    assert len(data["n_grams"][3]) == 42**3
    assert abs(1 - sum(data["n_grams"][1].values())) < 1e-5
    assert abs(1 - sum(data["n_grams"][2].values())) < 1e-5
    assert abs(1 - sum(data["n_grams"][3].values())) < 1e-5
    assert data["left_to_right"]
