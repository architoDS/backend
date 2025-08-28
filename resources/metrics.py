from flask_restx import Resource, fields, Namespace
from db import get_db_connection
from middleware import token_required
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from flask import request


api = Namespace('usage_metrics', description='Usage Metrics operations')

# Define the response model for Swagger
usage_metrics_response = api.model('Usage Metrics Response', {
    'model_name': fields.String(required = False, description='The name of the model'),
    'cpu_usage_percentage': fields.List(fields.Raw(), description='List of CPU usage metrics'),
    'mem_usage_percentage': fields.List(fields.Raw(), description='List of memory usage metrics'),
})

class UsageMetricsResource(Resource):
    @api.doc('get_usage_metrics')
    @api.doc('get_application_model')
    # @api.doc(security='Bearer Auth')
    @api.marshal_with(usage_metrics_response)
    @api.expect(api.parser().add_argument('model_id', type=str, help='The model_name', required=False))
    @token_required  # Ensure that token authentication is applied
    def get(self):
        model_id = request.args.get('model_id')
        db_connection = None
        cursor = None
        try:
            # Establish a database connection
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Calculate the date 7 days ago from today
            seven_days_ago = (datetime.now() - timedelta(days=7)).date()
            date_object = datetime.strptime(str(seven_days_ago), "%Y-%m-%d")
            # Convert the datetime object to a timestamp in milliseconds
            timestamp = int(date_object.timestamp() * 1000)

            # Prepare the SQL query based on whether model_name is provided
            if model_id:
                query = '''
                    SELECT metric_name, value, timestamp, endpoint_name, workspace_id, served_model_id, served_model_name
                    FROM dbr_report.cpu_mem_usage_data
                    WHERE served_model_id = ? 
                      AND metric_name IN ('cpu_usage_percentage', 'mem_usage_percentage')
                      AND timestamp >= ?
                '''
                parameters = (model_id, timestamp)
            else:
                query = '''
                    SELECT metric_name, value, timestamp, endpoint_name, workspace_id, served_model_id, served_model_name
                    FROM dbr_report.cpu_mem_usage_data
                    WHERE metric_name IN ('cpu_usage_percentage', 'mem_usage_percentage')
                      AND timestamp >= ?
                '''
                parameters = (timestamp)
            
            # Execute the query
            cursor.execute(query, parameters)

            metrics = cursor.fetchall()
            # Prepare the response data
            response_data = {
                'model_id': model_id if model_id else 'All Models',
                'cpu_usage_percentage': [],
                'mem_usage_percentage': []
            }
            cpu_values = []
            cpu_timestamps = []
            mem_values = []
            mem_timestamps = []
            if metrics:
                for metric in metrics:
                    metric_name, value, timestamp, endpoint_name, workspace_id, served_model_id, served_model_name = metric
                    
                    timestamp_seconds = timestamp / 1000
                    # Convert the timestamp to a datetime object
                    date_timestamp = datetime.fromtimestamp(timestamp_seconds)
                    # Format the datetime object as a date string
                    date_string = date_timestamp.strftime("%Y-%m-%d")

                    if metric_name == 'cpu_usage_percentage':
                        cpu_values.append(value)
                        cpu_timestamps.append(date_string)
                    elif metric_name == 'mem_usage_percentage':
                        mem_values.append(value)
                        mem_timestamps.append(date_string)

            # Aggregate the response
            if cpu_values:
                response_data['cpu_usage_percentage'].append({
                    'metric_name': 'cpu_usage_percentage',
                    'value': cpu_values,
                    'timestamp': cpu_timestamps,
                    'endpoint_name': endpoint_name,
                    'workspace_id': workspace_id,
                    'served_model_id': served_model_id,
                    'served_model_name': served_model_name
                })

            if mem_values:
                response_data['mem_usage_percentage'].append({
                    'metric_name': 'mem_usage_percentage',
                    'value': mem_values,
                    'timestamp': mem_timestamps,
                    'endpoint_name': endpoint_name,
                    'workspace_id': workspace_id,
                    'served_model_id': served_model_id,
                    'served_model_name': served_model_name
                })

            return response_data if response_data else [], 200  # Return the structured data with HTTP status 200

        except (ConnectionError, OSError) as e:
            # Handle connection-related errors
            return {'message': 'Database connection error'}, 500

        except Exception as e:
            # Handle all other exceptions
            return {'message': 'An unexpected error occurred'}, 500

        finally:
            # Ensure resources are cleaned up
            if cursor:
                cursor.close()  # Close the cursor if it was created
            if db_connection:
                db_connection.close()  # Close the database connection if it was created

# Add the resource to the namespace
api.add_resource(UsageMetricsResource, '/')
