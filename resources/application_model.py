from collections import defaultdict
from flask import request, jsonify
# from flask_restful import Resource
from flask_jwt_extended import jwt_required
from db import get_db_connection
from flask_restx import Namespace, fields,Resource # type: ignore
from middleware import token_required

api = Namespace('application_model', description='Application Model operations')

# Model schema for individual models
model_schema = api.model('Model', {
    'model_id': fields.String(description='ID of the model', example='5678'),
    'model_name': fields.String(description='Name of the model', example='Model 1'),
    'security_clearance': fields.String(description='Security clearance status', example='Approved'),
    'IT_clearance': fields.String(description='IT clearance status', example='Approved'),
    'legal_clearance': fields.String(description='Legal clearance status', example='Approved'),
    'expirementation': fields.String(description='expirementation', example='Yes/No')
})

# Model schema for the application
application_model = api.model('ModelInfo', {
    'models': fields.List(fields.Nested(model_schema))  # Nested list of models
})

class ApplicationModelResource(Resource):
    @api.doc('get_application_model')
    @api.marshal_with(application_model, as_list=False)
    @token_required
    def get(self):
        """
        Retrieve model information from the `base.models` table.
        """
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            
            # Query to fetch model data
            query = """
                    SELECT DISTINCT
                        model_id, 
                        model_name, 
                        security_clearance, 
                        IT_clearance, 
                        legal_clearance,
                        expirementation
                    FROM 
                        base.models where active = ?;
                    """
            
            cursor.execute(query,'true')
            model_data = cursor.fetchall()
            
            # Transform data into the expected format
            models = []
            if model_data:
                for row in model_data:
                    model = {
                        "model_id": row[0],
                        "model_name": row[1],
                        "security_clearance": row[2],
                        "IT_clearance": row[3],
                        "legal_clearance": row[4],
                        "expirementation": row[5]
                    }
                    models.append(model)

            # Response format expected by the application_model schema
            return {"models": models if models else []}, 200

        except Exception as e:
            print(f"Error fetching application model data: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500
        finally:
            cursor.close()
            db_connection.close()

api.add_resource(ApplicationModelResource, '/')