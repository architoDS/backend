# resources/submit_page.py
import datetime
from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from middleware import token_required
from db import get_db_connection

api = Namespace('submit_page', description='Submit page operations')

# Swagger models (same as before)
role_model = api.model('Role', {
    'role': fields.String(required=True),
    'message': fields.String(required=True)
})
variable_model = api.model('Variable', {
    'name': fields.String(required=True),
    'default_value': fields.String(required=False),
    'description': fields.String(required=False)
})
prompt_model = api.model('Prompt', {
    'application_id': fields.String(required=True),
    'prompt_name': fields.String(required=True),
    'prompt_version': fields.String(required=False, example='1'),
    'prompt_type': fields.String(required=True),         # Public/Private
    'llm_tested_with': fields.String(required=True),
    'interaction_type': fields.String(required=True),    # Single Turn / Multi Turn
    'description': fields.String(required=True),
    'roles': fields.List(fields.Nested(role_model)),
    'variables': fields.List(fields.Nested(variable_model)),
    'usage_example': fields.String(required=False)
})

@api.route('/form-data')
class PromptFormData(Resource):
    @api.doc('get_form_data')
    @token_required
    def get(self):
        """
        Fetch dropdowns from DB (no ORM).
        Adjust table/column names if different in your DB.
        """
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Applications
            cur.execute("SELECT application_id, application_name FROM base.applications")
            apps = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # LLMs / Models
            cur.execute("SELECT model_id, model_name FROM base.models")
            llms = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

            # Static
            interaction_types = ["Single Turn", "Multi Turn"]
            variable_types = ["String", "Number", "URL", "Boolean"]

            return jsonify({
                "applications": apps,
                "llms": llms,
                "interaction_types": interaction_types,
                "variable_types": variable_types
            })
        except Exception as e:
            print("form-data error:", e)
            return jsonify({"message": "Error fetching dropdowns"}), 500
        finally:
            try:
                cur.close(); conn.close()
            except: pass

@api.route('/submit_page')
class SubmitPrompt(Resource):
    @api.expect(prompt_model)
    @api.doc('create_prompt')
    @token_required
    def post(self):
        """
        Save prompt (and optionally roles/variables) using raw SQL like prompt_lib.py
        """
        data = request.json
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            prompt_id = f"prompt_{int(datetime.datetime.utcnow().timestamp())}"
            now = datetime.datetime.utcnow()

            # Insert into base.prompt_lib (align columns to your table!)
            cur.execute("""
                INSERT INTO base.prompt_lib (
                    prompt_id, app_name, llm_tested_with, description, category,
                    creation_date, last_modified_date, usage_examples, author,
                    version, is_current, prompt_type, interaction_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt_id,
                data.get('application_id'),          # if your column is app_name, map accordingly
                data.get('llm_tested_with'),
                data.get('description'),
                "General",
                now, now,
                data.get('usage_example'),
                "System",
                int(data.get('prompt_version', 1)),
                1,
                data.get('prompt_type'),
                data.get('interaction_type')
            ))

            # OPTIONAL: if you have child tables, insert roles/variables too
            # Example tables: base.prompt_roles, base.prompt_variables
            # for r in data.get('roles', []):
            #     cur.execute("INSERT INTO base.prompt_roles (prompt_id, role, message) VALUES (?, ?, ?)",
            #                 (prompt_id, r['role'], r['message']))
            # for v in data.get('variables', []):
            #     cur.execute("""
            #         INSERT INTO base.prompt_variables (prompt_id, name, default_value, description)
            #         VALUES (?, ?, ?, ?)
            #     """, (prompt_id, v['name'], v.get('default_value'), v.get('description')))

            conn.commit()
            return jsonify({"message": "Prompt created", "prompt_id": prompt_id})
        except Exception as e:
            print("submit error:", e)
            try: conn.rollback()
            except: pass
            return jsonify({"message": "Error saving prompt"}), 500
        finally:
            try:
                cur.close(); conn.close()
            except: pass

# Add resource to the API
api.add_resource(SubmitPrompt, '/')