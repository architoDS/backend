from flask_restx import Resource, fields, Namespace  # type: ignore # Use flask-restplus instead of flask-restx
from db import get_db_connection
from middleware import token_required
from flask_jwt_extended import jwt_required
from flask import g, request
import json
from datetime import datetime, timezone

api = Namespace('application', description='Application operations')

# Define the Application model for Swagger
app_model = api.model('Application', {
    'application_id': fields.String(description='The application ID'),
    'application_name': fields.String(description='The name of the application')
})

app_model_post = api.model('Application', {
    'application_id': fields.String(required=True, description='The application ID'),
    'application_name': fields.String(required=True, description='The name of the application'),
    'primary_owner': fields.String(required=True, description='Primary owner'),
    'secondary_owner': fields.String(required=False, description='Application user')
})

class ApplicationResource(Resource):
    @api.doc('get_applications')  # API documentation for this endpoint
    @api.marshal_with(app_model, as_list=True)  # Format output according to app_model
    @token_required
    def get(self):
        token_details = g.decoded_token
        user_email = token_details['preferred_username']
        db_connection = None
        cursor = None  # Initialize cursor to None
        try:
            # Connect to the database
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            rai_data = request.args.get('rai', False)    
            # Check if the user is an admin
            admin_check_query = 'SELECT 1 FROM shared.admin_users WHERE email = ? and is_active = 1'
            cursor.execute(admin_check_query, (user_email.lower(),))
            is_admin = cursor.fetchone() is not None
            # If user is an admin, retrieve all applications
            if is_admin:
                query = 'SELECT * FROM shared.application'
                cursor.execute(query)
            elif rai_data:
                # Otherwise, retrieve applications based on owner
                query = 'SELECT * FROM shared.application WHERE owner = ?'
                cursor.execute(query, (user_email.lower()))
            else:
                # Otherwise, retrieve applications based on owner or app_user
                query = 'SELECT * FROM shared.application WHERE owner = ? OR app_user = ?'
                cursor.execute(query, (user_email.lower(), user_email.lower()))

            applications = cursor.fetchall()
            applications.sort(key=lambda x: x[1])
            # Prepare data for response
            applications_data = []
            for app in applications:
                applications_data.append({
                    'application_id': app[0],
                    'application_name': app[1],
                })

            return applications_data, 200
        except Exception as e:
            print(f"Database connection failed: {e}")
            return {'message': 'Database connection failed'}, 500
        finally:
            if cursor:  # Only close the cursor if it was successfully created
                cursor.close()
            if db_connection:  # Only close the connection if it was successfully created
                db_connection.close()
                
    
    @api.expect(app_model_post)
    @api.doc('create_application')
    @token_required
    def post(self):
        request_data = request.get_json()
        application_id = request_data.get('application_id') #client-id
        application_name = request_data.get('application_name')
        primary_owner = request_data.get('primary_owner')
        secondary_owner = request_data.get('secondary_owner') 
        created_time = updated_time = datetime.now(timezone.utc)
        
        required_fields = ['application_id', 'application_name', 'primary_owner']
        missing_or_empty = [
            field for field in required_fields if not request_data.get(field) or (isinstance(request_data.get(field), str) and not request_data.get(field).strip())
        ]
        if missing_or_empty:
            return {
                "message": f"The following required fields are missing or empty: {', '.join(missing_or_empty)}"
        }, 

        db_connection = None
        cursor = None
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            cursor.execute('''
            INSERT INTO shared.application 
            (client_id, app_name, owner, app_user, created_date, updated_date) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                application_id,
                application_name,
                primary_owner,
                secondary_owner,
                created_time,
                updated_time,
                # onboarding_req_num (Optional)
            ))
            db_connection.commit()
            return {'message': 'Application created successfully'}, 201
        except Exception as e:
            print(f"Error inserting application: {e}")
            return {'message': 'Failed to create application'}, 500
        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()

# Add the resource to the namespace
api.add_resource(ApplicationResource, '/')
