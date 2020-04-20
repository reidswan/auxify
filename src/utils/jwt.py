from jwcrypto import jwt, jwk
import ujson
from typing import Dict
from datetime import datetime, timedelta
from enum import Enum

TOKEN_DURATION: timedelta = timedelta(hours=24)


def key_from_secret(secret: str) -> jwk.JWK:
    return jwk.JWK.from_json(ujson.dumps({
        "k": secret,
        "kty": "oct"
    }))


class Aud(Enum):
    AUTH: str = "auth"
    API: str = "api"


def generate_jwt(user_id: int, aud: Aud, key: jwk.JWK) -> str:
    claims= {
        'sub': str(user_id),
        'nbf': datetime.now().timestamp(),
        'exp': (datetime.now() + TOKEN_DURATION).timestamp(),
        'aud': aud.value
    }

    token = jwt.JWT(
        header={'alg': 'HS256'},
        claims=claims,
    )
    token.make_signed_token(key)
    return token.serialize()


def get_claims_from_jwt(token: str, key: jwk.JWK, expected_aud: Aud) -> Dict:
    """ raises Exception if JWT missing """
    claims = ujson.loads(jwt.JWT(
        key=key,
        jwt=token,
        # None-value means check that claim exists
        check_claims={'exp': None, 'sub': None, 'aud': None}).claims)

    if not claims.get('aud') or claims['aud'] != expected_aud.value:
        raise jwt.JWTInvalidClaimValue("Expected aud to be %s" % expected_aud.value)
    return claims
