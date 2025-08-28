from flask import request, jsonify, g
from functools import wraps
from token_validation import validate_token
import jwt

def token_required(func):
    """
    Middleware to require and validate a token for accessing the endpoint.
    It extracts the token from the 'Authorization' header and validates it.

    :param func: The endpoint function to protect
    :return: The decorated function
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            # Extract Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return {"error": "Authorization header missing"}, 401

            if not auth_header.startswith('Bearer '):
                return {"error": "Invalid Authorization header format"}, 401

            # Extract the token from the header
            token = auth_header.split(' ')[1]

            # Validate the token
            validation_response = validate_token(token)
            if 'error' in validation_response:
                return validation_response, 401
            print("====================>", validation_response)
            # Store the decoded token in the global 'g' object for use in the request
            g.decoded_token = validation_response

            # Proceed to the actual endpoint
            return func(*args, **kwargs)

        except IndexError:
            # Token splitting error
            return {"error": "Token missing or malformed"}, 401
        except KeyError:
            # Expected keys not present in the token
            return {"error": "Invalid token structure"}, 400
        except Exception as e:
            # Catch-all for unexpected errors
            return {"error": "An error occurred", "details": str(e)}, 500

    return decorated


def extract_app_id_from_token(func):
    @wraps(func)
    def wrapper(*args):
        # Retrieve token from the request headers
        token = request.headers.get("Authorization")
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            # Decode the token
            decoded_data = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
            app_id = decoded_data.get("appid")
            
            if not app_id:
                return jsonify({"error": "App ID not found in token"}), 401

            # Pass app_id to the function as a keyword argument
            return func(*args, app_id=app_id)
        
        except jwt.DecodeError:
            return jsonify({"error": "Token is invalid"}), 401

    return wrapper

