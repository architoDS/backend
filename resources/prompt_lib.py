# prompt_lib.py
from datetime import datetime, timedelta, date
import uuid

from flask import request, jsonify
from flask_restx import Resource, Namespace, fields  # type: ignore

# keep these if you’ll switch to DB later; unused while USE_INMEMORY=True
# from db import get_db_connection
from middleware import token_required

api = Namespace('prompt_lib', description='Prompt lib operations')

# ============================= In-memory stub (toggle off when DB is ready) =============================
USE_INMEMORY = True
CURRENT_USER_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

PROMPTS = [
    {
        "prompt_id": "11111111-1111-1111-1111-111111111111",
        "title": "Category-Level Savings Identifier",
        "description": "Identify cost-saving and supplier consolidation opportunities across selected categories and business units.",
        "prompt_type": "public",
        "owner_user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "origin_creator_user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "forked_from_prompt_id": None,
        "forked_from_version_id": None,
        "created_at": "2025-08-12T10:00:00Z",
        "updated_at": "2025-08-20T10:00:00Z",
        "app_name": "DemoApp",
        "latest_version": {
            "version_id": "11111111-2222-3333-4444-555555555555",
            "version_no": 3,
            "created_at": "2025-08-20T10:00:00Z",
            "created_by": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        },
        "parameters": [
            {"name": "category", "type": "string[]", "default_value": ["Home Care", "Beauty & Wellbeing"]},
            {"name": "business_unit", "type": "string", "default_value": "Global"},
            {"name": "region", "type": "string", "default_value": "EU"},
            {"name": "time_window", "type": "string", "default_value": "Last 12 months"}
        ],
        "tags": ["Spend", "Cost Benchmarking"],
        "endpoint": {
            "endpoint_id": "ep-100",
            "provider": "openai",
            "task": "generation",
            "ab": {
                "enabled": True,
                "arms": [
                    {"model_name": "gpt-4o", "served_model_id": "sm-1", "traffic_percentage": 60},
                    {"model_name": "llama-3.1-405b", "served_model_id": "sm-2", "traffic_percentage": 40}
                ],
                "split_label": "A/B 60/40"
            }
        },
        "governance": {
            "rate_limits": {"calls": 500, "renewal_period": "1d"},
            "guardrails": {"pii_behaviour": "mask", "safety": "strict"}
        },
        "stats_30d": {"runs": 128, "avg_latency_ms": 1420, "total_cost": 18.74}
    },
    {
        "prompt_id": "22222222-2222-2222-2222-222222222222",
        "title": "Supply Risk Detector by Category",
        "description": "Highlight geopolitical, climate, or logistical risks for key supply chains by category.",
        "prompt_type": "private",
        "owner_user_id": CURRENT_USER_ID,
        "origin_creator_user_id": CURRENT_USER_ID,
        "forked_from_prompt_id": "11111111-1111-1111-1111-111111111111",
        "forked_from_version_id": "11111111-2222-3333-4444-555555555555",
        "created_at": "2025-08-22T09:10:00Z",
        "updated_at": "2025-08-22T09:10:00Z",
        "app_name": "RiskApp",
        "latest_version": {
            "version_id": "22222222-aaaa-bbbb-cccc-333333333333",
            "version_no": 1,
            "created_at": "2025-08-22T09:10:00Z",
            "created_by": CURRENT_USER_ID
        },
        "parameters": [
            {"name": "category", "type": "string[]", "default_value": ["Home Care"]},
            {"name": "region", "type": "string", "default_value": "APAC"},
            {"name": "risk_horizon", "type": "string", "default_value": "3 months"},
            {"name": "risk_types", "type": "string[]", "default_value": ["Geopolitical", "Logistics"]}
        ],
        "tags": ["Procurement", "Supply Risk"],
        "endpoint": {
            "endpoint_id": "ep-200",
            "provider": "azure",
            "task": "generation",
            "ab": {
                "enabled": False,
                "arms": [{"model_name": "gpt-4o-mini", "served_model_id": "sm-3", "traffic_percentage": 100}],
                "split_label": "Single model"
            }
        },
        "governance": {
            "rate_limits": {"calls": 200, "renewal_period": "1d"},
            "guardrails": {"pii_behaviour": "block", "safety": "moderate"}
        },
        "stats_30d": {"runs": 12, "avg_latency_ms": 980, "total_cost": 1.92}
    },
    {
        "prompt_id": "33333333-3333-3333-3333-333333333333",
        "title": "Logistics Optimization Planner",
        "description": "Recommend optimized warehousing, shipment modes, or routes.",
        "prompt_type": "public",
        "owner_user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "origin_creator_user_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "forked_from_prompt_id": None,
        "forked_from_version_id": None,
        "created_at": "2025-07-28T08:00:00Z",
        "updated_at": "2025-08-05T12:00:00Z",
        "app_name": "LogiApp",
        "latest_version": {
            "version_id": "33333333-aaaa-bbbb-cccc-444444444444",
            "version_no": 2,
            "created_at": "2025-08-05T12:00:00Z",
            "created_by": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        },
        "parameters": [
            {"name": "origin", "type": "string", "default_value": "Rotterdam"},
            {"name": "destination", "type": "string", "default_value": "Mumbai"},
            {"name": "mode", "type": "enum", "default_value": "Sea"},
            {"name": "constraints", "type": "string[]", "default_value": ["Min cost", "Max OTIF"]}
        ],
        "tags": ["Supply Chain"],
        "endpoint": {
            "endpoint_id": "ep-300",
            "provider": "vertexai",
            "task": "planning",
            "ab": {
                "enabled": True,
                "arms": [
                    {"model_name": "gemini-1.5-pro", "served_model_id": "sm-4", "traffic_percentage": 50},
                    {"model_name": "gpt-4.1",        "served_model_id": "sm-5", "traffic_percentage": 50}
                ],
                "split_label": "A/B 50/50"
            }
        },
        "governance": {
            "rate_limits": {"calls": 100, "renewal_period": "1d"},
            "guardrails": {"pii_behaviour": "allow", "safety": "standard"}
        },
        "stats_30d": {"runs": 64, "avg_latency_ms": 1650, "total_cost": 9.51}
    }
]


