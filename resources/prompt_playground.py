from flask_restx import Resource, fields, Namespace  # type: ignore # Use flask-restplus instead of flask-restx
from db import get_db_connection
from middleware import token_required
from flask import g, request
import requests, json, time
from config import Config
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from resources.response_format import convert_to_valid_json_string , transform_data

api = Namespace('Playground', description='Playground operations')

def get_model_data(model_id, model_name):
    db_connection = get_db_connection()
    cursor = db_connection.cursor()
    if model_id and model_name:
        # Query for fetching model details if the model is provided
        query = '''
            SELECT model_id, model_name, model_provider 
            FROM base.models 
            WHERE model_id = ? and model_name = ?
        '''
        cursor.execute(query, model_id, model_name)
        results = cursor.fetchall()

    return [{
        'model_id': row[0],
        'model_name': row[1],
        'model_provider': row[2],
    } for row in results]  

def get_client_secret():
    
    key_vault_rg=Config.key_vault_rg
    key_vault_secret=Config.key_vault_secret
    KEY_VAULT_URL = f"https://{key_vault_rg}.vault.azure.net"
    secret_name = f"{key_vault_secret}"

    credential = DefaultAzureCredential()
    # Use the correct secret client initialization
    secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)
    
    # Fetch the secret using get_secret method
    try:
        retrieved_secret = secret_client.get_secret(secret_name)
        return retrieved_secret.value
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None

