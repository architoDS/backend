from flask_restx import Resource, fields, Namespace
from db import get_db_connection
from flask_jwt_extended import jwt_required
from middleware import token_required

api = Namespace('model_usage', description='Model Usage operations')

# Define the Model Usage model for Swagger documentation
model_fields = api.model('ModelUsage', {  # Changed model name for consistency
    'model_id': fields.String(description='The ID of the model'),
    'model_name': fields.String(description='The name of the model'),
    'percentage_usage': fields.Float(description='The performance percentage of the model'),
})

class ModelUsagesResource(Resource):
    @api.doc('get_models')
    # @api.doc(security='Bearer Auth')
    @api.marshal_with(model_fields, as_list=True)
    @token_required  # Token authentication enabled
    def get(self):
        db_connection = None
        cursor = None
        try:
            # Establish a database connection
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Execute query to retrieve models ordered by percentage_usage in descending order
            query = """
                SELECT 
                model_id,
                model_name,
                percentage_usage
                        FROM (
                            SELECT 
                                m.model_id,
                                m.model_name,
                                u.percentage_usage,
                                ROW_NUMBER() OVER (PARTITION BY m.model_id ORDER BY u.percentage_usage DESC) AS rn
                            FROM 
                                dbr_report.usage_metrics AS u
                            JOIN 
                                base.models AS m 
                            ON 
                                u.model_id = m.model_id
                            WHERE
                                m.model_type != 'Embedding'
                        ) AS ranked_models
                        WHERE 
                            rn = 1
                        ORDER BY 
                            percentage_usage DESC;

            """
            cursor.execute(query)
            models = cursor.fetchall()

            # Prepare the response data
            models_data = [{
                'model_id': model[0],
                'model_name': model[1],
                'percentage_usage': model[2]
            } for model in models]

            return models_data, 200  # Return the data with HTTP status 200

        except (ConnectionError, OSError) as e:
            # Handle connection-related errors
            print(f"Database connection error: {e}")
            return {'message': 'Database connection error'}, 500

        except Exception as e:
            # Handle all other exceptions
            print(f"Unexpected error: {e}")
            return {'message': 'An unexpected error occurred'}, 500

        finally:
            # Ensure resources are cleaned up
            if cursor:
                cursor.close()  # Close the cursor if it was created
            if db_connection:
                db_connection.close()  # Close the database connection if it was created

# Add the resource to the namespace
api.add_resource(ModelUsagesResource, '/')
