from flask_restful import Resource
from flask_restx import Resource, Namespace
from middleware import token_required
import logging

logging.basicConfig(level=logging.INFO)

api = Namespace('index', description='Index operations')

class IndexResource(Resource):
    # Don't fetch the data at the import time, move the call to get_data to inside the function
    @token_required
    def get(self):
        return {'message': 'Welcome to the Flask test with space new!'}, 200

# Add the resource to the namespace
api.add_resource(IndexResource, '/')
