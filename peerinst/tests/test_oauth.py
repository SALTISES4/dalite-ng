import binascii
import hmac
import time
from hashlib import sha1


def test_oauth_signature(client, settings):
    """
    See:
    https://oauth1.wp-api.org/docs/basics/Signing.html
    https://github.com/joestump/python-oauth2/blob/release/1.9/oauth2/__init__.py
    """

    settings.LTI_CLIENT_KEY = "abcd"  # The consumer key
    settings.LTI_CLIENT_SECRET = "1234"  # The consumer secret

    oauth_parameters = {
        "lti_version": "1.0",
        "lti_message_type": "basic-lti-message",
        "user_id": "test",
        "custom_assignment_id": "test-assignment",
        "custom_question_id": "1",
        "oauth_consumer_key": settings.LTI_CLIENT_KEY,
        "oauth_nonce": "nonce",
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        #  "oauth_timestamp": "1578323651",
    }

    # Build oauth base string
    # - Must be url encoded
    # - Must start with uppercase http method
    # - Must be followed by lowercase url, no port if 80 or 443
    # - Must be followed by request parameters, alphabetical by keys,
    #   excluding oauth_signature, concatenated with &
    base_string = (
        "POST&http%3A%2F%2Ftestserver%2Flti%2F&"
        + "custom_assignment_id%3D"
        + oauth_parameters["custom_assignment_id"]
        + "%26custom_question_id%3D"
        + oauth_parameters["custom_question_id"]
        + "%26lti_message_type%3D"
        + oauth_parameters["lti_message_type"]
        + "%26lti_version%3D"
        + oauth_parameters["lti_version"]
        + "%26oauth_consumer_key%3D"
        + oauth_parameters["oauth_consumer_key"]
        + "%26oauth_nonce%3D"
        + oauth_parameters["oauth_nonce"]
        + "%26oauth_signature_method%3D"
        + oauth_parameters["oauth_signature_method"]
        + "%26oauth_timestamp%3D"
        + oauth_parameters["oauth_timestamp"]
        + "%26user_id%3D"
        + oauth_parameters["user_id"]
    )

    # Build oauth signature from basestring and consumer secret (no token here)
    key = settings.LTI_CLIENT_SECRET + "&"

    hashed = hmac.new(key.encode(), base_string.encode(), sha1)
    oauth_signature = binascii.b2a_base64(hashed.digest())[:-1].decode()

    oauth_parameters.update({"oauth_signature": oauth_signature})

    response = client.post("/lti/", oauth_parameters, follow=True)

    assert (
        response.status_code == 404
    )  # Assignment does not exist, but oauth protocol succeeds
