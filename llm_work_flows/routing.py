import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    base_url ="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

def router(user_input: str) -> str:
    prompt = (
    f"You are a classification assistant specialized in distinguishing Math questions from Coding questions.\n"
    f"Given the user input below, decide which category it belongs to:\n\n"
    f"    \"{user_input}\"\n\n"
    f"Respond with exactly one of:\n"
    f"  • Math\n"
    f"  • Coding\n"
    f"  • I don't know\n\n"
    f"Examples:\n"
    f"  • \"What is the derivative of sin(x)?\"        → Math\n"
    f"  • \"How do I reverse a linked list in Python?\" → Coding\n"
    )
    message = [{"role": "user", "content": prompt}]
    out = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=message,
    )
    label = out.choices[0].message.content.strip().lower()
    
    # 2) Dispatch
    if label.startswith("math"):
        return get_math_answer(user_input)
    elif label.startswith("coding"):
        return get_coding_answer(user_input)
    else:
        return "Sorry, I couldn’t classify that input."

def get_math_answer(query: str) -> str:
    messages = [
        {"role": "system", "content": "You are a math assistant."},
        {"role": "user",   "content": query},
    ]
    out = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
    )
    return out.choices[0].message.content

def get_coding_answer(query: str) -> str:
    messages = [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user",   "content": query},
    ]
    out = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
    )
    return out.choices[0].message.content

# Example
print(router("What is the derivative of sin(x)?"))
