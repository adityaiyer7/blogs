import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

groq_api_key = os.getenv('GROQ_API_KEY')
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key)

def get_response(user_input):
    prompt = f"""
            You are a coding assistant. The user will describe a Python function they want to implement.

            YOUR TASK:
            - Write Python code that implements the requested function.
            - Include only code in your answer. No explanations or extra text.
            - Make sure the code is syntactically correct.

            USER REQUEST:
            {user_input}
"""
    message = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=message
    )
    answer = response.choices[0].message.content.strip()
    return answer

def evaluator(user_input, response_text):
    prompt = f"""
            You are a code reviewer.

            Your job is to check whether the following Python code correctly implements the user's request.

            USER REQUEST:
            {user_input}

            PYTHON CODE:
            {response_text}

            EVALUATION CRITERIA:
            - Does the code fully solve what the user asked?
            - Is the code syntactically correct?
            - Does the code follow good Python practices?
            - Are there obvious errors or edge cases missing?

            IF THE CODE IS CORRECT AND COMPLETE:
            - Reply with exactly the single word:
            proceed

            IF THE CODE HAS ISSUES:
            - Provide clear, specific feedback on what needs to be fixed.
            - Do not generate new code yourself.

            Reply with either:
            - The single word "proceed"
            - OR feedback describing what is wrong.
"""
    message = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=message
    )
    answer = response.choices[0].message.content.strip()
    return answer


def main():
    user_input = "Write python code to get the n_th prime number"
    
    response = get_response(user_input)
    answer = evaluator(user_input, response)

    while answer.lower() != "proceed":
        print("Evaluator feedback:", answer)
        user_input += "\n\nEvaluator feedback: " + answer
        response = get_response(user_input)
        answer = evaluator(user_input, response)

    print("Final accepted output:\n", response)

if __name__ == "__main__":
    main()
