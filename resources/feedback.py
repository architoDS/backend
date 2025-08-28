import json
from flask import request, g
from flask_restful import Resource
from db import get_db_connection
from flask_restx import Resource, Namespace, fields  # type: ignore
from middleware import token_required

api = Namespace('feedback', description='Feedback Management')

# Model for request validation using Flask-RESTX
feedback_model = api.model('Feedback', {
    'dashboard_decision_impact': fields.String(description='Impact of dashboard decisions', example='Improved decision-making efficiency.'),
    'feature_change_suggestion': fields.String(description='Suggestions for feature changes', example='Add a dark mode toggle.'),
    'user_experience_feedback': fields.String(description='Feedback on user experience', example='The interface is intuitive and easy to use.'),
    'user_email': fields.String(description='Email of the user providing feedback', example='user@example.com')
})

class FeedbackResource(Resource):
    @token_required
    @api.doc('create_feedback')
    @api.expect(feedback_model)
    def post(self):
        """
        Handle creation of a new feedback record. Return the created record.
        """
        try:
            # Parse incoming request data
            request_data = json.loads(request.data)
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            token_details = g.decoded_token
            user_email = token_details['preferred_username']

            # Insert a new record into the feedback table
            query = '''INSERT INTO shared.feedback (dashboard_decision_impact, feature_change_suggestion, user_experience_feedback, user_email)
                       VALUES (?, ?, ?, ?)'''
            cursor.execute(query, (
                request_data.get('dashboard_decision_impact'),
                request_data.get('feature_change_suggestion'),
                request_data.get('user_experience_feedback'),
                user_email
            ))

            db_connection.commit()
            return {
                "message": "Feedback created successfully",
            }, 201

        except Exception as e:
            print(f"Error occurred while creating feedback: {e}")
            return {"message": "An error occurred", "error": str(e)}, 500

# Add resource to the API
api.add_resource(FeedbackResource, '/')
