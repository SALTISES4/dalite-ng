import random
import string
import time
from datetime import timedelta

from django.test import TestCase

from peerinst.utils import create_token, verify_token


class TestTokens(TestCase):
    def test_token(self):
        payloads = [
            {
                _random_string(): _random_string()
                for _ in range(random.randint(1, 5))
            }
            for _ in range(5)
        ]
        for payload in payloads:
            payload_, err = verify_token(create_token(payload))
            self.assertIs(err, None)
            for k, v in list(payload.items()):
                self.assertEqual(v, payload_[k])

    def test_token_expired(self):
        payload = {_random_string(): _random_string()}
        token = create_token(payload, exp=timedelta(microseconds=1))
        time.sleep(1)
        payload_, err = verify_token(token)
        self.assertIs(payload_, None)
        self.assertEqual(err, "Token expired")


def _random_string(length=10):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))
