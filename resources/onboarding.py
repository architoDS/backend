from flask_restx import Resource, fields, Namespace
from db import get_db_connection
from middleware import token_required
from flask import g, request
import json , requests
from datetime import datetime,timezone
from config import Config

api = Namespace('onboarding', description='Onboarding operations')

onboarding_form_model = api.model('OnboardingForm', {
    'environment': fields.List(fields.String, required=True, description='Environment', example=['non-prod']),
    'application_name': fields.String(required=True, description='Application Name', example='some name'),
    'model_name': fields.List(fields.String, required=True, description='Model Name', example=['dbr_phi2_completion']),
    'model_id': fields.List(fields.String, required=True, description='Model Id', example=['az_openai_gpt','az_openai_gpt-4o-mini_chat']),
    'primary_owner': fields.String(required=True, description='Primary Owner', example='nice'),
    'wl3_approver': fields.String(required=False, description='WL3 Approver', example='upfront'),
    'application_description': fields.String(required=True, description='Application Description', example='good description'),
    'secondary_owner': fields.String(required=False, description='Secondary Owner', example=''),
    'icc': fields.String(required=False, description='ICC', example='dsa'),
    'cc': fields.String(required=False, description='CC', example='dee'),
    'llm_as_judge': fields.Boolean(required=False, description='LLM as Judge', example=False),
    'hallucination': fields.Boolean(required=False, description='Hallucination', example=False),
    'aif_rag_access': fields.Boolean(required=False, description='AIF RAG Access', example=False),
    'ai_inventory_id': fields.String(required=True, description='AI Inventory ID', example='some-id'),
    'onboardingstatus': fields.String(required= False, description='Onboarding status', example='', nullable=True),
    'adgroupforappaccess': fields.List(fields.String, required=True, description='Model Name', example=['bnlwe-ai04-d-931039-openai','bnlwe-ai04-d-931039-gemini']),
    'spn_appid_env_map': fields.List( 
        fields.Nested(api.model('SPNAppIDEnvMap', {
            'environment': fields.String(required=True, description='Environment', example='non-prod'),
            'service_principal_name': fields.String(required=True, description='Service Principal Name', example='bow'),
            'application_id': fields.String(required=True, description='Application ID', example='meo')
        })),
        required=True,
        description='SPN App ID Environment Map',
        example=[{
            'environment': 'non-prod',
            'service_principal_name': 'bow',
            'application_id': 'meo'
        }]
    )
})


