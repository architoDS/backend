from flask import jsonify, request
from db import get_db_connection
from flask_restx import fields, Namespace, Resource
from middleware import token_required

# Define a Namespace for the Model API
api = Namespace('Model', description='Model operations')

# Define the Application model for Swagger documentation
model_model = api.model('Model', {
    'client_id': fields.String(description='The client ID'),
    'model_id': fields.String(description='The ID of the model'),
    'model_name': fields.String(description='The name of the model')
})

class ModelResource(Resource):
    @api.doc('Model')
    @api.marshal_with(model_model, as_list=True)
    @token_required
    def get(self):
        """
        Retrieves model data based on client_id. 
        If client_id is provided, filters by client_id; otherwise, returns all data.
        """
        db_connection = None
        cursor = None
        try:
            client_id = request.args.get('client_id')
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            query = '''
                    SELECT 
                        DISTINCT mu.model_id,
                        mu.requester_id,
                        m.model_name
                    FROM 
                        dbr_report.model_requester_aggr AS mu
                    JOIN 
                        base.models AS m 
                    ON
                        mu.model_id = m.model_id
            '''
            if client_id:
                query += "WHERE mu.requester_id = ?"
                cursor.execute(query, client_id)
            else:
                cursor.execute(query)

            models = cursor.fetchall()
            if models:
                models_data = [
                    {
                        'model_id': model[0],
                        'client_id': model[1],
                        'model_name': model[2]
                    } for model in models
                ]
            return models_data if models else [], 200
        except Exception as e:
            print(f"Error fetching model data: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500

        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()


class BaseModelsResource(Resource):
    @api.doc('get_base_models')
    @token_required
    def get(self):
        """
        Retrieves all base models with ad group access information.
        """
        db_connection = None
        cursor = None
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            query = '''
                    SELECT model_id, model_name, adgroupformodelaccess_nonprod, adgroupformodelaccess_prod
                    FROM base.models
                    '''
            cursor.execute(query)
            models = cursor.fetchall()
            
            models_data = []
            for model in models:
                models_data.append({
                    'model_id': model[0],
                    'model_name': model[1],
                    'non-prod':model[2],
                    'prod':model[3]
                })
            
            return models_data, 200
        except Exception as e:
            print(f"Database connection failed: {e}")
            return {'message': 'Database connection failed'}, 500
        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()


# Register the ModelResource with the API
api.add_resource(ModelResource, '/')
api.add_resource(BaseModelsResource, '/base')
