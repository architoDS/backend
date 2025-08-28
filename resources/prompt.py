import datetime
import json
from flask import request, jsonify, g
from flask_restx import Resource, Namespace, fields  # Corrected to only import Resource from flask_restx
from flask_jwt_extended import jwt_required
from db import get_db_connection
from middleware import token_required

api = Namespace('prompt', description='Prompt lib creation')

# Model for request and response validation using Flask-RESTX
prompt = api.model('Promptcreate', {
    'prompt_id': fields.String(required=False, description='ID of the prompt', example='001'),
    'app_name': fields.String(description='ID of the associated application', example='1234'),
    'model_name': fields.String(description='Model that the prompt is tested against', example='GPT-3.5'),
    'description': fields.String(description='Description of the prompt', example='This prompt tests model performance.'),
    'category': fields.String(description='Category of the prompt', example='Finance'),
    'creation_date': fields.Date(description='Creation date of the prompt', example='2024-09-15'),
    'last_modified_date': fields.Date(description='Last modified date of the prompt', example='2024-10-01'),
    'usage_examples': fields.String(description='Examples of how the prompt is used', example='Calculate annual revenue'),
    'author': fields.String(description='Author of the prompt', example='John Doe')
})

# POST method to create or update prompt data (new method)
class PromptResource(Resource):
    @token_required
    @api.doc('create_or_update_prompt_lib')
    @api.expect(prompt)
    def post(self):
        """
        Create or update a prompt entry with versioning.
        """
        try:
            # Parse the incoming request data
            request_data = json.loads(request.data)
            if not request_data:
                return {"message": "Request data is missing or invalid."}, 400

            # Validate required fields
            app_id = request_data.get('app_id')
            model_id = request_data.get('model_id')

            if not app_id or not model_id:
                return {"message": "app_id and model_id are required fields."}, 400

            # Establish database connection
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Fetch app_name and model_name from their respective tables
            app_query = 'SELECT app_name FROM shared.application WHERE client_id = ?'
            model_query = 'SELECT model_name FROM base.models WHERE model_id = ?'

            app_result = cursor.execute(app_query, (app_id,)).fetchone()
            model_result = cursor.execute(model_query, (model_id,)).fetchone()

            if not app_result or not model_result:
                return {"message": "Invalid app_id or model_id. No data found."}, 404

            app_name = app_result[0]
            model_name = model_result[0]

            # Retrieve user details from the token
            token_details = g.decoded_token
            user_email = token_details.get('preferred_username', 'Unknown')

            # Check for existing prompt ID
            prompt_id = request_data.get('prompt_id')
            if prompt_id:
                cursor.execute('SELECT MAX(version) FROM base.prompt_lib WHERE prompt_id = ?', (prompt_id,))
                version_result = cursor.fetchone()

                if not version_result or version_result[0] is None:
                    return {"message": "Prompt ID not found for update."}, 404

                # Increment version and update the current flag
                new_version = version_result[0] + 1
                cursor.execute(
                    'UPDATE base.prompt_lib SET is_current = 0 WHERE prompt_id = ? AND is_current = 1',
                    (prompt_id,)
                )
            else:
                # Generate a new prompt_id and initialize the version
                cursor.execute('SELECT MAX(CAST(prompt_id AS INTEGER)) FROM base.prompt_lib')
                max_prompt_id = cursor.fetchone()[0]
                prompt_id = max_prompt_id + 1 if max_prompt_id else 1
                new_version = 1

            # Insert the new or updated prompt entry
            current_date = datetime.date.today()
            insert_query = '''
                INSERT INTO base.prompt_lib (prompt_id, version, app_name, llm_tested_with, description, category,
                                            creation_date, last_modified_date, usage, author, is_current)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(insert_query, (
                prompt_id,
                new_version,
                app_name,
                model_name,
                request_data.get('description', ''),
                request_data.get('category', ''),
                current_date,
                current_date,
                request_data.get('usage_examples', ''),
                user_email,
                1  # is_current
            ))

            db_connection.commit()

            # Prepare and return the response data
            result_data = {
                'prompt_id': prompt_id,
                'version': new_version,
                'app_name': app_name,
                'model_name': model_name,
                'description': request_data.get('description', ''),
                'category': request_data.get('category', ''),
                'creation_date': current_date.isoformat(),
                'last_modified_date': current_date.isoformat(),
                'usage_examples': request_data.get('usage_examples', ''),
                'author': user_email
            }

            return {
                "message": "Prompt created or updated successfully.",
                "data": result_data
            }, 200

        except ValueError as e:
            return {"message": str(e)}, 400

        except Exception as e:
            print(f"Error occurred: {e}")
            return {"message": "An error occurred while processing the request."}, 500

# Add resource to API
api.add_resource(PromptResource, '/')
