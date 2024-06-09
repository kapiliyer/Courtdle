import os
import json
from openai import OpenAI
import oyez_api_wrapper
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date

app = Flask(__name__)
CORS(app)
client = OpenAI()
CACHE_FILE = 'cases_cache.json'
DEFAULT_CASES = [('1900-1940', '249us47'), ('1900-1940', '274us357'), ('1940-1955', '337us1'), ('1940-1955', '341us494'), ('1968', '492')]
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
    for term, docket in DEFAULT_CASES:
        cases.append(oyez_api_wrapper.court_case(term, docket))
    return cases, theme


# Function to summarize a case
def summarize_case(case):
    print('Fetching case info')
    try:
        _, *parties = case.get_basic_info()
    except:
        parties = []
    try:
        facts = case.get_case_facts()
    except:
        facts = ''
    try:
        question = case.get_legal_question()
    except:
        question = ''
    print('Got case info')

    prompt = (
        f'Parties: {parties}\n'
        f'Facts: {facts}\n'
        f'Legal Question: {question}\n'
        'Summarize the above Supreme Court case details.'
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    summary = response.choices[0].message.content.strip()
    return summary


# Function to check whether user was correct
def is_correct(case, user_choice):
    print('Fetching case info')
    try:
        case_name, *parties = case.get_basic_info()
    except:
        case_name, parties = '', []
    try:
        ruling = case.get_ruling()
        winning_party = ruling[2]
    except:
        winning_party = ''
    print('Got case info')

    prompt = (
        f'Respond "Correct" if correct answer was chosen by user, else "Incorrect"\n'
        f'Case Name: {case_name}\n'
        f'Choices: {parties}\n'
        f'Answer (if available, else go off of what you know about the case): {winning_party}\n'
        f'User choice: {user_choice}'
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    correct = response.choices[0].message.content.strip()
    return correct

# Function to summarize a case's conclusion
def summarize_case_conclusion(case):
    print('Fetching case info')
    try:
        conclusion = case.get_conclusion()
    except:
        conclusion = ''
    print('Got case info')

    prompt = (
        f'Conclusion: {conclusion}\n'
        'Summarize the above Supreme Court case conclusion details.'
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )

    conclusion_summary = response.choices[0].message.content.strip()
    return conclusion_summary


# Endpoint to fetch and summarize cases
@app.route('/cases_info', methods=['GET'])
def get_cases_info():
    print('GET')

    print('Loading cache')
    cache = load_cached_cases()
    print('Loaded cache')
    if cache and cache['date'] == str(date.today()):
        print('Got cached result')
        cases_info = cache['cases_info']
    else:
        print('No cached result')
        print('Fetching cases')
        cases_info = []
        cases, theme = fetch_cases_theme()

        for case in cases:
            print(f'Fetching case info for {case.term}.{case.docket}')
            try:
                judges = case.get_case_judges()
            except:
                judges = []
            try:
                case_name, *parties = case.get_basic_info()
            except:
                case_name, parties = '', []
            try:
                question = case.get_legal_question()
            except:
                question = ''
            print('Got case info')

            print('Fetching GPT summary')
            summary = summarize_case(case)
            print('Got GPT summary')

            cases_info.append({
                'case_id': f'{case.term}.{case.docket}',
                'theme': theme,
                'judges': judges,
                'case_name': case_name,
                'parties': parties,
                'question': question,
                'summary': summary,
            })

        print('Got case info')
        print('Saving cache')
        save_cached_cases(cases_info)
        print('Saved cache')

    return jsonify(cases_info)


# Endpoint to check user answer
@app.route('/check_answer', methods=['POST'])
def check_answer():
    print('POST')

    print('Fetching answer info')
    data = request.json
    case_id = data['case_id']
    user_choice = data['user_choice']
    term, docket = case_id.split('.')
    print('Got answer info')

    print('Fetching case info')
    case = oyez_api_wrapper.court_case(term, docket)
    try:
        correct = is_correct(case, user_choice)
    except:
        correct = 'Incorrect'
    try:
        decisions = case.get_judge_decisions()
    except:
        decisions = []
    print('Got case info')

    conclusion = summarize_case_conclusion(case)

    return jsonify({'correct': correct, 'decisions': decisions, 'conclusion': conclusion})


if __name__ == '__main__':
    app.run(debug=True)