class PlaygroundResource(Resource):
    @api.doc('get_playground')  # API documentation for this endpoint
    @token_required
    def get(self):
        db_connection = None
        cursor = None  # Initialize cursor to None
        try:
            # Connect to the database
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            remove_model_name = ['codellama_13b_python_hf', 'llamaguard_7b']
            query = '''
                SELECT DISTINCT model_id, model_name 
                FROM base.models 
                WHERE active = ? 
                AND model_type != ? 
                AND model_name NOT IN ({})
            '''.format(','.join(['?'] * len(remove_model_name)))
            # Execute the query
            cursor.execute(query, ('true', 'Embedding') + tuple(remove_model_name))
            models = cursor.fetchall()
            
            # Prepare data for response
            models_data = []
            for model in models:
                models_data.append({
                    'model_id': model[0],
                    'model_name': model[1],
                })

            return models_data, 200
        except Exception as e:
            print(f"Database connection failed: {e}")
            return {'message': 'Database connection failed'}, 500
        finally:
            if cursor:  # Only close the cursor if it was successfully created
                cursor.close()
            if db_connection:  # Only close the connection if it was successfully created
                db_connection.close()
    
              
    @api.doc('playground_createion ')  # Documentation for the POST method
    @token_required
    def post(self):
        auth_header = request.headers.get('Authorization')
        user_token = auth_header.split(" ")[1]
        token_details = g.decoded_token
        app_id = token_details.get('aud')
        
        client_secret = get_client_secret()
        if not client_secret:
            print("Failed to retrieve client secret")
            return None

        request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": Config.CLIENT_ID,
            "client_secret": client_secret, 
            "assertion": user_token,
            "scope": Config.APIM_SCOPE,
            "requested_token_use": "on_behalf_of"
        }

        url = f"https://login.microsoftonline.com/{Config.TENANT_ID}/oauth2/v2.0/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(url, headers=headers, data=request_data)
        
        if response.status_code == 200:
            print("Request successful!")
            response_data = response.json()
        else:
            return {"message": "Failed to fetch access token", "error": response.text}, response.status_code
        
        try:
            token = response_data['access_token']
            prompt_data = json.loads(request.data)
            headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'Ocp-Apim-Subscription-Key': Config.Subscription_key
                }
            openai_baseurl = Config.APIM_URL+"openai-embeddings"
            codellama_baseurl = Config.APIM_URL+"codellama"
            llama_baseurl = Config.APIM_URL+"llama"
            gemini_baseurl=Config.APIM_URL+"gemini"
            custom_baseurl=Config.APIM_URL+"custom"
            dbrx_baseurl=Config.APIM_URL+"dbrx_model"
            dbrx_emb_baseurl=Config.APIM_URL+"dbrx-embeddings"
            phi3_baseurl=Config.APIM_URL+"phi-model"
            openai3_baseurl=Config.APIM_URL+"openai3"
            openai4_baseurl=Config.APIM_URL+"openai4"
            query_baseurl=Config.APIM_URL+"custom/custom-model"
            google_emurl=Config.APIM_URL+"google-embeddings"
            dbrx_baseurl_emb=Config.APIM_URL+"dbrx-embeddings"
            o1_baseurl=Config.APIM_URL+"o1"
            o3_baseurl=Config.APIM_URL+"o1"
            deepseek_baseurl=Config.APIM_URL+"deepseek"
            
            result_data = []
            for i in prompt_data:
                model_data = get_model_data(i['model_id'], i['model_name'])
                if model_data:
                    model_id = model_data[0]['model_id']
                    model_name= model_data[0]['model_name']
                    model_identified = model_data[0]['model_provider']
                else:
                    model_id = i['model_id'],
                    model_name = i['model_name']
                prompt = i['prompt']
                o1_basejson = {
                    "messages": [{"role": "user", "content": prompt}]
                }
                o3_basejson = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 128
                }
                 
                openai_basejson = {
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 256
                }
                completion_basejson = {
                    "prompt": [prompt],
                    "max_tokens": 256
                }
                codellama_basejson = {
                    "prompt": [prompt],
                    "max_tokens": 256
                }
                phi2_basejson = {
                    "prompt": prompt,
                    "max_tokens": 256
                }
                gemini_basejson = {
                    "messages": [
                        {
                            "role": "user",
                            "content": [[prompt]]
                        }
                    ],
                    "max_tokens": 256
                }
                embedding = {
                        "input": prompt
                }
                customemodel_basejson_meta_llama = {
                    "dataframe_split": {
                        "columns": [
                            "prompt",
                            "temperature",
                            "max_tokens",
                            "model_id",
                            "query_context"
                        ],
                        "data": [
                            [
                                prompt,
                                0.7,  
                                256,  
                                model_id,  
                                ""  
                            ]
                        ]
                    }
                }
                query_basejson = {
                    "client_request_id":app_id,
                    "dataframe_split": {
                        "columns": [
                            "prompt",
                            "temperature",
                            "max_tokens",
                            "model_id",
                            "query_context"
                        ],
                        "data": [
                            [
                                prompt,
                                0.7,  
                                256,  
                                model_id,  
                                "" 
                            ]
                        ]
                    }
                }
                openai_35_basejson = {
                    "prompt": f"{prompt}",
                    "max_tokens": 256
                }
                if "openai" in model_identified.lower() and  "text-embedding" in model_name.lower():
                        url = openai_baseurl +"/"+ model_id
                        post_str = (url, embedding)
                elif "openai" in model_identified.lower() and "text_embedding_3" in model_name.lower():
                        url = openai_baseurl +"/"+ model_id
                        post_str = (url, embedding)
                elif "openai" in model_identified.lower() and  "gpt_4_turbo" in model_name.lower(): 
                        url = openai4_baseurl +"/"+ model_id
                        openai_basejson["messages"][0]["content"] = prompt
                        post_str = (url, openai_basejson)
                elif "openai" in model_identified.lower() and  "o3" in model_name.lower():
                        url = o3_baseurl +"/"+ model_id
                        o3_basejson["messages"][0]["content"] = prompt
                        post_str = (url, o3_basejson) 
                elif "openai" in model_identified.lower() and "gpt-3.5-turbo" in model_name.lower() and "completion" in model_id.lower():
                        url = openai3_baseurl +"/"+ model_id
                        openai_35_basejson["prompt"] = prompt
                        post_str = (url, openai_35_basejson) 
                elif "openai" in model_identified.lower() and  "gpt-3.5-turbo" in model_name.lower(): 
                        url = openai3_baseurl +"/"+ model_id
                        openai_basejson["messages"][0]["content"] = prompt
                        post_str = (url, openai_basejson)
                elif "openai" in model_identified.lower() and  "gpt-4" in model_name.lower():
                        url = openai4_baseurl +"/"+ model_id
                        openai_basejson["messages"][0]["content"] = prompt
                        post_str = (url, openai_basejson)      
                elif "openai" in model_identified.lower() and  "o1" in model_name.lower():
                        url = o1_baseurl +"/"+ model_id
                        o1_basejson["messages"][0]["content"] = prompt
                        post_str = (url, o1_basejson) 
                elif "openai" in model_identified.lower() and  "deepseek" in model_name.lower():
                        url = deepseek_baseurl +"/"+ model_id
                        openai_basejson["messages"][0]["content"] = prompt
                        post_str = (url, openai_basejson)   
                elif "gemini" in model_identified.lower() or "google cloud vertex ai" in model_identified.lower() and  "text-embedding" in model_name.lower():
                        url = google_emurl +"/"+ model_id
                        post_str = (url, embedding)  
                elif "gemini" in model_identified.lower() or "google cloud vertex ai" in model_identified.lower():
                    url = query_baseurl
                    post_str = (url,query_basejson)
                elif "dbrx" in model_identified.lower() and "large-en" in model_name.lower():
                        url = dbrx_baseurl_emb +"/"+ model_id
                        post_str = (url, embedding)        
                elif "dbrx" in model_identified.lower():
                        url = query_baseurl
                        post_str = (url,query_basejson)   
                        # customemodel_basejson_meta_llama["messages"][0]["content"] = text
                        # post_str = (url, customemodel_basejson_meta_llama)
                elif "emb" in model_identified.lower():
                        url = dbrx_emb_baseurl +"/"+ model_id
                        post_str = (url, embedding)    
                elif "completion" in model_identified.lower():
                        url = openai_baseurl +"/"+ model_id
                        post_str = (url, completion_basejson)      
                elif "phi2" in model_name.lower():
                        url = query_baseurl
                        post_str = (url,query_basejson)
                elif "phi3" in model_name.lower():
                        url = phi3_baseurl +"/"+ model_id
                        post_str = (url,openai_basejson)
                elif "codellama" in model_name.lower():
                        url = codellama_baseurl +"/"+ model_id
                        post_str = (url, codellama_basejson)           
                elif "meta-llama" in model_identified.lower() or "databricks" in model_identified.lower():
                        url = query_baseurl
                        post_str = (url,query_basejson)   
                else:
                        return {"error": "Unsupported model provider"}, 400
                print("url_generated====>",post_str[0])
                print("json_generated===>",post_str[1])
  
            # Send the POST request
                try:
                    start_time = time.time()
                    response = requests.post(post_str[0], headers=headers, json=post_str[1])
                    if response.text and response.text.endswith('2198766\",\"type\":null}}}') and model_identified.lower() == "azure openai" and response.status_code == 400:
                        valid_response = convert_to_valid_json_string(response.text)
                        converted_response = transform_data(valid_response)
                        converted_response_json = json.loads(converted_response)
                        result_data.append({
                        "message": "Model response received",
                        "model": model_name,
                        "response_data": converted_response_json
                        })
                    else:
                        end_time = time.time()
                        response.raise_for_status()  # Raises an error for bad responses
                        response_data = response.json()
                        latency = end_time - start_time               
                        
                        if not post_str[0].endswith("custom/custom-model"):
                            result_data.append({
                                    "message": "Model response received",
                                    "response_data": response_data,
                                    "latency": latency
                                })
                        if post_str[0].endswith("custom/custom-model"):
                            result_data.append(
                                { "message": "Model response received", "model": model_name, "response_data": response_data}
                            )    
                except requests.exceptions.HTTPError as http_err:
                    if '403' in str(http_err) or 'Forbidden' in str(http_err):
                        result_data.append({
                            "error_code":"PERMISSION_DENIED",
                            "message":"You do not have permission to query the endpoint",
                            "model_name": model_name,
                            "model_id": model_id
                        })
                    elif '400' in str(http_err) or 'Forbidden' in str(http_err):
                        result_data.append({
                            "error_code":"Bad Request",
                            "status_code": 400,
                            "message":"The response was filtered due to the prompt triggering content management policy. Please modify your prompt and retry.",
                            "model_name": model_name,
                            "model_id": model_id
                        })
                    else:
                        return {"error": "Model request failed and url is not giving any data", "details": str(http_err), "response": response.text}, 500
            return result_data
        except Exception as e:
                return {"error": "An error occurred while making the model request", "details": str(e)}, 500


# Add the resource to the namespace
api.add_resource(PlaygroundResource, '/')
