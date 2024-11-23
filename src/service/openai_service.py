import os
import sys

import openai


def call_openai_api(prompt):
    """Send the combined prompt to OpenAI API and return the response."""
    # Set the API key
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        # Return the assistant's response
        return response["choices"][0]["message"]["content"]
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {str(e)}")
        sys.exit(1)
