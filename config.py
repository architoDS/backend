import os,logging
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)

class Config:
    env = os.getenv("ENVIRONMENT")
    SERVER = os.getenv('SERVER')
    DATABASE = os.getenv('DATABASE')
    DRIVER = os.getenv('DRIVER')
    CLIENT_ID = os.getenv('CLIENT_ID')
    TENANT_ID= os.getenv('TENANT_ID')
    AUDIENCE= os.getenv('AUDIENCE')
    DATABRICKS = os.getenv('DATABRICKS')
    APIM_URL= os.getenv('APIM_URL')
    Subscription_key = os.getenv('Subscription_key')
    APIM_CLIENT_ID = os.getenv('APIM_CLIENT_ID')
    APIM_CLIENT_SECRET = os.getenv('APIM_CLIENT_SECRET')
    APIM_SCOPE = os.getenv('APIM_SCOPE')
    key_vault_rg = os.getenv('key_vault_rg')
    key_vault_secret = os.getenv('key_vault_secret')
load_dotenv()