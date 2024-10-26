from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import os
from groq import Groq
import plotly.express as px

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Groq client with your API key directly
client = Groq(api_key="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")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'regional_file' not in request.files:
        return redirect(request.url)
    
    main_file = request.files['file']
    regional_file = request.files['regional_file']
    
    if main_file.filename == '' or regional_file.filename == '':
        return redirect(request.url)
    
    try:
        # Create the directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        # Save main file to uploads folder
        main_file_path = os.path.join(app.config['UPLOAD_FOLDER'], main_file.filename)
        main_file.save(main_file_path)

        # Save regional file to uploads folder
        regional_file_path = os.path.join(app.config['UPLOAD_FOLDER'], regional_file.filename)
        regional_file.save(regional_file_path)

        # Load main CSV file
        df_main = pd.read_csv(main_file_path)
        df_main[df_main.columns[1:]] = df_main[df_main.columns[1:]].replace({',': ''}, regex=True)
        df_main[df_main.columns[1:]] = df_main[df_main.columns[1:]].apply(pd.to_numeric, errors='coerce')

        # Check for valid data in the main file
        if df_main[df_main.columns[1]].isna().all():
            return "No valid numeric data found in the main file for plotting."

        # Process the main CSV data with Groq API to get analysis and suggestions
        analysis_main, suggestions_main = process_with_groq(df_main)

        # Generate the primary plot based on the main CSV data (simple line plot)
        plt.figure()
        df_main.plot(x=df_main.columns[0], y=df_main.columns[1], kind='line')
        graph_path = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
        plt.savefig(graph_path)
        plt.close()

        # Load regional CSV file
        df_regional = pd.read_csv(regional_file_path)

        # Process regional data
        regional_analysis, regional_suggestions = process_with_groq(df_regional)

        # Generate a regional summary
        regional_summary = df_regional.groupby('Region').agg({'Sales': 'sum'}).reset_index()

        return render_template(
            'results.html', 
            graph_url=graph_path, 
            groq_analysis=analysis_main, 
            groq_suggestions=suggestions_main, 
            groq_regional_analysis=regional_analysis, 
            groq_regional_suggestions=regional_suggestions,
            regional_summary=regional_summary.to_html(index=False)  # Convert to HTML for rendering
        )
    
    except Exception as e:
        return f"An error occurred: {e}"

def process_with_groq(df):
    """
    Send the CSV data to Groq for analysis and get insights and recommendations.
    """
    csv_data = df.to_csv(index=False)  # Convert dataframe to CSV string

    # Using the Groq API to generate a prompt based on the CSV data
    chat_completion = client.chat.completions.create(
    messages=[{
        "role": "user",
        "content": (
            f"Provide a concise analysis of the following CSV data, summarizing key trends, strengths, and opportunities for improvement in a single, cohesive paragraph. "
            f"Make practical recommendations that enhance sales, operations, and customer satisfaction. Ensure the response is brief, straightforward, and in continuous text without bullet points, symbols, or extra line spacing:\n{csv_data}"
        ),
    }],
    model="llama3-8b-8192",
)


    # Handle the response
    response_text = chat_completion.choices[0].message.content
    parts = response_text.split("Suggestions:", 1)

    # Ensure that we always have a response for analysis and suggestions
    analysis = parts[0].strip() if len(parts) > 0 else "No analysis available."
    suggestions = parts[1].strip() if len(parts) > 1 else "No specific suggestions available."

    # Ensure line breaks in HTML
    analysis = analysis.replace("\n", "<br>")
    suggestions = suggestions.replace("\n", "<br>")

    return analysis, suggestions

if __name__ == '__main__':
    app.run(debug=True)
