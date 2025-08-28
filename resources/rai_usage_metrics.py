from flask_restx import Resource, fields, Namespace, reqparse
from db import get_db_connection
from flask_jwt_extended import get_jwt_identity
from flask import g, jsonify, request
from middleware import token_required
from werkzeug.exceptions import InternalServerError

# Define the namespace for RAI usage operations
api = Namespace('rai_usage', description='RAI Usage operations')

# Define the RAI Usage model for Swagger documentation
rai_usage_summary_model = api.model('RaiUsageSummary', {
    'total_request_count': fields.Integer(description='Total number of requests'),
    'content_filter_count': fields.Integer(description='Total content filter requests'),
    'hallucination_count': fields.Integer(description='Total hallucination count'),
    'llm_judge_count': fields.Integer(description='Total LLM as a judge requests'),
    'total_token_count': fields.Integer(description='Total number of tokens'),
    'total_cost': fields.Float(description='Total cost'),
})

class RaiUsageMetricsResource(Resource):
    @api.doc('get_rai_usage_metrics')
    @token_required  # Middleware to ensure token is valid
    @api.expect(api.parser().add_argument('application_id', type=str, required=True, help='Application ID for metrics'))  # Expect application_id as a query parameter
    @api.marshal_with(rai_usage_summary_model)  # Format the response according to the model
    def get(self):
        # Parse the application_id from the query parameters
        application_id = request.args.get('application_id')

        try:
            # Connect to the database
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Decode the token and retrieve the user email
            token_details = g.decoded_token
            user_email = token_details['preferred_username']

            # Prepare the SQL query based on the presence of application_id
            if application_id:
                # Query with application_id filter
                query = '''
                SELECT 
                    SUM(total_request_count) AS total_request_count,
                    SUM(content_filter_count) AS content_filter_count,
                    SUM(hallucination_count) AS hallucination_count,
                    SUM(llm_judge_count) AS llm_judge_count,
                    SUM(token_count) AS total_token_count,
                    SUM(cost) AS total_cost
                FROM dbr_report.rai_usage_metrics
                WHERE application_id = ?
                '''
                cursor.execute(query, (application_id,))
            else:
                # Aggregate all data when no application_id is provided
                query = '''
                SELECT 
                    SUM(total_request_count) AS total_request_count,
                    SUM(content_filter_count) AS content_filter_count,
                    SUM(hallucination_count) AS hallucination_count,
                    SUM(llm_judge_count) AS llm_judge_count,
                    SUM(token_count) AS total_token_count,
                    SUM(cost) AS total_cost
                FROM dbr_report.rai_usage_metrics
                '''
                cursor.execute(query)

            # Fetch the result of the query
            result = cursor.fetchone()


            # Prepare the response data with default values if any field is None
            if result:
                response_data = {
                    'total_request_count': result[0] or 0,
                    'content_filter_count': result[1] or 0,
                    'hallucination_count': result[2] or 0,
                    'llm_judge_count': result[3] or 0,
                    'total_token_count': result[4] or 0,
                    'total_cost': float(result[5] or 0.0)
                }

            return response_data if response_data else [], 200

        except Exception as e:
            # Log the error and return an internal server error response
            print(f"Error fetching RAI usage metrics: {e}")
            return {'message': 'Error fetching RAI usage metrics. Please try again later.'}, 500

        finally:
            # Close the cursor and database connection
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()

# Add the resource to the namespace with the base URL
api.add_resource(RaiUsageMetricsResource, '/')