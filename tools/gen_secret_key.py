#!/usr/bin/env python
"""
Simple script to generate a secret key that you can put into local_settings.py.
"""

import random
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        key_length = int(sys.argv[1])
    else:
        key_length = 50
    urandom = random.SystemRandom()
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    key = "".join(urandom.choice(chars) for i in range(key_length))
    print(f"SECRET_KEY = {repr(key)}")
