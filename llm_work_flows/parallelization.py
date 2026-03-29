import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()


groq_api_key = os.getenv('GROQ_API_KEY')

def extract_info(input_message):
    client = OpenAI(base_url ="https://api.groq.com/openai/v1", api_key=groq_api_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=input_message
    )
    answer = response.choices[0].message.content
    return answer

def aggregator(responses):
    prompt = """You are an expert JSON response aggregator. You will be given a list of JSON responses from multiple AI models that have attempted to extract information from an invoice. Your task is to analyze these responses and determine the best one.

The expected information is:
- vendor_name (string)
- total_amount (float)
- number_of_purchases (integer)

Here are the responses from the models:
"""
    for i, r in enumerate(responses):
        prompt += f"Response {i+1}:\\n{r}\\n\\n"
    
    prompt += "Please analyze the responses and return only the best, most accurate, and complete JSON object. Do not add any commentary or explanation. If none are perfect, choose the one that is most correct."
    
    client = OpenAI(base_url ="https://api.groq.com/openai/v1", api_key=groq_api_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    
    best_response = response.choices[0].message.content
    return best_response


def main():
    user_input = """
From the following invoice, please extract the vendor name, the total amount, and the number of purchases.
Provide the output in a clean JSON format with the following keys: "vendor_name", "total_amount", and "number_of_purchases".

Invoice:
Date: 2024-01-15
Invoice Number: INV-001
To:
John Doe
123 Main St
Anytown, USA 12345

From:
Vendor Inc.
456 Oak Ave
Somecity, USA 67890

Description | Quantity | Unit Price | Total
--- | --- | --- | ---
Product A | 2 | $50.00 | $100.00
Product B | 1 | $75.00 | $75.00
Service C | 3 | $25.00 | $75.00
Subtotal: $250.00
Tax (10%): $25.00
Total Amount: $275.00

Thank you for your business!
Number of items purchased: 3
"""
    responses = []
    for _ in range(3):
        answer = extract_info([{"role": "user", "content": user_input}])
        responses.append(answer)
    
    best_response = aggregator(responses)
    print(best_response)
    return best_response

if __name__ == '__main__':
    main()