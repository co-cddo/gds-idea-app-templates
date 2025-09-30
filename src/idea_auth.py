region = "eu-west-2"
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "a-strong-random-string"
client_id = "56kmmfhi268eqfrcpd2a83kjar"
client_secret = "109ech186fufuu18jio1oa1m9lljrd5h8vq4veinkho4bsur2b1s"
user_pool_id = "eu-west-2_T6nubwfbi"
server_metadata_url = "https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_T6nubwfbi/.well-known/openid-configuration"
# Test with a hardcoded token (replace with your actual token)
test_token = "eyJ0eXAiOiJKV1QiLCJraWQiOiIyMzMzMDhlMS02OWQxLTRkZmQtODQ5MS1lNjExNTk4NGIzZGUiLCJhbGciOiJFUzI1NiIsImlzcyI6Imh0dHBzOi8vY29nbml0by1pZHAuZXUtd2VzdC0yLmFtYXpvbmF3cy5jb20vZXUtd2VzdC0yX1Q2bnVid2ZiaSIsImNsaWVudCI6IjEwMmFjdGl1YzE0ajVsYWdjdDZ1NmdmYXVwIiwic2lnbmVyIjoiYXJuOmF3czplbGFzdGljbG9hZGJhbGFuY2luZzpldS13ZXN0LTI6OTkyMzgyNzIyMzE4OmxvYWRiYWxhbmNlci9hcHAvZHVtcGVyLUxvYWRCLXd5RkNVV0NXMlF4eS9hMWIyZDk5OWFlYmY4MzgwIiwiZXhwIjoxNzU5MjE5NTU1fQ==.eyJzdWIiOiJmNjkyNzJjNC05MDUxLTcwZTAtMWViYi0xYTA2NzRmMjE3Y2EiLCJlbWFpbF92ZXJpZmllZCI6InRydWUiLCJlbWFpbCI6ImRhdmlkLmdpbGxlc3BpZUBkaWdpdGFsLmNhYmluZXQtb2ZmaWNlLmdvdi51ayIsInVzZXJuYW1lIjoiZjY5MjcyYzQtOTA1MS03MGUwLTFlYmItMWEwNjc0ZjIxN2NhIiwiZXhwIjoxNzU5MjE5NTU1LCJpc3MiOiJodHRwczovL2NvZ25pdG8taWRwLmV1LXdlc3QtMi5hbWF6b25hd3MuY29tL2V1LXdlc3QtMl9UNm51YndmYmkifQ==.R5odHbr8tFAa4YQGztDvz9sb1I6mGOQLPxn6J8WR5oq8p-gkbRTE028aInG-qR6dYYeu9zQenjquTyU18KEE8g=="
import json
import os
import time
from functools import lru_cache
from textwrap import indent
from typing import Dict, Optional

import requests
from authlib.integrations.requests_client.oauth2_session import OAuth2Session
from authlib.jose import jwt


