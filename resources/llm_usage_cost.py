import json
from flask import request
from flask_restful import Resource
from db import get_db_connection
from flask_restx import Resource, Namespace, fields
from middleware import token_required
from datetime import datetime

api = Namespace('dbr_model_serving_cost', description='DBR Model Serving Cost Management')

# Model for request validation using Flask-RESTX
dbr_model_serving_cost_model = api.model('DbrModelServingCost', {
    'client_request_id': fields.String(description='Client Request ID', example='REQ12345'),
    'model_id': fields.String(description='Model ID', example='GPT-3.5'),
    'usage_date': fields.String(description='Date of Usage (YYYY-MM-DD)', example='2024-12-15'),
    'total_tokens': fields.Integer(description='Total Tokens Used', example=1500),
    'total_cost': fields.Float(description='Total Cost Incurred', example=12.75),
})


class ModelServingCostResource(Resource):
    @token_required
    @api.doc('create_dbr_model_serving_cost')
    @api.expect(dbr_model_serving_cost_model)
    def post(self):
        """
        Create a new record in the model_serving_cost table.
        """
        try:
            # Parse the incoming request data
            request_data = json.loads(request.data)
            
            client_request_id= request_data.get('client_request_id')
            model_id= request_data.get('model_id')
            usage_date= request_data.get('usage_date')
            total_tokens= request_data.get('total_tokens')
            total_cost= request_data.get('total_cost')
            
            # Validate required fields
            required_fields = ['client_request_id', 'model_id', 'usage_date', 'total_tokens', 'total_cost']
            missing_fields = [field for field in required_fields if field not in request_data or not request_data[field]]
            if missing_fields:
                return {"message": f"Missing required fields: {', '.join(missing_fields)}"}, 400

            # Validate date format
            try:
                usage_date = datetime.strptime(usage_date, '%Y-%m-%d').date()
            except ValueError:
                return {"message": "Invalid date format. Use YYYY-MM-DD."}, 400

            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Insert the new record into the database
            query = '''INSERT INTO dbr_report.dbr_model_serving_cost (client_request_id, model_id, usage_date, total_tokens, total_cost) VALUES (?, ?, ?, ?, ?)'''
            cursor.execute(query, (client_request_id, model_id, usage_date, total_tokens, total_cost))
            db_connection.commit()

            return {
                "message": "Record created successfully",
                "record": request_data
            }, 201

        except json.JSONDecodeError:
            return {"message": "Invalid JSON payload."}, 400
        except ConnectionError:
            return {"message": "Failed to connect to the database."}, 500
        except Exception as e:
            print(f"Error occurred while creating record: {e}")
            return {"message": "An unexpected error occurred.", "error": str(e)}, 500

    @token_required
    @api.doc('get_dbr_model_serving_costs')
    def get(self):
        """
        Fetch records from the dbr_report.dbr_model_serving_cost table with optional filters:
        - startDate and endDate (YYYY-MM-DD format)
        - client_id (optional).
        """
        try:
            start_date = request.args.get('startDate')
            end_date = request.args.get('endDate')
            client_id = request.args.get('client_id')

            # Validate date range if provided
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    if start_date > end_date:
                        return {"message": "startDate cannot be greater than endDate."}, 400
                except ValueError:
                    return {"message": "Invalid date format. Use YYYY-MM-DD."}, 400

            db_connection = get_db_connection()
            if db_connection is None:
                return {"message": "Failed to connect to the database."}, 500
            cursor = db_connection.cursor()

            # Base query with joins to fetch client name and model name
            query = '''
                SELECT DISTINCT
                    cost.client_request_id,
                    cost.model_id,
                    cost.usage_date, 
                    cost.total_tokens, 
                    cost.total_cost,
                    COALESCE(
                        CASE 
                            WHEN cost.client_request_id LIKE '%ul_custom_model%' THEN 'Custom Model'
                            WHEN cost.client_request_id LIKE '%ul_dbr_devloper%' THEN 'DBR Developer'
                        END,
                        user_grp.usr_grp_id,
                        app.app_name
                    ) AS client_name,
                    models.model_name AS model_name
                FROM 
                    dbr_report.dbr_model_serving_cost AS cost
                LEFT JOIN 
                    shared.application AS app ON cost.client_request_id = app.client_id
                LEFT JOIN 
                    base.models AS models ON cost.model_id = models.model_id
                LEFT JOIN 
                    shared.user_grp_map AS user_grp ON cost.client_request_id = user_grp.usr_id
                WHERE 1=1
            '''
            params = []

            # Apply filters if provided
            if start_date and end_date:
                query += " AND cost.usage_date BETWEEN ? AND ?"
                params.extend([start_date, end_date])

            if client_id:
                query += " AND cost.client_request_id = ?"
                params.append(client_id)

            cursor.execute(query, params)
            records = cursor.fetchall()

            # Format the results
            results = [
                {
                    "client_id": record[0],
                    "model_id": record[1],
                    "usage_date": record[2],
                    "total_tokens": record[3],
                    "total_cost": format(round(float(record[4]), 6), '.6f') if record[4] is not None else None,  # Rounding to 6 decimal places
                    "client_name": record[5],
                    "model_name": record[6]
                }
                for record in records
            ]

            # Return results
            return {
                "message": "Records fetched successfully",
                "records": results if results else []
            }, 200

        except ConnectionError:
            return {"message": "Failed to connect to the database."}, 500
        except Exception as e:
            print(f"Error occurred while fetching records: {e}")
            return {"message": "An unexpected error occurred.", "error": str(e)}, 500


# Add resource to the API
api.add_resource(ModelServingCostResource, '/')
