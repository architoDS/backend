import datetime, json
from flask import request, jsonify, g
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from db import get_db_connection
from flask_restx import Resource, Namespace, fields  # type: ignore
from middleware import token_required

api = Namespace('prompt_create', description='Prompt lib creation')

# Model for request and response validation using Flask-RESTX
prompt_create = api.model('Promptcreate', {
    'app_id': fields.String(description='ID of the associated application', example='1234'),
    'model_id': fields.String(description='Model that the prompt is tested against', example='GPT-3.5'),
    'description': fields.String(description='Description of the prompt', example='This prompt tests model performance.'),
    'category': fields.String(description='Category of the prompt', example='Finance'),
    'usage_examples': fields.String(description='Examples of how the prompt is used', example='Calculate annual revenue'),
})

# POST method to create or update prompt data (new method)
class PromptCreateResource(Resource):
    @token_required  
    @api.doc('create_or_update_prompt_lib')
    @api.expect(prompt_create)  
    @api.marshal_with(prompt_create)  
    def post(self):
        """
        Handle the creation or update of a prompt entry. The prompt is associated with an application and model.
        """
        try:
            # Parse the incoming JSON data
            request_data = json.loads(request.data)
            db_connection = get_db_connection()  # Establish a DB connection
            cursor = db_connection.cursor()

            if request_data:
                print("Request Data:", request_data)

                app_id = request_data['app_id']
                model_id = request_data['model_id']

                # SQL queries to fetch application name and model name based on IDs
                app_query = 'SELECT app_name FROM shared.application WHERE client_id = ?'
                model_query = 'SELECT model_name FROM base.models WHERE model_id = ?'

                # Execute the queries and fetch the results
                app_query_result = cursor.execute(app_query, (app_id,)).fetchall()
                model_query_result = cursor.execute(model_query, (model_id,)).fetchall()

                # If no results are returned, raise an exception
                if not app_query_result or not model_query_result:
                    raise ValueError("Invalid app_id or model_id. No data found.")

                # Loop through the query results
                for app_row, model_row in zip(app_query_result, model_query_result):
                    app_name = app_row[0]  # Extract the app_name
                    model_name = model_row[0]  # Extract the model_name

                    # Print for debugging purposes
                    print(f"App Name: {app_name}, Model Name: {model_name}")

                print("App Query Result:", app_query_result)
                print("Model Query Result:", model_query_result)

            # Retrieve user details from the token (JWT-based authentication)
            token_details = g.decoded_token
            user_email = token_details['preferred_username']

            # Get the current highest prompt_id from the database (assumes prompt_id is numeric)
            cursor.execute('SELECT MAX(CAST(prompt_id AS INTEGER)) FROM base.prompt_lib')
            result = cursor.fetchone()

            # Determine the next prompt_id
            new_prompt_id = result[0] + 1 if result[0] is not None else 1

            # Get the current date for creation_date and last_modified_date
            current_date = datetime.date.today()

            # Insert a new record into the prompt_lib table
            query = '''INSERT INTO base.prompt_lib (prompt_id, app_name, llm_tested_with, description, category, 
                                                creation_date, last_modified_date, usage, author)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            cursor.execute(query, (
                new_prompt_id,  # New prompt_id
                app_name,       # App name retrieved from the DB
                model_name,     # Model name retrieved from the DB
                request_data['description'],  # Prompt description from the request
                request_data['category'],     # Prompt category from the request
                current_date,   # Creation date
                current_date,   # Last modified date (initially same as creation)
                request_data['usage_examples'],  # Example usage from the request
                user_email  # Author (email from the JWT token)
            ))

            db_connection.commit()  # Commit the transaction to the DB

            # Return a success message with the newly created prompt ID
            return jsonify({"message": "Prompt created successfully", "prompt_id": new_prompt_id}), 200

        except ValueError as e:
            # Handle specific value errors (e.g., invalid app_id or model_id)
            print(f"Validation Error: {e}")
            return jsonify({"message": str(e)}), 400

        except Exception as e:
            # Catch all other exceptions and log the error
            print(f"Error occurred while inserting/updating prompt: {e}")
            
# Add resource to API
api.add_resource(PromptCreateResource, '/')