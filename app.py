import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_restx import Api 
from datetime import timedelta 

# Initialize Flask app
app = Flask(__name__)
allowed_origins = [
    "https://bnlwe-ai04-d-930633-webapi-02.azurewebsites.net",
    "http://127.0.0.1:3000",
    "http://localhost:3000"
]

# Set up CORS with allowed origins
# CORS(app, resources={r"/*": {"origins": "https://bnlwe-ai04-d-930633-webapi-02.azurewebsites.net"}})
CORS(app, resources={r"/*": {"origins": "*"}})

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Use a strong secret key
jwt = JWTManager(app)

# Store the generated token in a global variable
GENERATED_TOKEN = None

def generate_token():
    with app.app_context():  # Use application context
        return create_access_token(identity='default_user', expires_delta=timedelta(hours=1))  # Replace with desired identity

# Generate token at startup
GENERATED_TOKEN = generate_token()

# Setup Flask-Restplus API
api = Api(app, version='1.0', title='Dashboard API', description='Unilever Dashboard API', security='Bearer Auth',
          authorizations={
              'Bearer Auth': {
                  'type': 'apiKey',
                  'in': 'header',
                  'name': 'Authorization',
                  'description': 'Add a JWT token with `Bearer` prefix (e.g., Bearer <token>)'
              }
          }
)


# Importing namespaces (not individual resources)
from resources.index import api as index_namespace
from resources.application import api as application_namespace
from resources.model import api as model_namespace
from resources.application_model import api as application_model_namespace
from resources.model_status import api as model_status_namespace
from resources.prompt_lib import api as prompt_lib_namespace
from resources.llm_dashboard_card import api as  llm_ops_dasgboard_namespace
from resources.model_usage  import api as  model_usage_namespace
from resources.metrics import api as  metrics_namespace
from resources.databricks_token import databricks_ns
from resources.leaderboard import api as leaderboard_namespace 
from resources.prompt_playground import api as playground_namespace
from resources.prompt import api as prompt_namespace
from resources.rai_usage_metrics import api as rai_usage_metrics_namespace
from resources.rai_batch_metrics import api as rai_batch_metrics_namespace
from resources.rai_safety_metrics import api as rai_safety_metrics_namespace
from resources.admin_check import api as admin_check_namespace
from resources.feedback import api as feedback_namespace
from resources.llm_usage_cost import api as llm_usage_cost_namespace
from resources.prompt_application_models import api as prompt_app_models_namespace
from resources.onboarding import api as onboarding_namespace
from resources.submit_page import api as submit_page_namespace
from resources.prompt_lib_manual import api as prompt_lib_manual
# Register namespaces with the API
api.add_namespace(index_namespace, '/index')
api.add_namespace(application_namespace, '/application')
api.add_namespace(model_namespace, '/model')
api.add_namespace(application_model_namespace, '/application_model')
api.add_namespace(model_status_namespace, '/model_status')
api.add_namespace(prompt_lib_namespace, '/prompt_lib')
api.add_namespace(llm_ops_dasgboard_namespace, '/llm_ops_dashboard')
api.add_namespace(model_usage_namespace, '/model_usage')
api.add_namespace(metrics_namespace, '/metrics')
api.add_namespace(databricks_ns, '/databricks')
api.add_namespace(leaderboard_namespace, '/leaderboard')
api.add_namespace(playground_namespace, '/playground')
api.add_namespace(prompt_namespace, '/prompt')
api.add_namespace(rai_usage_metrics_namespace,'/rai_usage_metrics')
api.add_namespace(rai_batch_metrics_namespace,'/rai_batch_metrics')
api.add_namespace(rai_safety_metrics_namespace,'/rai_safety_metrics')
api.add_namespace(admin_check_namespace,'/admin')
api.add_namespace(feedback_namespace,'/feedback')
api.add_namespace(llm_usage_cost_namespace,'/llm_usage_cost')
api.add_namespace(prompt_app_models_namespace,'/prompt_app_models')
api.add_namespace(onboarding_namespace, '/onboarding')
api.add_namespace(submit_page_namespace, '/submit_page')
api.add_namespace(prompt_lib_manual, '/prompt_lib_manual')

if __name__ == '__main__':
    app.run(debug=True)

