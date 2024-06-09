import os
import json
import random
import openai
import oyez_api_wrapper
from flask import Flask, jsonify, request
from datetime import date

app = Flask(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CACHE_FILE = 'cases_cache.json'

DEFAULT_CASES = [('1919', '437'), ('1926', '3'), ('1949', '272'), ('1950', '336'), ('1969', '492')]
DEFAULT_THEME = 'Free Speech'


# Function to load cached cases
def load_cached_cases():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            cache = json.load(file)
            return cache
    return None


# Function to save cached cases
def save_cached_cases(cases):
    cache = {
        'date': str(date.today()),
        'cases_info': cases
    }
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file)


# Function to fetch cases using Oyez API Wrapper
def fetch_cases_theme():
    # TODO: Fetch random 5 cases, associated with some random theme
    theme = DEFAULT_THEME
    cases = []
    for year, docket_number in DEFAULT_CASES:
        cases.append(oyez_api_wrapper.court_case(year, docket_number))
    return cases, theme


# Function to summarize a case using GPT
def summarize_case(case):
    openai.api_key = OPENAI_API_KEY
    case_name, *parties = case.get_basic_info()
    facts = case.get_case_facts()
    question = case.get_legal_question()
    
    prompt = (
        f'Case Name: {case_name}\n'
        f'Parties: {parties}\n'
        f'Facts: {facts}\n'
        f'Legal Question: {question}\n'
        'Summarize the above Supreme Court case details.'
    )

    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt
    )
    summary = response.choices[0].text.strip()
    return summary


# Endpoint to fetch and summarize cases
@app.route('/cases_info', methods=['GET'])
def get_cases_info():
    cache = load_cached_cases()
    if cache and cache['date'] == str(date.today()):
        cases_info = cache['cases_info']
    else:
        cases_info = []
        cases, theme = fetch_cases_theme()
        for case in cases:
            judges = case.get_case_judges()
            case_name, *parties = case.get_basic_info()
            question = case.get_legal_question()
            summary = summarize_case(case)

            cases_info.append({
                'case_id': f'{case.year}.{case.docket_number}',
                'theme': theme,
                'judges': judges,
                'case_name': case_name,
                'parties': parties,
                'question': question,
                'summary': summary,
            })
        save_cached_cases(cases_info)

    return jsonify(cases_info)


# Endpoint to check user answer
@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.json
    case_id = data['case_id']
    user_choice = data['user_choice']
    year, docket_number = case_id.split('.')

    case = oyez_api_wrapper.court_case(year, docket_number)
    ruling = case.get_ruling()
    winning_party = ruling[2]
    is_correct = (user_choice == winning_party)
    decisions = case.get_judge_decisions()
    conclusion = case.get_conclusion()

    return jsonify({'correct': is_correct, 'decisions': decisions, 'conclusion': conclusion})


if __name__ == '__main__':
    app.run(debug=True)
