from db import get_db_connection
from flask_restful import Resource, request
from flask_restx import Resource, Namespace
from middleware import token_required
from flask import g
import logging


logging.basicConfig(level=logging.INFO)

api = Namespace('admin_check', description='Admin check operations')

class AdminResource(Resource):
    @token_required
    def get(self):
        token_details = g.decoded_token
        user_email = token_details['preferred_username'].lower()
        db_connection = None
        cursor = None  # Initialize cursor to None
        try:
            # Connect to the database
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Check if the user is an admin
            admin_check_query = 'SELECT 1 FROM shared.admin_users WHERE email = ? AND is_active = 1'
            cursor.execute(admin_check_query, (user_email,))
            is_admin = cursor.fetchone() is not None

            # Check if the user is the owner of any application
            owner_check_query = 'SELECT 1 FROM shared.application WHERE owner = ?'
            cursor.execute(owner_check_query, (user_email,))
            is_owner = cursor.fetchone() is not None

            # Return both admin and owner status in the response
            return {
                'is_admin': is_admin,
                'is_owner': is_owner
            }, 200

        except Exception as e:
            # Catch any error and log it
            logging.error(f"An error occurred: {e}")
            return {'message': 'Internal Server Error', 'details': str(e)}, 500

        finally:
            # Ensure that the cursor and connection are properly closed
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()


# Add the resource to the namespace
api.add_resource(AdminResource, '/')