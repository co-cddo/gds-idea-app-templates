"""
Test script for AWS ALB Cognito User Library

Usage:
    1. Create a file called 'test_tokens.txt' with the following format:

    OIDC_DATA=<paste x-amzn-oidc-data value here>
    ACCESS_TOKEN=<paste x-amzn-oidc-accesstoken value here>
    REGION=eu-west-2

    2. Run: python test_alb_user.py
"""

import os

from cognito_user import ExpiredTokenError, InvalidTokenError, MissingTokenError, User


def load_tokens_from_file(filename="./test_tokens.txt"):
    """Load tokens from a configuration file"""
    if not os.path.exists(filename):
        return None

    config = {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    return config


def test_user_library():
    """Interactive test for the User library"""

    print("=" * 70)
    print("AWS ALB Cognito User Library - Test Script")
    print("=" * 70)
    print()

    # Try to load from file first
    config = load_tokens_from_file()

    if config:
        print("✓ Found test_tokens.txt file")
        oidc_data = config.get("OIDC_DATA", "").strip()
        access_token = config.get("ACCESS_TOKEN", "").strip()
        region = config.get("REGION", "eu-west-2").strip()

        if not oidc_data or not access_token:
            print("❌ ERROR: test_tokens.txt is missing OIDC_DATA or ACCESS_TOKEN")
            print()
            print("Please create test_tokens.txt with this format:")
            print()
            print("OIDC_DATA=<your x-amzn-oidc-data value>")
            print("ACCESS_TOKEN=<your x-amzn-oidc-accesstoken value>")
            print("REGION=eu-west-2")
            return
    else:
        print("No test_tokens.txt file found.")
        print()
        print("Please create a file called 'test_tokens.txt' with:")
        print()
        print("OIDC_DATA=<your x-amzn-oidc-data value>")
        print("ACCESS_TOKEN=<your x-amzn-oidc-accesstoken value>")
        print("REGION=eu-west-2")
        print()
        print("This avoids terminal paste issues with long tokens.")
        return

    print(f"✓ Region: {region}")
    print(f"✓ OIDC_DATA length: {len(oidc_data)} characters")
    print(f"✓ ACCESS_TOKEN length: {len(access_token)} characters")
    print()

    print("=" * 70)
    print("Testing token verification and User creation...")
    print("=" * 70)
    print()

    try:
        # Test with verification enabled (default)
        print("🔐 Creating User with token verification enabled...")
        user = User(
            oidc_data_header=oidc_data,
            access_token_header=access_token,
            region=region,
            verify_tokens=True,
        )

        print("✅ SUCCESS! User created and tokens verified.")
        print()
        print("-" * 70)
        print("User Information:")
        print("-" * 70)
        print(f"  Authenticated:    {user.is_authenticated}")
        print(f"  Username:         {user.username}")
        print(f"  Email:            {user.email}")
        print(f"  Email Verified:   {user.email_verified}")
        print(f"  Subject (ID):     {user.sub}")
        print(f"  Expires:          {user.exp}")
        print(f"  Issuer:           {user.issuer}")
        print()
        print(f"  String repr:      {str(user)}")
        print(f"  Python repr:      {repr(user)}")
        print()

        print("-" * 70)
        print("All OIDC Claims (from x-amzn-oidc-data):")
        print("-" * 70)
        for key, value in user.oidc_claims.items():
            print(f"  {key}: {value}")
        print()

        print("-" * 70)
        print("All Access Token Claims (from x-amzn-oidc-accesstoken):")
        print("-" * 70)
        for key, value in user.access_claims.items():
            print(f"  {key}: {value}")
        print()

        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("The library is working correctly! 🎉")

    except ExpiredTokenError as e:
        print(f"❌ ERROR: Token has expired")
        print(f"   Details: {e}")
        print()
        print("   This is expected if your tokens are old.")
        print("   Try getting fresh tokens from your application.")

    except InvalidTokenError as e:
        print(f"❌ ERROR: Token verification failed")
        print(f"   Details: {e}")
        print()
        print("   Possible causes:")
        print("   - Wrong AWS region specified")
        print("   - Token was modified or corrupted")
        print("   - Network issues fetching public keys")

    except MissingTokenError as e:
        print(f"❌ ERROR: Missing required token")
        print(f"   Details: {e}")

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}")
        print(f"   Details: {e}")
        print()
        import traceback

        traceback.print_exc()
        print()
        print("   Please share this error for debugging.")


if __name__ == "__main__":
    test_user_library()
