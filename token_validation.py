import jwt
from jwt.algorithms import RSAAlgorithm
import requests
from config import Config

def get_public_key(token):
    """
    Retrieves the public key for the given JWT from Azure AD based on the 'kid' in the token's header.

    :param token: JWT that needs to be validated
    :return: Public RSA key for the token if found, None otherwise
    """
    try:
        # Decode the token without verification to get the header and extract the 'kid'
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header['kid']
    except jwt.DecodeError as e:
        print(f"Error decoding token header: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while decoding the token: {e}")
        return None

    try:
        # Fetch the JSON Web Key Set (JWKS) from Azure AD
        jwks_uri = f"https://login.microsoftonline.com/{Config.TENANT_ID}/discovery/v2.0/keys"
        jwks_response = requests.get(jwks_uri)
        jwks_response.raise_for_status()  # Raise HTTPError for bad responses
        jwks = jwks_response.json()

        # Match 'kid' from the token header to find the correct public key
        public_key = None
        for key in jwks['keys']:
            if key['kid'] == kid:
                public_key = RSAAlgorithm.from_jwk(key)
                break

        if public_key is None:
            print("Public key not found for the token's Key ID.")
        return public_key
    except requests.RequestException as e:
        print(f"Error fetching JWKS from Azure AD: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while retrieving the public key: {e}")
        return None

def validate_token(token):
    """
    Validates a JWT against Azure AD using the public key and checks the signature.

    :param token: JWT to validate
    :return: Decoded token payload if valid, error message otherwise
    """
    public_key = get_public_key(token)
    if public_key:
        try:
            # Get the algorithm from the JWT header
            unverified_header = jwt.get_unverified_header(token)
            if unverified_header.get("alg") != "RS256":
                return {"error": "Invalid algorithm specified in token"}

            # Validate and decode the JWT using the fetched public key
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],  # The algorithm should match the one used by Azure AD
                audience=Config.CLIENT_ID,  # Your Azure AD Application (client) ID
                issuer=f"https://login.microsoftonline.com/{Config.TENANT_ID}/v2.0"
            )
            return decoded_token
        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired"}
        except jwt.InvalidAlgorithmError as e:
            return {"error": f"Invalid algorithm: {e}"}
        except jwt.InvalidTokenError as e:
            return {"error": f"Invalid token: {e}"}
    else:
        return {"error": "No valid public key found for token"}
