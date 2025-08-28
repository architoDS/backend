from sqlalchemy import create_engine, Column, Date, String, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from db import get_db_connection
import uuid


# Create a base model class
Base = declarative_base()

# Define the Applications model
class Application(Base):
    __tablename__ = 'applications'
    
    application_id = Column(String(255), primary_key=True)
    application_name = Column(String(255))

    def __repr__(self):
        return f"<Application(id={self.application_id}, name={self.application_name})>"

# Define the Models model
class Model(Base):
    __tablename__ = 'models'
    
    model_id = Column(String(255), primary_key=True)
    model_name = Column(String(255))
    onboarded_date = Column(Date)
    active = Column(String(255))
    security_clearance = Column(String(255))
    IT_clearance = Column(String(255))
    legal_clearance = Column(String(255))
    model_provider = Column(String(255))
    deployment_name = Column(String(255))
    model_type = Column(String(255))
    endpoint_url = Column(String(1000))
    updated_date = Column(Date)
    update_comments = Column(String(1000))

    def __repr__(self):
        return f"<Model(id={self.model_id}, name={self.model_name})>"

# Define the ApplicationModels model
class ApplicationModel(Base):
    __tablename__ = 'application_models'
    
    sr_no = Column(String(1000), primary_key=True)
    application_id = Column(String(1000))
    model_id = Column(String(1000))
    onboarded_date = Column(Date)
    renewal_date = Column(Date)

    def __repr__(self):
        return f"<ApplicationModel(sr_no={self.sr_no}, app_id={self.application_id}, model_id={self.model_id})>"

# Define the PromptLib model
class PromptLib(Base):
    __tablename__ = 'prompt_lib'
    
    prompt_id = Column(String(1000), primary_key=True)
    application_id = Column(String(1000))
    model_tested_against = Column(String(1000))
    description = Column(String(1000))
    category = Column(String(1000))
    creation_date = Column(Date)
    last_modified_date = Column(Date)
    usage_examples = Column(String(1000))
    # New fields
    title = Column(String(255))
    user_id = Column(String(1000))
    # If you don't want MSSQL-specific type here, keep as String(36)
    version_id = Column(String(36), default=lambda: str(uuid.uuid4()))

    # Existing versioning
    author = Column(String(1000))
    version = Column(Integer)
    is_current = Column(Boolean)

    def __repr__(self):
        return f"<PromptLib(id={self.prompt_id}, app_id={self.application_id})>"

# new model for variable name 28 August 2025
class PromptVariable(Base):
    __tablename__ = 'prompt_variable'

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(String(1000), ForeignKey('prompt_lib.prompt_id'))
    variable_name = Column(String(255))
    variable_type = Column(String(255))   # e.g. string, int, etc.
    default_value = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<PromptVariable(name={self.variable_name}, prompt={self.prompt_id})>"

# Define the ModelStatus model
class ModelStatus(Base):
    __tablename__ = 'model_status'
    
    application_id = Column(String(1000), primary_key=True)
    model_id = Column(String(1000), primary_key=True)
    content_filter = Column(String(1000))
    hallucination = Column(String(1000))
    llm_as_a_judge = Column(String(1000))

    def __repr__(self):
        return f"<ModelStatus(app_id={self.application_id}, model_id={self.model_id})>"

# Create the database engine
def create_db_engine():
    conn = get_db_connection()
    if conn is not None:
        engine = create_engine(conn)
        return engine
    return None

# Create all tables in the database
# Base.metadata.create_all(create_db_engine())
