from flask import request, jsonify, g
from db import get_db_connection
from flask_restx import Namespace, fields, Resource
from middleware import token_required

# Define the Namespace for the llm_ops_dashboard
api = Namespace('llm_ops_dashboard', description='LLM Operations Dashboard')

# Define the API model for Swagger documentation
llm_ops_dashboard = api.model('LlmOpsDashboard', {
    'avg_execution_time': fields.String(description='Average execution time', example='30'),
    'no_of_users': fields.String(description='Number of users', example='5678'),
    'total_no_of_requests': fields.String(description='Total number of requests', example='1121'),
    'no_of_successful_responses': fields.String(description='Number of successful responses', example='121'),
    'no_of_tokens': fields.String(description='Number of tokens', example='123')
})

class LlmOpsDashboardResource(Resource):
    @api.doc('llm_ops_dashboard')  # Document endpoint for Swagger
    @api.expect(api.parser().add_argument('model_id', type=str, help='Model ID', required=False))  # Optional model_id parameter
    @api.expect(api.parser().add_argument('application_id', type=str, help='Application ID', required=False))  # Optional application_id parameter
    @api.marshal_with(llm_ops_dashboard)  # Specify response format
    @token_required  # Require token authorization
    def get(self):
        """
        Retrieves LLM operations data. If model_id is provided, filters by model_id; otherwise, uses multiple client_ids.
        """
        try:
            # Retrieve user details from the token
            token_details = g.decoded_token
            user_email = token_details.get('preferred_username')

            # Establish initial database connection to fetch client_ids based on user_email
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Check if the user is an admin
            admin_check_query = 'SELECT 1 FROM shared.admin_users WHERE email = ? and is_active = 1'
            cursor.execute(admin_check_query, (user_email,))
            is_admin = cursor.fetchone() is not None

            # Query to fetch applications based on user role (admin or not)
            if is_admin:
                query = 'SELECT client_id, app_name FROM shared.application'
                cursor.execute(query)
            else:
                # If the user is not an admin, filter by owner or app_user
                query = 'SELECT client_id, app_name FROM shared.application WHERE owner = ? OR app_user = ?'
                cursor.execute(query, (user_email.lower(), user_email.lower()))

            applications = cursor.fetchall()

            # Check if any application data is returned
            if not applications:
                return {"message": "No applications found for the user"}

            # Extract all client_ids from the application data
            client_ids = [app[0] for app in applications]
        except Exception as e:
            print(f"Error fetching application data: {e}")
            return jsonify({"message": "An error occurred while fetching application data"}), 500

        finally:
            # Close cursor and initial connection
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()

        # Retrieve the optional model_id parameter from the query string
        model_id = request.args.get('model_id')
        client_id = request.args.get('application_id')
        db_connection = None  # Reinitialize for the next query

        try:
            # Establish database connection for the main query
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Base query to retrieve aggregated data from model usage aggregation table
            query = """
                SELECT 
                    SUM(no_of_tokens) AS total_tokens,
                    COUNT(DISTINCT requester_id) AS total_users,
                    SUM(total_no_of_request) AS total_requests,
                    SUM(successful_responses) AS total_successful_responses,
                    AVG(avg_execution_time) AS avg_execution_time
                FROM 
                    dbr_report.model_requester_aggr
            """ 
            # Initialize parameters list
            parameters = []

            # Add WHERE clause for filtering by model_id or client_id
            conditions = []
            
            if model_id:
                conditions.append("model_id = ?")
                parameters.append(model_id)

            if client_id:
                conditions.append("requester_id = ?")
                parameters.append(client_id)

            # If both model_id and client_id are not provided, use client_ids
            if not model_id and not client_id:
                if client_ids:  # For multiple client_ids
                    conditions.append("requester_id IN ({})".format(','.join(['?'] * len(client_ids))))
                    parameters.extend(client_ids)

            # If there are any conditions, add them to the query
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Execute the query with parameters
            cursor.execute(query, parameters)
            result = cursor.fetchone()

            # Prepare response data, handling None results by returning '0' where appropriate
            if result:
                llm_ops_details = {
                    'avg_execution_time': str(result[4]) if result and result[4] is not None else '0',
                    'no_of_users': str(result[1]) if result and result[1] is not None else '0',
                    'total_no_of_requests': str(result[2]) if result and result[2] is not None else '0',
                    'no_of_successful_responses': str(result[3]) if result and result[3] is not None else '0',
                    'no_of_tokens': str(result[0]) if result and result[0] is not None else '0'
                }

            # Return the response data with a 200 HTTP status code
            return llm_ops_details if llm_ops_details else [], 200

        except Exception as e:
            # Log exception and return an error message with status 500
            print(f"Error fetching LLM operations data: {e}")
            return jsonify({"message": "An error occurred while fetching data"}), 500

        finally:
            # Ensure cursor and connection are closed after query execution
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()

# Register the resource with the API namespace at the endpoint '/llm_ops_dashboard'
api.add_resource(LlmOpsDashboardResource, '/')
