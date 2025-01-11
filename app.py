import tkinter as tk
from tkinter import messagebox, scrolledtext
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

main_query = ""  # Define globally
main_query_uploaded = False  # Track if the main query has been uploaded

def gemini_generate(prompt):
    """
    Generate content using Gemini API.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        messagebox.showerror("Gemini API Error", f"Error with Gemini API: {e}")
        return "Error with Gemini API."

def openai_generate(prompt, role):
    """
    Generate content using OpenAI API.
    """
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
        messagebox.showerror("OpenAI API Error", f"Error with OpenAI API: {e}")
        return "Error with OpenAI API."

def upload_main_query():
    global main_query, main_query_uploaded
    if main_query_uploaded:
        messagebox.showerror("Permission Denied", "Main query has already been uploaded and cannot be changed.")
        return

    main_query = main_query_display.get("1.0", tk.END).strip()
    if not main_query:
        messagebox.showerror("Error", "Please enter the main query before uploading.")
        return

    main_query_uploaded = True
    messagebox.showinfo("Upload Successful", "Main query has been uploaded.")

def toggle_main_query_visibility():
    if not main_query_uploaded:
        messagebox.showerror("Permission Denied", "You must upload the main query first.")
        return

    if hide_button.config('text')[-1] == 'Hide':
        main_query_display.delete("1.0", tk.END)
        main_query_display.insert(tk.END, "[Main query is hidden]")
        main_query_display.configure(state=tk.DISABLED)
        hide_button.config(text='Show')
    else:
        main_query_display.configure(state=tk.NORMAL)
        main_query_display.delete("1.0", tk.END)
        main_query_display.insert(tk.END, main_query)
        hide_button.config(text='Hide')

def execute_solution_query(event=None):
    global main_query
    if not main_query_uploaded:
        messagebox.showerror("Permission Denied", "Main query has not been uploaded yet.")
        return

    solution_query = solution_query_display.get("1.0", tk.END).strip()
    if not solution_query:
        messagebox.showerror("Error", "Please enter the solution query first.")
        return

    main_query_display.configure(state=tk.NORMAL)
    main_query_display.delete("1.0", tk.END)
    main_query_display.insert(tk.END, main_query)
    execute_queries(main_query, solution_query)
    compare_queries(main_query, solution_query)
    provide_feedback(main_query, solution_query)
    toggle_main_query_visibility()

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
        main_output_display.delete("1.0", tk.END)
        main_output_display.insert(tk.END, "Main Query Output:\n")
        if not results_query1:
            main_output_display.insert(tk.END, "No results returned for the main query.\n")
        else:
            for row in results_query1:
                main_output_display.insert(tk.END, f"{row}\n")

        # Execute Solution Query
        cursor.execute(query2)
        results_query2 = cursor.fetchall()
        solution_output_display.delete("1.0", tk.END)
        solution_output_display.insert(tk.END, "Solution Query Output:\n")
        if not results_query2:
            solution_output_display.insert(tk.END, "No results returned for the solution query.\n")
        else:
            for row in results_query2:
                solution_output_display.insert(tk.END, f"{row}\n")

    except Exception as error:
        messagebox.showerror("Database Error", f"Error executing queries: {error}")
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
    comparison = openai_generate(prompt, role="You are an SQL analysis expert.")

    # Display comparison
    comparison_display.delete("1.0", tk.END)
    comparison_display.insert(tk.END, "Query Comparison:\n")
    comparison_display.insert(tk.END, comparison)

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
    feedback = gemini_generate(prompt)

    # Display feedback for improvement
    feedback_display.delete("1.0", tk.END)
    feedback_display.insert(tk.END, "Feedback for Improvement:\n")
    feedback_display.insert(tk.END, feedback)

# GUI setup
root = tk.Tk()
root.title("SQL Query Comparison Tool with Dual AI")
root.geometry("900x800")

# Main Query Frame
main_frame = tk.Frame(root)
main_frame.pack(pady=5)
tk.Label(main_frame, text="Main Query").grid(row=0, column=0, padx=5)
hide_button = tk.Button(main_frame, text="Hide", command=toggle_main_query_visibility)
hide_button.grid(row=0, column=1, padx=5)
tk.Button(main_frame, text="Upload", command=upload_main_query).grid(row=0, column=2, padx=5)
main_query_display = scrolledtext.ScrolledText(main_frame, height=5, width=80)
main_query_display.grid(row=1, columnspan=3, pady=5)
main_query_display.bind("<Return>", execute_solution_query)

# Solution Query Frame
solution_frame = tk.Frame(root)
solution_frame.pack(pady=5)
tk.Label(solution_frame, text="Solution Query").grid(row=0, column=0, padx=5)
solution_query_display = scrolledtext.ScrolledText(solution_frame, height=5, width=80)
solution_query_display.grid(row=1, columnspan=2, pady=5)
solution_query_display.bind("<Return>", execute_solution_query)

# Main Output Frame
main_output_frame = tk.Frame(root)
main_output_frame.pack(pady=5)
tk.Label(main_output_frame, text="Main Query Output").pack()
main_output_display = scrolledtext.ScrolledText(main_output_frame, height=5, width=80)
main_output_display.pack()

# Solution Output Frame
solution_output_frame = tk.Frame(root)
solution_output_frame.pack(pady=5)
tk.Label(solution_output_frame, text="Solution Query Output").pack()
solution_output_display = scrolledtext.ScrolledText(solution_output_frame, height=5, width=80)
solution_output_display.pack()

# Comparison Display Frame
comparison_frame = tk.Frame(root)
comparison_frame.pack(pady=5)
tk.Label(comparison_frame, text="Query Comparison").pack()
comparison_display = scrolledtext.ScrolledText(comparison_frame, height=10, width=80)
comparison_display.pack()

# Feedback Display Frame
feedback_frame = tk.Frame(root)
feedback_frame.pack(pady=5)
tk.Label(feedback_frame, text="Feedback for Improvement").pack()
feedback_display = scrolledtext.ScrolledText(feedback_frame, height=10, width=80)
feedback_display.pack()

root.mainloop()
