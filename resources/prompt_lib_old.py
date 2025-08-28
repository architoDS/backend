import datetime
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from db import get_db_connection
from flask_restx import Resource, Namespace, fields # type: ignore
from middleware import token_required
 
api = Namespace('prompt_lib', description='Prompt lib operations')

"""

# Define the API model for prompt_lib
prompt_lib = api.model('PromptLib', {
    'id' : fields.String(required= False, description='ID of the prompt', example='1'),
    'prompt_id': fields.String(required= False, description='ID of the prompt', example='001'),
    'app_name': fields.String(description='ID of the associated application', example='1234'),
    'llm_tested_with': fields.String(description='Model that the prompt is tested against', example='GPT-3.5'),
    'description': fields.String(description='Description of the prompt', example='This prompt tests model performance.'),
    'category': fields.String(description='Category of the prompt', example='Finance'),
    'creation_date': fields.Date(description='Creation date of the prompt', example='2024-09-15'),
    'last_modified_date': fields.Date(description='Last modified date of the prompt', example='2024-10-01'),
    'usage_examples': fields.String(description='Examples of how the prompt is used', example='Calculate annual revenue'),
    'author': fields.String(description='Author of the prompt', example='John Doe'),
    'version': fields.Integer(description='Version number of the prompt', example='1'),
    'is_current': fields.Boolean(description='Indicates whether this is the current version of the prompt', example=True)
})
"""

# new API Prompt_lib laibray for exp 28 aug 2025
prompt_lib = api.model('PromptLib', {
    'id': fields.String(required=False, description='Row index (computed)'),
    'prompt_id': fields.String(required=True, description='ID of the prompt', example='PROMPT-001'),
    'app_name': fields.String(required=True, description='Application name', example='SalesApp'),
    'title': fields.String(required=True, description='Human-friendly title for the prompt', example='Quarterly Revenue Summary'),
    'llm_tested_with': fields.String(description='Model tested against', example='gpt-4o'),
    'description': fields.String(description='Description', example='Summarizes quarterly revenue.'),
    'category': fields.String(description='Category', example='Finance'),
    'creation_date': fields.Date(description='Creation date', example='2024-09-15'),
    'last_modified_date': fields.Date(description='Last modified date', example='2024-10-01'),
    'usage_examples': fields.String(description='Usage examples', example='Compute annual revenue'),
    'author': fields.String(description='Author', example='John Doe'),
    'user_id': fields.String(description='User who created/owns this version', example='user-123'),
    'version': fields.Integer(description='Version number', example=2),
    'version_id': fields.String(description='Unique ID for this version (UUID)'),
    'is_current': fields.Boolean(description='Is this the current version?', example=True),
})

 
class PromptLibResource(Resource):
 
    # GET method to retrieve all records
    @api.doc('get_prompt_lib')
    @api.doc('get_application_model')
    @api.expect(api.parser().add_argument('prompt_id', type=str, help='prompt_id name of the model', required=False))
    @api.marshal_with(prompt_lib, as_list=True)
    @token_required
    def get(self):
        prompt_id = request.args.get('prompt_id')
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            if prompt_id:
                cursor.execute('SELECT * FROM base.prompt_lib WHERE prompt_id = ? ORDER BY version DESC', (prompt_id,))
            else:
                cursor.execute('SELECT * FROM base.prompt_lib p1 WHERE p1.version = (SELECT MAX(p2.version) FROM base.prompt_lib p2 WHERE p2.prompt_id = p1.prompt_id) AND p1.is_current = 1')
            prompt_data = cursor.fetchall()
 
            prompt_details = []
            if prompt_data:
                for index, prompt in enumerate(prompt_data, start=1):
                    prompt_details.append({
                        'id':index,
                        'prompt_id': prompt[0],
                        'app_name': prompt[1],
                        'llm_tested_with': prompt[2],
                        'description': prompt[3],
                        'category': prompt[4],
                        'creation_date': prompt[5].isoformat(),
                        'last_modified_date': prompt[6].isoformat(),
                        'usage_examples': prompt[7],
                        'author': prompt[8],
                        'version' : prompt[9],
                        'is_current' : prompt[10]
                    })
 
            return prompt_details if prompt_data else [], 200
        except Exception as e:
            print(f"Error fetching prompt lib data: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500
        finally:
            cursor.close()
            db_connection.close()
 
    @api.doc('post_prompt_lib_by_app_name')
    @api.expect(api.model('AppNameRequest', {
        'app_name': fields.String(required=True, description='The name of the application', example='application_name')
    }))
    @api.marshal_with(prompt_lib, as_list=True)
    @token_required
    def post(self):
        # To get the app_name from request
        request_data = request.get_json()
        app_name = request_data.get('app_name')
        
        if not app_name:
            return jsonify({"message": "app_name is required"}), 400
 
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            # The query to use LIKE for partial matching (keyword search)
            query ='SELECT * FROM base.prompt_lib p1 WHERE p1.version = (SELECT MAX(p2.version) FROM base.prompt_lib p2 WHERE p2.prompt_id = p1.prompt_id) AND p1.is_current = 1 AND LOWER(p1.app_name) LIKE LOWER(?)'
            # query = 'SELECT * FROM base.prompt_lib WHERE LOWER(app_name) LIKE LOWER(?)'
            cursor.execute(query, (f'%{app_name}%',))
            prompt_data = cursor.fetchall()
 
            # Return an empty array if no records are found
            if not prompt_data:
                return [], 200  
 
            prompt_details = []
            for index, prompt in enumerate(prompt_data, start=1):
                prompt_details.append({
                    'id':index,
                    'prompt_id': prompt[0],
                    'app_name': prompt[1],
                    'llm_tested_with': prompt[2],
                    'description': prompt[3],
                    'category': prompt[4],
                    'creation_date': prompt[5].isoformat(),
                    'last_modified_date': prompt[6].isoformat(),
                    'usage_examples': prompt[7],
                    'author': prompt[8],
                    'version' : prompt[9],
                    'is_current' : prompt[10]
                })
 
            return prompt_details, 200
 
        except Exception as e:
            print(f"Error fetching prompt lib data for app_name {app_name}: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500
        finally:
            cursor.close()
            db_connection.close()        
 
# Add resource to API
api.add_resource(PromptLibResource, '/')