def _primary_model_name(p: dict) -> str:
    ab = p.get("endpoint", {}).get("ab", {})
    if ab.get("enabled") and ab.get("arms"):
        return ab["arms"][0].get("model_name", "")
    arms = p.get("endpoint", {}).get("arms", [])
    if arms:
        return arms[0].get("model_name", "")
    return ""


def _to_prompt_lib_row(p: dict, index: int) -> dict:
    created = datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")).date()
    updated = datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00")).date()
    return {
        "id": index,
        "prompt_id": p["prompt_id"],
        "app_name": p.get("app_name", "DemoApp"),
        "title": p.get("title"),
        "llm_tested_with": _primary_model_name(p),
        "description": p.get("description"),
        "category": "General",  # default for demo
        "creation_date": created,          # fields.Date → date object
        "last_modified_date": updated,     # fields.Date → date object
        "usage_examples": None,
        "author": p.get("origin_creator_user_id"),
        "user_id": p.get("owner_user_id"),
        "version": p["latest_version"]["version_no"],
        "version_id": p["latest_version"]["version_id"],
        "is_current": True,
    }


def _find_prompt(prompt_id: str):
    return next((x for x in PROMPTS if x["prompt_id"] == prompt_id), None)


def _next_version_no(prompt_id: str) -> int:
    p = _find_prompt(prompt_id)
    if not p:
        return 1
    return int(p["latest_version"]["version_no"]) + 1