class OnboardingResource(Resource):
    @api.doc('get_onboarding_form')
    @token_required
    def get(self):
        token_details = g.decoded_token
        user_email = token_details['preferred_username']
        db_connection = None
        cursor = None
        try:
            # Connect to the database
            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Check if the user is an admin
            admin_check_query = 'SELECT 1 FROM shared.admin_users WHERE email = ? and is_active = 1'
            cursor.execute(admin_check_query, (user_email.lower(),))
            is_admin = cursor.fetchone() is not None

            if is_admin:
                query = 'SELECT * FROM base.onboarding_form'
                cursor.execute(query)
            else:
                 # Otherwise, retrieve applications based on owner or app_user
                query = 'SELECT * FROM base.onboarding_form WHERE primary_owner = ? OR secondary_owner = ?'
                cursor.execute(query, (user_email.lower(), user_email.lower()))


            onboarding_form_data = cursor.fetchall()
            # prepare data for response
            columns = [desc[0] for desc in cursor.description]
            onboarding_data = [dict(zip(columns, row)) for row in onboarding_form_data]

            return onboarding_data,200
        
        except Exception as e:
            print(f"Database connection failed: {e}")
            return {'message': 'Database connection failed'}, 500
        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()


    @api.doc('create_onboarding_form')
    @api.expect(onboarding_form_model)
    @token_required
    def post(self):
        db_connection = None
        cursor = None
        
        try:
            request_data = json.loads(request.data)
            
            application_name = request_data.get('application_name')
            model_names = request_data.get('model_name', [])
            model_ids = request_data.get('model_id',[])
            primary_owner = request_data.get('primary_owner')
            wl3_approver = request_data.get('wl3_approver')
            ai_inventory_id = request_data.get('ai_inventory_id')
            application_description = request_data.get('application_description')
            secondary_owner = request_data.get('secondary_owner')
            icc = request_data.get('icc')
            cc = request_data.get('cc')
            llm_as_judge = request_data.get('llm_as_judge')
            hallucination = request_data.get('hallucination')
            aif_rag_access = request_data.get('aif_rag_access')
            onboardingstatus = None #request_data.get('onboardingstatus')
            created_time = updated_time = datetime.now(timezone.utc)
            adgroupforappaccess = request_data.get('adgroupforappaccess', [])
            # onboardedon field - part of automation task
            
            required_fields = [
                'environment',
                'application_name',
                'model_name',
                'model_id',
                'primary_owner',
                'application_description',
                'ai_inventory_id',
                'spn_appid_env_map',
                'adgroupforappaccess'
                ]
                
            missing_or_empty = [
                field for field in required_fields if not request_data.get(field) or (isinstance(request_data.get(field), list) and not request_data.get(field))
                ]
            
            if missing_or_empty:
                return {
                    "message": f"The following required fields are missing or empty: {', '.join(missing_or_empty)}"
                    }, 400


            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Loop through spn_appid_env_map to create entries
            for spn_appid_env in request_data.get('spn_appid_env_map', []):
                service_principal_name = spn_appid_env.get('service_principal_name')
                application_id = spn_appid_env.get('application_id')
                environment = spn_appid_env.get('environment')

                # llm_as_judge, hallucination ( If true)
                if(hallucination and llm_as_judge):
                    query = '''INSERT INTO shared.app_func_mapping (application_id, hallucination, llm_as_a_judge)
                       VALUES (?, ?, ?)'''
                    cursor.execute(query, (
                        application_id,
                        "yes" if hallucination else "no",
                        "yes" if llm_as_judge else "no"
                    ))

                # Insert a new record into the onboarding_form table
                query = '''INSERT INTO base.onboarding_form (service_principal_name, application_id, application_name, model_name, primary_owner, environment, wl3_approver, ai_inventory_id, application_description, secondary_owner, icc, cc, llm_as_judge, hallucination, aif_rag_access, created, updated, onboardingstatus, error_message, onboardedon, adgroupforappaccess)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)'''
                cursor.execute(query, (
                    service_principal_name,
                    application_id,
                    application_name,
                    ','.join(model_names),
                    primary_owner,
                    environment,
                    wl3_approver,
                    ai_inventory_id,
                    application_description,
                    secondary_owner,
                    icc,
                    cc,
                    "yes" if llm_as_judge else "no",
                    "yes" if hallucination else "no",
                    "yes" if aif_rag_access else "no",
                    created_time,
                    updated_time,
                    onboardingstatus,
                    None,  # error_message
                    None, # onboardedon
                    ','.join(adgroupforappaccess)
                    ))
                
                # Insert into app_model_map table - Couldn't find the existing post method for app_mode_map
                for model_id in model_ids:
                    cursor.execute('INSERT INTO shared.app_model_map (client_id,model_id) VALUES (?,?)', (
                        application_id,
                        model_id
                        ))
                    
                
                #Send the POST request to the /application endpoint
                url = f'{Config.APIM_URL}/application'
                auth_header = request.headers.get('Authorization')
                
                application_data = {
                    "application_id": application_id,
                    "application_name": application_name,
                    "primary_owner": primary_owner,
                    "secondary_owner": secondary_owner,  # app_user
                }

                if auth_header:
                    try:
                        response = requests.post(
                            url,
                            data = application_data,
                            headers={
                                'Authorization': auth_header,
                                'Content-Type': 'application/json'
                            }
                        )
                    except Exception as e:
                        return {"message": "An error occurred", "error": str(e)}, 500
                else:
                    return {"error": "Authorization header missing"}, 401
                    
                        
                # Commit the transaction
                db_connection.commit()
                        
            return {
                "message": "Onboarding form created successfully",
                }, 201
                
        except Exception as e:
            print(f"Error occurred while creating onboarding form: {e}")
            return {"message": "An error occurred", "error": str(e)}, 500
        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()


# Add resource to the API
api.add_resource(OnboardingResource, '/')
