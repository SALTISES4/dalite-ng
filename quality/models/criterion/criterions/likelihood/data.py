import io
import os
import pickle
import zipfile
from itertools import product

import requests


def read_data(language, urls, left_to_right):
    path = os.path.join(os.path.dirname(__file__), ".data", language)

    pkl_path = os.path.join(path, "data.pkl")

    if os.path.exists(pkl_path):
        with open(pkl_path, "rb") as f:
            data = pickle.load(f)

    else:
        data = {
            gram + 1: read_gram_file(language, gram + 1, url, path)
            for gram, url in enumerate(urls)
        }
        data = {
            gram: {
                "".join(g): val.get("".join(g), 1e-16)
                for g in product(*["".join(list(data[1].keys()))] * gram)
            }
            for gram, val in list(data.items())
        }
        data = {"n_grams": data, "left_to_right": left_to_right}
        with open(pkl_path, "wb") as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

    return data


def read_gram_file(language, gram, url, path):
    path = os.path.join(path, f"{gram}-grams.txt")
    if os.path.exists(path):
        with open(path) as f:
            f.readline()
            lines = [line.strip().split() for line in f]
            data = {line[0]: float(line[1]) for line in lines}
    else:
        data = download_gram_file(language, gram, url, path)

    return data


def download_gram_file(language, gram, url, path):

    resp = requests.get(url)
    resp.raise_for_status()

    if url.endswith("zip"):
        with zipfile.ZipFile(io.BytesIO(resp.content)) as f_zip:
            with f_zip.open(os.path.basename(url)[:-4]) as f:
                lines = [line.strip().split() for line in f]
                data = {
                    line[0].decode().lower(): float(line[1]) for line in lines
                }

    else:
        lines = [
            line.strip().split()
            for line in resp.content.decode("utf-8").split("\n")
            if line
        ]
        data = {line[0].lower(): float(line[1]) for line in lines}

    total = sum(data.values())
    data = {key: val / total for key, val in list(data.items())}

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write("n-gram\tfrequency\n")
        for n_gram, frequency in list(data.items()):
            f.write(f"{n_gram}\t{frequency}\n")

    return data
