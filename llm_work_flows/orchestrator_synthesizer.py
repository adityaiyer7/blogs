import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()


groq_api_key = os.getenv('GROQ_API_KEY')
client = OpenAI(base_url ="https://api.groq.com/openai/v1", api_key=groq_api_key)


def orchestrator(location):
    prompt = f"""You are an expert market research analyst. Your task is to break down the broad topic of 'Market Research on EVs in {location}' into 3 distinct sub-topics. These sub-topics should be specific enough to be researched individually. Please provide the 3 sub-topics as a comma-separated list.
"""
    message = [{"role":"user", "content": prompt}]
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=message
    )
    answer = response.choices[0].message.content
    return answer


def get_model_response(input_topic):
    prompt = f"""You are an expert market research analyst. Please provide a detailed analysis of the following topic: '{input_topic}' with respect to electric vehicles. Your analysis should be comprehensive and well-researched."""
    message = [{"role":"user", "content": prompt}]
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=message
    )
    answer = response.choices[0].message.content
    return answer

def synthesizer(responses, location):
    prompt = f"""You are an expert market research analyst. You have been provided with analyses on different sub-topics of 'Market Research on EVs in {location}'. Your task is to synthesize these analyses into a single, concise, and coherent summary.

Here are the individual reports:
{"\n\n".join(responses)}

Please provide a synthesized summary of the overall market research on EVs in {location} based on these reports."""    
    client = OpenAI(base_url ="https://api.groq.com/openai/v1", api_key=groq_api_key)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": prompt}]
    )
    
    synthesized_response = response.choices[0].message.content
    print(synthesized_response)
    return synthesized_response

def main():
    location = "EU"
    sub_topics = orchestrator(location)
    responses = []
    for topic in sub_topics.split(','):
        responses.append(get_model_response(topic))
    
    return synthesizer(responses, location)

if __name__ == '__main__':
    main()