from collections import defaultdict
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from db import get_db_connection
from flask_restx import Resource, Namespace, fields # type: ignore
from middleware import token_required

# Create a namespace for the API
api = Namespace('leaderboard', description='Leaderboard related operations')

# Swagger model for the response for LB_RAI
leaderboard_rai_model = api.model('Leaderboard_rai', {
    'id' : fields.String(required= False, description='ID of the prompt', example='1'),
    'model_name': fields.String(description='The name of the model'),
    'flesch_kincaid_grade': fields.Float(description='Flesch-Kincaid grade level for LB_RAI'),
    'automated_readability_index': fields.Float(description='Automated readability index for LB_RAI'),
    'flesch_reading_ease': fields.Float(description='Flesch reading ease score for LB_RAI'),
    'smog_index': fields.Float(description='SMOG index for LB_RAI'),
    'coleman_liau_index': fields.Float(description='Coleman-Liau index for LB_RAI'),
    'dale_chall_readability_score': fields.Float(description='Dale-Chall readability score for LB_RAI'),
    'gunning_fog_score': fields.Float(description='Gunning fog score for LB_RAI'),
    'linsear_write_formula': fields.Float(description='Linsear Write formula for LB_RAI'),
    'toxicity': fields.Float(description='Toxicity score for LB_RAI'),
    'perplexity': fields.Float(description='Perplexity score for LB_RAI'),
    'relevance_score': fields.Float(description='Relevance score for LB_RAI')
})

# Swagger model for the response for LB_Latency
leaderboard_latency_model = api.model('Leaderboard_latency', {
    'id' : fields.String(required= False, description='ID of the prompt', example='1'),
    'model_name': fields.String(description='The name of the model'),
    'tpot': fields.Float(description='Time per output token for LB_Latency'),
    'ttft': fields.Float(description='Time to first token for LB_Latency'),
    'throughput': fields.Integer(description='Throughput for LB_Latency')
})

leaderboard = api.model('Leaderboard', {
    "LB_latency":fields.List(fields.Nested(leaderboard_latency_model)),
    "LB_RAI" : fields.List(fields.Nested(leaderboard_rai_model))
})

# Single endpoint to get data from either LB_Latency or LB_RAI with model name
class LeaderboardResource(Resource):
    @api.doc('get_leaderboard')
    @api.marshal_with(leaderboard, as_list=True)
    @token_required
    def get(self):
        try:
            db_connection = get_db_connection()
            cursor = db_connection.cursor()
            cursor.execute('''SELECT
                                mra.model_id,
                                m.model_name,
                                SUM(mra.avg_flesch_kincaid_grade) AS flesch_kincaid_grade,
                                SUM(mra.avg_automated_readability_index) AS automated_readability_index,
                                SUM(mra.avg_flesch_reading_ease) AS flesch_reading_ease,
                                SUM(mra.avg_smog_index) AS smog_index,
                                SUM(mra.avg_coleman_liau_index) AS coleman_liau_index,
                                SUM(mra.avg_dale_chall_readability_score) AS dale_chall_readability_score,
                                SUM(mra.avg_gunning_fog_score) AS gunning_fog_score,
                                SUM(mra.avg_linsear_write_formula) AS linsear_write_formula,
                                SUM(mra.avg_toxicity) AS toxicity,
                                SUM(mra.avg_perplexity) AS perplexity,
                                SUM(mra.avg_relevance_score) AS relevance_score
                            FROM
                                dbr_report.model_requester_aggr mra
                            JOIN
                                base.models m
                            ON
                                mra.model_id = m.model_id
                            GROUP BY
                                mra.model_id, m.model_name''')
            rai_data = cursor.fetchall()
            lb_rai_result = []
            if rai_data:
                for index, rai in enumerate(rai_data, start=1):
                    lb_rai_result.append({
                        'id': index,
                        'model_name': rai[1],
                        'flesch_kincaid_grade': rai[2],
                        'automated_readability_index': rai[3],
                        'flesch_reading_ease': rai[4],
                        'smog_index': rai[5],
                        'coleman_liau_index': rai[6],
                        'dale_chall_readability_score': rai[7],
                        'gunning_fog_score': rai[8],
                        'linsear_write_formula': rai[9],
                        'toxicity': rai[10],
                        'perplexity': rai[11],
                        'relevance_score': rai[12]
                    })

            # Fetch LB_Latency data
            cursor.execute('SELECT lbl.*, m.model_name FROM dbr_report.lb_latency lbl JOIN base.models m ON lbl.model_id = m.model_id')
            latency_data = cursor.fetchall()
            lb_latency_result = []
            if latency_data:
                for index, latency in enumerate(latency_data, start=1):
                    lb_latency_result.append({
                        'id' : index,
                        'model_name': latency[4],
                        'tpot': latency[1],
                        'ttft': latency[2],
                        'throughput': latency[3]
                    })
            
            # If both results are empty, return empty list
            if not lb_rai_result and not lb_latency_result:
                return [], 200
            
            result_data = [{
                "LB_latency": lb_latency_result,
                "LB_RAI": lb_rai_result
            }]

            return result_data, 200
        except Exception as e:
            return jsonify({"message": "An error occurred while fetching data"}), 500
        finally:
            cursor.close()
            db_connection.close()

api.add_resource(LeaderboardResource, '/')
