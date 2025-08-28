from flask_restx import Resource, fields, Namespace  # type: ignore # Use flask-restplus instead of flask-restx
from flask import request
from azure.identity import ManagedIdentityCredential
from config import Config


databricks_ns = Namespace('databricks', description='Databricks Token Exchange Operations')

# Define the token model for Swagger documentation
token_model = databricks_ns.model('TokenResponse', {
    'databricks_token': fields.String(description='The Databricks access token')
})

class DatabricksTokenExchangeService:
    def __init__(self):
        """
        Initializes the DatabricksTokenExchange with tenant ID and Databricks scope.
        """
        self.tenant_id = Config.TENANT_ID
        self.databricks_scope = Config.DATABRICKS
        self.url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        self.credential = ManagedIdentityCredential()

    def exchange_token_on_behalf_of(self, user_token):
        """
        Exchanges the provided user token for a Databricks access token using the On-Behalf-Of (OBO) flow.
        
        Parameters:
        - user_token: str - The user token obtained from the request header to be exchanged.

        Returns:
        - str: The Databricks access token that can be used for API calls.
        """
        try:
            # Retrieve a token for the Databricks API using the specified scope
            access_token = self.credential.get_token(self.databricks_scope)
            print("Access token retrieved for Databricks scope")

            # Headers and data for the OBO token request
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_id": self.credential.client_id,
                "client_secret": self.credential.client_secret,
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": user_token,
                "requested_token_use": "on_behalf_of",
                "scope": self.databricks_scope,
            }

            # Make the request to exchange the user token for a Databricks token
            response = request.post(self.url, headers=headers, data=data)

            # Check if the request was successful
            if response.status_code == 200:
                databricks_token = response.json().get("access_token")
                print("Databricks token successfully retrieved")
                return databricks_token
            else:
                raise Exception(f"Token exchange failed: {response.status_code}, {response.text}")

        except Exception as e:
            raise Exception(f"An error occurred during token exchange: {e}")

# Instantiate the service
token_service = DatabricksTokenExchangeService()

class DatabricksTokenResource(Resource):
    @databricks_ns.doc('get_databricks_token', description="Get Databricks token using user token.")
    @databricks_ns.marshal_with(token_model)  # Use token_model to format the output
    def get(self):
        """
        GET endpoint to retrieve a Databricks token on behalf of the user.
        Expects a user token in the Authorization header.
        """
        # Get the user token from the Authorization header
        user_token = request.headers.get("Authorization")
        
        if not user_token:
            databricks_ns.abort(400, "Authorization header missing")

        try:
            # Exchange the user token for a Databricks token
            databricks_token = token_service.exchange_token_on_behalf_of(user_token)
            return {"databricks_token": databricks_token}, 200
        except Exception as e:
            return {"message": str(e)}, 500

# Add the namespace to the API
databricks_ns.add_resource(DatabricksTokenResource, '/')