class TokenDecoder:
    def __init__(self):
        self.is_development = os.getenv("ENVIRONMENT", "development") == "development"

        # Cognito configuration
        self.region = region
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.client_secret = client_secret

        # Setup OAuth2 session
        self._setup_oauth_session()

    def _setup_oauth_session(self):
        """Setup OAuth2 session with Cognito endpoints"""
        if not self.user_pool_id or not self.client_id:
            if not self.is_development:
                print("Warning: Missing Cognito configuration")
            return

        # Cognito URLs
        self.cognito_domain = (
            f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
        )

        # Create OAuth2 session
        self.oauth = OAuth2Session(
            client_id=self.client_id, client_secret=self.client_secret
        )

        # Fetch server metadata (endpoints, JWKs URL, etc.)
        self._fetch_server_metadata()

    def _fetch_server_metadata(self):
        """Fetch OIDC server metadata from Cognito"""
        try:
            # https://cognito-idp.eu-west-2.amazonaws.com/eu-west-2_T6nubwfbi/.well-known/jwks.json
            metadata_url = f"{self.cognito_domain}/.well-known/openid-configuration"
            response = requests.get(metadata_url, timeout=10)
            response.raise_for_status()
            self.server_metadata = response.json()

            # Extract useful endpoints
            self.jwks_uri = self.server_metadata.get("jwks_uri")
            self.issuer = self.server_metadata.get("issuer")
            self.token_endpoint = self.server_metadata.get("token_endpoint")

            print(f"✅ Loaded server metadata from {metadata_url}")

        except Exception as e:
            print(f"Failed to fetch server metadata: {e}")
            self.server_metadata = {}

    @lru_cache(maxsize=1)
    def _get_jwks(self) -> Dict:
        """Get JWKs using the metadata"""
        if not hasattr(self, "jwks_uri") or not self.jwks_uri:
            print("No JWKs URI available")
            return {"keys": []}

        try:
            response = requests.get(self.jwks_uri, timeout=10)
            response.raise_for_status()
            print(response.json)
            return response.json()
        except Exception as e:
            print(f"Failed to fetch JWKs: {e}")
            return {"keys": []}

    def decode_token(self, token: str) -> Optional[Dict]:
        """Decode and validate JWT token"""
        if self.is_development:
            # Development mode - just decode without verification
            try:
                return jwt.decode(token, key=self._get_jwks())
            except Exception as e:
                print(f"Development: Failed to decode token: {e}")
                return None

        if not hasattr(self, "oauth"):
            print("OAuth session not configured")
            return None

        try:
            # Use OAuth2Session's built-in token validation
            # This automatically handles JWKs fetching and signature verification
            claims = self.oauth.parse_id_token(token, self.server_metadata)

            return dict(claims)

        except Exception as e:
            print(f"Token validation failed: {e}")
            return None

    def introspect_token(self, token: str) -> Optional[Dict]:
        """Use OAuth2 token introspection if supported"""
        if not hasattr(self, "server_metadata"):
            print("Server metadata not available")
            return None

        introspect_endpoint = self.server_metadata.get("introspection_endpoint")
        if not introspect_endpoint:
            print("Token introspection not supported by server")
            return None

        try:
            # Use OAuth2Session to introspect token
            response = self.oauth.introspect_token(introspect_endpoint, token)
            return response
        except Exception as e:
            print(f"Token introspection failed: {e}")
            return None

    def get_server_info(self) -> Dict:
        """Get information about the OAuth server"""
        if not hasattr(self, "server_metadata"):
            return {}

        return {
            "issuer": self.server_metadata.get("issuer"),
            "jwks_uri": self.server_metadata.get("jwks_uri"),
            "token_endpoint": self.server_metadata.get("token_endpoint"),
            "userinfo_endpoint": self.server_metadata.get("userinfo_endpoint"),
            "supported_scopes": self.server_metadata.get("scopes_supported", []),
            "supported_response_types": self.server_metadata.get(
                "response_types_supported", []
            ),
            "supported_algorithms": self.server_metadata.get(
                "id_token_signing_alg_values_supported", []
            ),
        }


import base64
import json


def decode_jwt_payload(token: str) -> dict:
    """
    Decodes the payload of a JWT token without signature verification.
    WARNING: Do not use this for security-sensitive operations.
    """
    try:
        # JWT parts are separated by a period.
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # The payload is the second part.
        payload_encoded = parts[1]

        # Base64Url decode the payload.
        # Note: Base64Url uses hyphens and underscores instead of pluses and slashes,
        # and has no padding. We need to handle this.
        payload_decoded_bytes = base64.urlsafe_b64decode(payload_encoded + "==")

        # Decode the bytes to a string and parse as JSON.
        payload_json = payload_decoded_bytes.decode("utf-8")
        payload = json.loads(payload_json)

        return payload

    except (ValueError, IndexError, json.JSONDecodeError) as e:
        print(f"Error decoding token: {e}")
        return {}


# Simple test
if __name__ == "__main__":
    claims = decode_jwt_payload(test_token)
    print(json.dumps(claims, indent=2))
    # Initialize decoder
    decoder = TokenDecoder()

    # Show server info
    print("🔍 Server Information:")
    server_info = decoder.get_server_info()
    for key, value in server_info.items():
        print(f"  {key}: {value}")
    print()

    # Decode the token
    print("🔓 Decoding token...")
    claims = decoder.decode_token(test_token)
    print(f"Claims {json.dumps(claims, indent=2)}")

    if claims:
        print("✅ Token decoded successfully!")
        print(f"Subject: {claims.get('sub')}")
        print(f"Email: {claims.get('email')}")
        print(f"Groups: {claims.get('cognito:groups', [])}")
        print(f"Expires: {claims.get('exp')}")
        print(f"Token type: {claims.get('token_use')}")

        # Try introspection if available
        print("\n🔍 Trying token introspection...")
        introspect_result = decoder.introspect_token(test_token)
        if introspect_result:
            print(f"Introspection result: {introspect_result}")

    else:
        print("❌ Failed to decode token")
