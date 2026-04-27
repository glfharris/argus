import base64
import json
import os
from io import BytesIO

import requests
from openai import OpenAI
from PIL import Image


def encode_image_to_base64(image_path):
    """
    Convert an image file to base64 string.
    Works with both local files and URLs.
    """
    try:
        if image_path.startswith(("http://", "https://")):
            response = requests.get(image_path)
            image = Image.open(BytesIO(response.content))
        else:
            image = Image.open(image_path)

        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Save to BytesIO object
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise Exception(f"Error encoding image: {str(e)}")


def analyze_product_packaging(image_path, api_key):
    """
    Analyze product packaging image using OpenAI's API and return structured data.

    Args:
        image_path (str): Path to image file or URL
        api_key (str): OpenAI API key

    Returns:
        dict: Extracted product information in JSON format
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)

        # Encode image
        base64_image = encode_image_to_base64(image_path)

        # Prepare the message for GPT-4 Vision
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please analyze this medication packaging and
                         extract the following information in JSON format:
                        - Drug name
                        - Concentration
                        - Ampoule size
                        - Total drug content
                        - Route of administration
                        Please report total drug content as the amount only, not the volume.
                        """,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ]
        res_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "drug_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "description": "Name of drug from packaging",
                            "type": "string",
                        },
                        "concentration": {
                            "description": "Concentration of drug in ampoule",
                            "type": "string",
                        },
                        "ampoule_size": {
                            "description": "Size of drug ampoule",
                            "type": "string",
                        },
                        "total_drug": {
                            "description": "Total mass of drug per ampoule",
                            "type": "string",
                        },
                        "additionalProperties": False,
                    },
                },
            },
        }

        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format=res_format,
        )

        # Parse the response to ensure it's valid JSON
        try:
            product_info = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # If the response isn't valid JSON, try to extract JSON from the text
            content = response.choices[0].message.content
            # Find the JSON portion (assuming it's wrapped in ```)
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > 0:
                product_info = json.loads(content[json_start:json_end])
            else:
                raise Exception("Could not parse JSON from response")

        return product_info

    except Exception as e:
        return {"error": str(e)}


def main():
    # Load API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")

    # Example usage
    image_path = "test.jpg"  # Can be local file path or URL
    result = analyze_product_packaging(image_path, api_key)

    # Pretty print the results
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
