from openai import OpenAI
import base64

from rich.pretty import pprint
import json

import sys

client = OpenAI()

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

image = encode_image(sys.argv[1])
i = 0
while i < 5:
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Identify the drug, concentration, volume, and total content. Please reply as a JSON object"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image}"
                        }
                    },
                ],
            }
        ],
    )
    content = response.choices[0].message.content
    if content is not None:
        drug = json.loads(response.choices[0].message.content)
        pprint(drug)
        break
    else:
        print(f"Attempt {i + 1} failed, trying again...")
        i += 1
