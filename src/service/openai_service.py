import json
import os
import sys

import openai


class OpenAiService:
    client = None

    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY environment variable is not set.")
            sys.exit(1)
        self.client = openai.OpenAI()

    def call(self, prompt):
        """Send the combined prompt to OpenAI API and return the response."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )

            message = response.choices[0].message.content

            return json.loads(message.replace("```json", "").replace("```", ""))
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            sys.exit(1)
