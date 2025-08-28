from flask import jsonify, request
from db import get_db_connection
from flask_restx import fields, Namespace, Resource
from middleware import token_required

# Define a Namespace for the Application Model API
api = Namespace('AppModelMap', description='Application-Model Mapping operations')

# Define the Application Model for Swagger documentation
app_model_map_model = api.model('AppModelMap', {
    'id': fields.Integer(description='The unique ID of the mapping', example=1),
    'client_id': fields.String(description='The client ID', example='CLIENT123'),
    'model_id': fields.String(description='The model ID', example='az_openai_gpt-35-turbo-1106_chat'),
    'model_name': fields.String(description='The model name', example='gpt-3.5-turbo-1106')
})

class AppModels(Resource):  # Updated class name
    @api.doc('Get App-Model Mappings')
    @api.marshal_with(app_model_map_model, as_list=True)
    @token_required
    def get(self):
        """
        Retrieves App-Model mappings.
        - If `client_id` is provided as a query parameter, filters by `client_id`.
        - Returns both `model_id` and `model_name`.
        """
        db_connection = None
        cursor = None
        try:
            client_id = request.args.get('client_id')
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Query to join shared.app_model_map and base.models
            query = '''
                SELECT DISTINCT 
                    map.id, 
                    map.client_id, 
                    map.model_id, 
                    models.model_name
                FROM 
                    shared.app_model_map AS map
                INNER JOIN 
                    base.models AS models
                ON 
                    map.model_id = models.model_id
            '''
            params = []

            # Add filter if client_id is provided
            if client_id:
                query += " WHERE map.client_id = ?"
                params.append(client_id)

            cursor.execute(query, params)
            mappings = cursor.fetchall()

            # Format the results
            if mappings:
                mappings_data = [
                    {
                        'id': mapping[0],
                        'client_id': mapping[1],
                        'model_id': mapping[2],
                        'model_name': mapping[3],
                    }
                    for mapping in mappings
                ]
                return mappings_data, 200
            return [], 200

        except Exception as e:
            print(f"Error fetching app-model mappings: {e}")
            return jsonify({"message": "An error occurred while fetching data", "error": str(e)}), 500

        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()

# Register the AppModels resource with the API
api.add_resource(AppModels, '/')
