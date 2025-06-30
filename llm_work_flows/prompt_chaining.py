import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

groq_api_key = os.getenv('GROQ_API_KEY')
client = OpenAI(base_url ="https://api.groq.com/openai/v1", api_key=groq_api_key)

def summarize_user_experience(resume):
    prompt = f"""You are a helpful agent. You are given a resume and you're task is to summarize the experience.
    Be sure to include their impact, skills and responsibilities
    ## Resume:
    {resume}
    """
    message = [{'role': "user", "content": prompt}]
    output = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=message)
    summary = output.choices[0].message.content
    return summary


def generate_questions(user_experience, role):
    prompt = f"""You are a helpful agent. Based on the user experience, generate 5 questions that are relevant to the role of {role}
    User Experience:
    {user_experience}
    """
    message = [{'role': "user", "content": prompt}]
    output = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=message)
    questions = output.choices[0].message.content
    return questions

def generate_answers(questions):
    prompt = f"""Please answer these questions to the best of your abilities.
    Questions:
    {questions}
    """
    message = [{'role': "user", "content": prompt}]
    output = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=message)
    answers = output.choices[0].message.content
    return answers

def evaluate_answers(questions, user_answers):
    prompt = f"""You are a helpful agent.
    Evaluate the user's answers based on the following questions:
    Questions:
    {questions}
    User Answers:
    {user_answers}
    Provide feedback on the accuracy, relevance, and completeness of the answers.
    """
    message = [{'role': "user", "content": prompt}]
    output = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=message)
    feedback = output.choices[0].message.content
    return feedback

def get_verdict(evaulation):
    prompt = f"""Based on the evaluation, give a verdict of hire or no hire.
    Evaluation = {evaulation}
    """
    message = [{'role': "user", "content": prompt}]
    output = client.chat.completions.create(model="meta-llama/llama-4-scout-17b-16e-instruct", messages=message)
    verdict = output.choices[0].message.content
    return verdict

def main():
    resume = """
    Name: John Doe
    Contact Information: johndoe@example.com, (123) 456-7890

    Work Experience:
    - Software Engineer at TechCorp (2018 - Present)
    - Developed and maintained web applications using Python and JavaScript.
    - Led a team of 5 developers to implement a new feature that increased user engagement by 20%.
    - Collaborated with cross-functional teams to design and optimize system architecture.

    - Junior Developer at WebSolutions (2016 - 2018)
    - Assisted in the development of e-commerce platforms using PHP and MySQL.
    - Improved website performance by optimizing database queries and implementing caching strategies.

    Education:
    - Bachelor of Science in Computer Science, University of Technology (2012 - 2016)

    Skills:
    - Programming Languages: Python, JavaScript, PHP
    - Frameworks: Django, React, Node.js
    - Tools: Git, Docker, Jenkins

    Achievements:
    - Awarded 'Employee of the Year' at TechCorp in 2020.
    - Published a research paper on machine learning algorithms in a peer-reviewed journal.
    """
    role = "software engineer"
    user_experience_summary = summarize_user_experience(resume)
    questions = generate_questions(user_experience_summary, role)
    user_answers = generate_answers(questions)
    evaluatation = evaluate_answers(questions, user_answers)
    verdict = get_verdict(evaluatation)
    return verdict

    
print(main())