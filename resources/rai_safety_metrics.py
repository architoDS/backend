from flask import Flask, request,g
from flask_restx import Api, Resource, Namespace, fields
from db import get_db_connection
from middleware import token_required



api = Namespace('safety_metrics', description='Safety Metrics operations')

# Define response model
metrics_model = api.model('SafetyMetrics', {
    "response": fields.Nested(api.model('Response', {
        "labels": fields.List(fields.String, description="List of labels"),
        "data": fields.List(fields.Integer, description="Corresponding data for labels")
    })),
    "request": fields.Nested(api.model('Request', {
        "labels": fields.List(fields.String, description="List of labels"),
        "data": fields.List(fields.Integer, description="Corresponding data for labels")
    }))
})

# Check if all elements in data are null
def is_empty_data(data):
    return all(item is None for item in data)


class SafetyMetricsResource(Resource):
    @api.doc('safety metrics')
    @token_required
    @api.expect(api.parser().add_argument('application_id', type=str, required=True, help='Application ID for metrics'))
    @api.marshal_with(metrics_model)
    def get(self):
        """Fetch Safety Metrics for the given Application ID"""
        application_id = request.args.get('application_id')

        if not application_id:
            return {"message": "Application ID is required."}, 400

        try:
            token_details = g.decoded_token
            user_email = token_details.get('preferred_username', 'Unknown User')

            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Query for response metrics
            response_query = '''
                SELECT 
                    SUM(violent_crimes) AS violent_crimes,
                    SUM(privacy) AS privacy,
                    SUM(non_violent_crimes) AS non_violent_crimes,
                    SUM(intellectual_property) AS intellectual_property,
                    SUM(sex_crimes) AS sex_crimes,
                    SUM(indiscriminate_weapons) AS indiscriminate_weapons,
                    SUM(child_exploitation) AS child_exploitation,
                    SUM(hate) AS hate,
                    SUM(defamation) AS defamation,
                    SUM(self_harm) AS self_harm,
                    SUM(specialized_advice) AS specialized_advice,
                    SUM(sexual_content) AS sexual_content,
                    SUM(elections) AS elections
                FROM 
                    dbr_report.rai_safety_metrics
                WHERE 
                    application_id = ?
                    AND task_type = 'response';
            '''
            cursor.execute(response_query, (application_id,))
            response_data = cursor.fetchone()

            # Query for request metrics
            request_query = '''
                SELECT 
                    SUM(violent_crimes) AS violent_crimes,
                    SUM(privacy) AS privacy,
                    SUM(non_violent_crimes) AS non_violent_crimes,
                    SUM(intellectual_property) AS intellectual_property,
                    SUM(sex_crimes) AS sex_crimes,
                    SUM(indiscriminate_weapons) AS indiscriminate_weapons,
                    SUM(child_exploitation) AS child_exploitation,
                    SUM(hate) AS hate,
                    SUM(defamation) AS defamation,
                    SUM(self_harm) AS self_harm,
                    SUM(specialized_advice) AS specialized_advice,
                    SUM(sexual_content) AS sexual_content,
                    SUM(elections) AS elections
                FROM 
                    dbr_report.rai_safety_metrics
                WHERE 
                    application_id = ?
                    AND task_type = 'request';
            '''
            cursor.execute(request_query, (application_id,))
            request_data = cursor.fetchone()

            labels = [
                "violent_crimes", "privacy", "non_violent_crimes", "intellectual_property",
                "sex_crimes", "indiscriminate_weapons", "child_exploitation", "hate",
                "defamation", "self_harm", "specialized_advice", "sexual_content", "elections"
            ]

            # response = {
            #     "response": {
            #         "labels": labels,
            #         "data": list(response_data) if response_data else [0] * len(labels)
            #     },
            #     "request": {
            #         "labels": labels,
            #         "data": list(request_data) if request_data else [0] * len(labels)
            #     }
            # }
            response = {
                "response": {
                    "labels": ["non_harmful_response"] if is_empty_data(response_data) else labels,
                    "data": [100] if is_empty_data(response_data) else list(response_data)
                },
                "request": {
                    "labels": ["non_harmful_response"] if is_empty_data(request_data) else labels,
                    "data": [100] if is_empty_data(request_data) else list(request_data)
                }
            }
            return response, 200
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return {"message": "Error fetching metrics", "error": str(e)}, 500
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db_connection' in locals():
                db_connection.close()


# Add the namespace to the API
api.add_resource(SafetyMetricsResource, '/')