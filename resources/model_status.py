from flask import jsonify
from flask_restful import Resource
from db import get_db_connection
from flask_restx import Resource, Namespace, fields # type: ignore
from flask_jwt_extended import jwt_required
from middleware import token_required


api = Namespace('model_status', description='Model status operations')

# Define the API model for model_status
model_status = api.model('ModelStatus', {
    'application_id': fields.String(description='ID of the application', example='1234'),
    'application_name': fields.String(description='Name of the application', example='Application 1'),
    'model_id': fields.String(description='ID of the model', example='5678'),
    'model_name': fields.String(description='Name of the model', example='Model 1'),
    'content_filter': fields.String( description='Content filter status', example='Enabled'),
    'hallucination': fields.String(description='Hallucination detection status', example='Active'),
    'llm_as_a_judge': fields.String(description='LLM as a judge status', example='Enabled')
})

class ModelStatusResource(Resource):
    @api.doc('get_model_status')
    @api.doc('get_application_model')
    # @api.doc(security='Bearer Auth')
    @api.marshal_with(model_status, as_list=True)
    @token_required
    def get(self):
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            query = """
                SELECT
                    ms.application_id,
                    a.app_name,
                    MAX(ms.model_id) AS model_id,
                    MAX(m.model_name) AS model_name,
                    MAX(ms.content_filter) AS content_filter,
                    CASE 
                        WHEN MAX(CASE WHEN ms.hallucination = 'Yes' THEN 1 ELSE 0 END) = 1
                        THEN 'Yes' 
                        ELSE 'No' 
                    END AS hallucination,              
                    CASE 
                        WHEN MAX(CASE WHEN ms.llm_as_a_judge = 'Yes' THEN 1 ELSE 0 END) = 1
                        THEN 'Yes' 
                        ELSE 'No' 
                    END AS llm_as_a_judge
                FROM
                    base.model_status ms
                JOIN 
                    shared.application a ON ms.application_id = a.client_id
                JOIN 
                    base.models m ON ms.model_id = m.model_id
                GROUP BY
                    ms.application_id,
                    a.app_name
            """
            cursor.execute(query)
            model_status_data = cursor.fetchall()

            model_status_details = []
            if model_status_data:
                for model_status in model_status_data:
                    model_status_details.append({
                        'application_id': model_status[0],
                        'application_name': model_status[1],
                        'model_id': model_status[2],
                        'model_name': model_status[3],
                        'content_filter': model_status[4],
                        'hallucination': model_status[5],
                        'llm_as_a_judge': model_status[6]
                    })

            return model_status_details if model_status_data else [], 200
        except Exception as e:
            print(f"Error fetching model status data: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500
        finally:
            cursor.close()
            db_connection.close()


api.add_resource(ModelStatusResource, '/')