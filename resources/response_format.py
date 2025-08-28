import json
 
def convert_to_valid_json_string(input_string):
    try:
        # Parse the input string to a Python dictionary
        data = json.loads(input_string)
        # Convert the dictionary back to a valid JSON string with proper formatting
        valid_json_string = json.dumps(data, ensure_ascii=False, indent=2)
        return valid_json_string
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
 
def transform_data(valid_json_string):
    if not valid_json_string:
        print("Invalid JSON string provided.")
        return None
 
    try:
        # Load the input JSON string into a Python dictionary
        data = json.loads(valid_json_string)
 
        # Safely extract nested information
        error_message = (
            data.get("external_model_message", {})
            .get("error", {})
            .get("message", "No message available")
        )
        content_filter_result = (
            data.get("external_model_message", {})
            .get("error", {})
            .get("innererror", {})
            .get("content_filter_result", {})
        )
 
        # Determine categories based on the content filter results
        categories = []
        for category in ["violence", "sexual", "self_harm", "hate", "jailbreak"]:
            if content_filter_result.get(category, {}).get("filtered", False):
                categories.append(category)
 
        # Construct the transformed structure
        transformed_data = {
            "predictions": [
                {
                    "response": error_message,
                    "error": "Unsafe content detected in input",
                    "input_token_count": 0,
                    "output_token_count": 0,
                    "latency": 0,
                    "input_safety": False,
                    "categories": ",".join(categories),  # Join categories as a comma-separated string
                    "output_safety": None,
                    "output_categories": None,
                }
            ]
        }
       
 
        # Convert the transformed dictionary back to a JSON string and return it
        return json.dumps(transformed_data, indent=2)
    except Exception as e:
        print(f"Error during transformation: {e}")
        return None