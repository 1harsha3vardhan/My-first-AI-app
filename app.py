"""
My First AI App
----------------
A simple script that sends a message to an AI model and prints the response.

Currently wired up for Google Gemini (free tier).
When you're ready to upgrade to Claude, see the commented-out section
near the bottom — swapping providers only touches a few lines.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file (this is where your API key lives)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "No GEMINI_API_KEY found. Did you create a .env file with "
        "GEMINI_API_KEY=your-key-here ?"
    )


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return its text response."""
    from google import genai

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    return response.text


def main():
    print("Simple AI Chat (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        reply = ask_gemini(user_input)
        print(f"\nAI: {reply}\n")


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------
# UPGRADING TO CLAUDE LATER
# -----------------------------------------------------------------------
# When you're ready, this is roughly all that changes:
#
# 1. Add ANTHROPIC_API_KEY=your-key-here to your .env file
# 2. pip install anthropic
# 3. Replace the ask_gemini function with something like:
#
# def ask_claude(prompt: str) -> str:
#     import anthropic
#     client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
#     message = client.messages.create(
#         model="claude-sonnet-5",
#         max_tokens=1000,
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return message.content[0].text
#
# 4. Change the call in main() from ask_gemini(...) to ask_claude(...)
#
# Everything else -- git, GitHub, .env, .gitignore -- stays exactly the same.
