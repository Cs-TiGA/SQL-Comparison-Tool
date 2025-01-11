from flask import Flask, request, jsonify
import psycopg2
import google.generativeai as gemini
import openai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration for Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini.configure(api_key=GEMINI_API_KEY)
gemini_model = gemini.GenerativeModel("gemini-1.5-flash")

# Configuration for OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
main_query = ""  # Define globally
main_query_uploaded = False  # Track if the main query has been uploaded


@app.route('/upload_main_query', methods=['POST'])
def upload_main_query():
    global main_query, main_query_uploaded
    if main_query_uploaded:
        return jsonify({"error": "Main query has already been uploaded and cannot be changed."}), 400

    main_query = request.json.get('main_query', '').strip()
    if not main_query:
        return jsonify({"error": "Please enter the main query before uploading."}), 400

    main_query_uploaded = True
    return jsonify({"message": "Main query has been uploaded."})


@app.route('/execute_solution_query', methods=['POST'])
def execute_solution_query():
    global main_query
    if not main_query_uploaded:
        return jsonify({"error": "Main query has not been uploaded yet."}), 400

    solution_query = request.json.get('solution_query', '').strip()
    if not solution_query:
        return jsonify({"error": "Please enter the solution query first."}), 400

    main_output, solution_output = execute_queries(main_query, solution_query)
    comparison = compare_queries(main_query, solution_query)
    feedback = provide_feedback(main_query, solution_query)

    return jsonify({
        "main_output": main_output,
        "solution_output": solution_output,
        "comparison": comparison,
        "feedback": feedback
    })


def execute_queries(query1, query2):
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="Project",
            user="postgres",
            password="22022022"
        )
        cursor = connection.cursor()

        # Execute Main Query
        cursor.execute(query1)
        results_query1 = cursor.fetchall()

        # Execute Solution Query
        cursor.execute(query2)
        results_query2 = cursor.fetchall()

        return results_query1, results_query2

    except Exception as error:
        return str(error), None
    finally:
        if connection:
            cursor.close()
            connection.close()


def compare_queries(query1, query2):
    prompt = f"""
    Compare the following SQL queries:

    Main Query (Query 1):
    {query1}

    Solution Query (Query 2):
    {query2}

    Provide a detailed comparison based on:
    1. Syntax and structural differences.
    2. Expected result set differences.
    3. Performance considerations and optimizations.
    """
    return openai_generate(prompt, role="You are an SQL analysis expert.")


def provide_feedback(query1, query2):
    prompt = f"""
    Provide feedback on how the solution query can be improved to match the main query.

    Main Query (Query 1):
    {query1}

    Solution Query (Query 2):
    {query2}

    Provide specific actionable suggestions to:
    1. Improve performance.
    2. Match the expected result set.
    3. Fix syntax or structural issues.
    4. Optimize the query for better efficiency.
    """
    return gemini_generate(prompt)


def gemini_generate(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error with Gemini API: {e}"


def openai_generate(prompt, role):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error with OpenAI API: {e}"


if __name__ == '__main__':
    port = int(os.getenv("PORT", 9000))  # Default to 5000 if PORT is not set
    app.run(host='0.0.0.0', port=port)