# ============================= Swagger models =============================
PromptLibResponse = api.model('PromptLib', {
    'id': fields.String(required=False, description='Row index (computed)'),
    'prompt_id': fields.String(required=True, description='ID of the prompt', example='PROMPT-001'),
    'app_name': fields.String(required=True, description='Application name', example='SalesApp'),
    'title': fields.String(required=True, description='Human-friendly title', example='Quarterly Revenue Summary'),
    'llm_tested_with': fields.String(description='Model tested against', example='gpt-4o'),
    'description': fields.String(description='Description', example='Summarizes quarterly revenue.'),
    'category': fields.String(description='Category', example='Finance'),
    'creation_date': fields.Date(description='Creation date', example='2024-09-15'),
    'last_modified_date': fields.Date(description='Last modified date', example='2024-10-01'),
    'usage_examples': fields.String(description='Usage examples', example='Compute annual revenue'),
    'author': fields.String(description='Author', example='John Doe'),
    'user_id': fields.String(description='Owner user id', example='user-123'),
    'version': fields.Integer(description='Version number', example=2),
    'version_id': fields.String(description='Unique version UUID'),
    'is_current': fields.Boolean(description='Is current version?', example=True),
})

CreatePromptRequest = api.model('CreatePrompt', {
    'prompt_id': fields.String(required=True, description='Prompt UUID'),
    'app_name': fields.String(required=True, description='Application name'),
    'title': fields.String(required=True, description='Prompt title'),
    'description': fields.String(required=True, description='Prompt description'),
    'author': fields.String(description='Author'),
    'user_id': fields.String(description='Owner user id'),
    'llm_tested_with': fields.String(description='Primary model name'),
    'tags': fields.List(fields.String, description='Tags'),
    # optional extras you can pass and we echo into the stub structure
    'prompt_type': fields.String(description='public|private'),
    'parameters': fields.List(fields.Raw, description='Parameter schema'),
    'provider': fields.String(description='Endpoint provider (e.g., openai)'),
    'task': fields.String(description='Endpoint task (e.g., generation)'),
})

SearchPromptRequest = api.model('SearchPrompt', {
    'app_name': fields.String(required=True, description='Search by application name'),
})


# ============================= Resources =============================
@api.route('/')
class PromptLibResource(Resource):
    @api.doc('get_prompt_lib')
    @api.expect(api.parser().add_argument('prompt_id', type=str, required=False,
                                          help='prompt_id to fetch a specific prompt'))
    @api.marshal_with(PromptLibResponse, as_list=True)
    @token_required
    def get(self):
        """Return all prompts (or a specific one by prompt_id)."""
        prompt_id = request.args.get('prompt_id')

        if USE_INMEMORY:
            try:
                rows = []
                if prompt_id:
                    p = _find_prompt(prompt_id)
                    if p:
                        rows.append(_to_prompt_lib_row(p, 1))
                else:
                    for i, p in enumerate(PROMPTS, start=1):
                        rows.append(_to_prompt_lib_row(p, i))
                return rows, 200
            except Exception as e:
                print(f"[INMEMORY] Error: {e}")
                return jsonify({"message": "An error occurred while fetching data"}), 500

        # ==== DB path (keep for later) ====
        # try:
        #     db = get_db_connection()
        #     cur = db.cursor()
        #     if prompt_id:
        #         cur.execute('SELECT * FROM base.prompt_lib WHERE prompt_id = ? ORDER BY version DESC', (prompt_id,))
        #     else:
        #         cur.execute('''
        #             SELECT * FROM base.prompt_lib p1
        #             WHERE p1.version = (
        #                 SELECT MAX(p2.version)
        #                 FROM base.prompt_lib p2
        #                 WHERE p2.prompt_id = p1.prompt_id
        #             )
        #             AND p1.is_current = 1
        #         ''')
        #     rows = cur.fetchall()
        #     # map to PromptLibResponse...
        # finally:
        #     cur.close(); db.close()


