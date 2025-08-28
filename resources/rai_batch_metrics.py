from flask import request, g
from flask_restx import Resource, Namespace, fields  # type: ignore
from db import get_db_connection
from middleware import token_required

api = Namespace('rai_batch', description='RAI Batch metrics operations')

# Define nested models for LLMJudge metrics values
llmjudge_values_model = api.model('LLMJudgeValues', {
    'avg_answer_similarity': fields.Float(description='Average answer similarity score', example=0.80),
    'avg_answer_correctness': fields.Float(description='Average answer correctness score', example=0.90),
    'avg_answer_relevance': fields.Float(description='Average answer relevance score', example=0.85),
    'avg_faithfulness_score': fields.Float(description='Average faithfulness score', example=0.78),
})

# Define the LLMJudge result model
rai_llmjudge_result = api.model('RaiMetricsLLMJudge', {
    'month': fields.String(description='Month of the metrics', example='October'),
    'values': fields.Nested(llmjudge_values_model),
})

# Define nested models for Hallucination metrics values
hallucination_values_model = api.model('HallucinationValues', {
    'avg_hal_score': fields.Float(description='Average hallucination score', example=0.80),
})

# Define the Hallucination result model
rai_hallucination_result = api.model('RaiMetricsHallucination', {
    'month': fields.String(description='Month of the metrics', example='October'),
    'values': fields.Nested(hallucination_values_model),
})



hallucination_metrics_model = api.model('HallucinationMetrics', {
    "hallucination_metrics_yAxis": fields.List(fields.String, description="List of months for hallucination metrics", example=['October', 'November']),
    "hallucination_metrics_xaxis": fields.List(fields.Nested(rai_hallucination_result), description="List of hallucination metrics values"),
})

# Define the LLMJudge yAxis and xaxis models
llmjudge_metrics_model = api.model('LLMJudgeMetrics', {
    "llmjudge_metrics_yAxis": fields.List(fields.String, description="List of months for LLMJudge metrics", example=['October', 'November']),
    "llmjudge_metrics_xaxis": fields.List(fields.Nested(rai_llmjudge_result), description="List of LLMJudge metrics values"),
})

# Combine Hallucination and LLMJudge into the overall RAI Batch metrics model
rai_batch_metrics = api.model('RaiBatchMetrics', {
    "hallucination_metrics_yAxis": fields.List(fields.String, description="List of months for hallucination metrics", example=['October', 'November']),
    "hallucination_metrics_xaxis": fields.List(fields.Nested(rai_hallucination_result), description="List of hallucination metrics values"),
    "llmjudge_metrics_yAxis": fields.List(fields.String, description="List of months for LLMJudge metrics", example=['October', 'November']),
    "llmjudge_metrics_xaxis": fields.List(fields.Nested(rai_llmjudge_result), description="List of LLMJudge metrics values"),
})


class RaiBatchMetricsResource(Resource):
    @api.doc('get_rai_batch_metrics')
    @token_required
    @api.marshal_with(rai_batch_metrics)
    @api.expect(api.parser().add_argument('application_id', type=str, required=True, help='Application ID for metrics'))
    def get(self):
        application_id = request.args.get('application_id')

        if not application_id:
            return {"message": "Application ID is required."}, 400

        try:
            # Decode the token and retrieve the user email
            token_details = g.decoded_token
            user_email = token_details.get('preferred_username', 'Unknown User')

            db_connection = get_db_connection()
            cursor = db_connection.cursor()

            # Fetch Hallucination metrics
            cursor.execute('''
                SELECT 
                    month,
                    AVG(avg_hal_score) AS average_hal_score
                FROM 
                    dbr_report.rai_batch_metrics
                WHERE 
                    application_id = ?
                    AND task_type = 'Hallucination'
                GROUP BY 
                    month, year
                ORDER BY 
                    year DESC,  
                    CASE month
                        WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3
                        WHEN 'Apr' THEN 4 WHEN 'May' THEN 5 WHEN 'Jun' THEN 6
                        WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 WHEN 'Sep' THEN 9
                        WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
                    END
            ''', (application_id,))
            hallucination_metrics = cursor.fetchall()

            hallucination_result = [
                {
                    'month': row[0],
                    'values': {
                        'avg_hal_score': row[1],
                    }
                } for row in hallucination_metrics
            ]

            hallucination_yAxis = [row[0] for row in hallucination_metrics]

            # Fetch LLMJudge metrics
            cursor.execute('''
                SELECT 
                    month,
                    AVG(avg_answer_similarity) AS avg_answer_similarity,
                    AVG(avg_answer_correctness) AS avg_answer_correctness,
                    AVG(avg_answer_relevance) AS avg_answer_relevance,
                    AVG(avg_faithfulness_score) AS avg_faithfulness_score
                FROM 
                    dbr_report.rai_batch_metrics
                WHERE 
                    application_id = ?
                    AND task_type = 'LLMJudge'
                GROUP BY 
                    month, year
                ORDER BY 
                    year DESC,  
                    CASE month
                        WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3
                        WHEN 'Apr' THEN 4 WHEN 'May' THEN 5 WHEN 'Jun' THEN 6
                        WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8 WHEN 'Sep' THEN 9
                        WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
                    END
            ''', (application_id,))
            llmjudge_metrics = cursor.fetchall()

            llmjudge_result = [
                {
                    'month': row[0],
                    'values': {
                        'avg_answer_similarity': row[1],
                        'avg_answer_correctness': row[2],
                        'avg_answer_relevance': row[3],
                        'avg_faithfulness_score': row[4],
                    }
                } for row in llmjudge_metrics
            ]

            llmjudge_yAxis = [row[0] for row in llmjudge_metrics]

            # Combine results
            result_data = {
                "hallucination_metrics_yAxis": hallucination_yAxis,
                "hallucination_metrics_xaxis": hallucination_result,
                "llmjudge_metrics_yAxis": llmjudge_yAxis,
                "llmjudge_metrics_xaxis": llmjudge_result
            }

            return result_data, 200

        except Exception as e:
            print(f"Error fetching RAI batch metrics data: {e}")
            return {"message": "An error occurred while fetching data", "error": str(e)}, 500

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db_connection' in locals():
                db_connection.close()


# Add resource to API
api.add_resource(RaiBatchMetricsResource, '/')