@api.route('/create')
class PromptCreate(Resource):
    @api.doc('create_prompt')
    @api.expect(CreatePromptRequest, validate=True)
    @api.marshal_with(PromptLibResponse, as_list=False, code=201)
    @token_required
    def post(self):
        """Create a new prompt or a new version if prompt_id exists."""
        payload = request.get_json(force=True) or {}
        if not USE_INMEMORY:
            return jsonify({"message": "DB mode not implemented here"}), 501

        pid = payload['prompt_id']
        app_name = payload['app_name']
        title = payload['title']
        desc = payload['description']
        author = payload.get('author') or CURRENT_USER_ID
        owner_user_id = payload.get('user_id') or CURRENT_USER_ID
        llm_name = payload.get('llm_tested_with') or "gpt-4o"
        now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        existing = _find_prompt(pid)
        if existing:
            # create new version
            new_ver_no = _next_version_no(pid)
            new_ver_id = str(uuid.uuid4())
            existing["title"] = title
            existing["description"] = desc
            existing["app_name"] = app_name
            existing["updated_at"] = now_iso
            existing["owner_user_id"] = owner_user_id
            if "endpoint" not in existing:
                existing["endpoint"] = {"ab": {"enabled": False, "arms": [{"model_name": llm_name}]}}
            else:
                ab = existing["endpoint"].setdefault("ab", {"enabled": False, "arms": []})
                arms = ab.setdefault("arms", [])
                if arms:
                    arms[0]["model_name"] = llm_name
                else:
                    arms.append({"model_name": llm_name})

            existing["latest_version"] = {
                "version_id": new_ver_id,
                "version_no": new_ver_no,
                "created_at": now_iso,
                "created_by": owner_user_id
            }
            return _to_prompt_lib_row(existing, 1), 201

        # create brand new prompt
        new_ver_id = str(uuid.uuid4())
        new_prompt = {
            "prompt_id": pid,
            "title": title,
            "description": desc,
            "prompt_type": payload.get("prompt_type", "public"),
            "owner_user_id": owner_user_id,
            "origin_creator_user_id": owner_user_id,
            "forked_from_prompt_id": None,
            "forked_from_version_id": None,
            "created_at": now_iso,
            "updated_at": now_iso,
            "app_name": app_name,
            "latest_version": {
                "version_id": new_ver_id,
                "version_no": 1,
                "created_at": now_iso,
                "created_by": owner_user_id
            },
            "parameters": payload.get("parameters", []),
            "tags": payload.get("tags", []),
            "endpoint": {
                "endpoint_id": payload.get("endpoint_id", "ep-temp"),
                "provider": payload.get("provider", "openai"),
                "task": payload.get("task", "generation"),
                "ab": {
                    "enabled": False,
                    "arms": [{"model_name": llm_name, "served_model_id": "sm-temp", "traffic_percentage": 100}],
                    "split_label": "Single model"
                }
            },
            "governance": payload.get("governance", {}),
            "stats_30d": payload.get("stats_30d", {"runs": 0, "avg_latency_ms": 0, "total_cost": 0.0})
        }
        PROMPTS.append(new_prompt)
        return _to_prompt_lib_row(new_prompt, len(PROMPTS)), 201


@api.route('/search')
class PromptSearch(Resource):
    @api.doc('search_prompt_by_app_name')
    @api.expect(SearchPromptRequest, validate=True)
    @api.marshal_with(PromptLibResponse, as_list=True)
    @token_required
    def post(self):
        """Search prompts by app_name (legacy POST behavior)."""
        payload = request.get_json(force=True) or {}
        if not USE_INMEMORY:
            return jsonify({"message": "DB mode not implemented here"}), 501

        key = payload['app_name'].lower()
        items = []
        for i, p in enumerate(PROMPTS, start=1):
            if key and key not in p.get("app_name", "").lower():
                continue
            items.append(_to_prompt_lib_row(p, i))
        return items, 200
