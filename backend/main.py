from flask import Flask, jsonify, render_template
from google.cloud import bigquery

app = Flask(__name__)

# Initialize the BigQuery client.
client = bigquery.Client(project="capstone-henry")

@app.route('/')
def home():
    # You can redirect to /graph, or just display a link, etc.
    return "Go to /graph to see the dashboard."

@app.route('/days', methods=['GET'])
def get_days():
    """
    Returns a list of all distinct dates in ascending order.
    Example: ["2025-02-10", "2025-02-11", ...]
    """
    query = """
        SELECT DISTINCT Date
        FROM `capstone-henry.capstone_db.Intraday_Germany_15mins`
        ORDER BY Date ASC
    """
    query_job = client.query(query)
    results = query_job.result()
    days = [str(row.Date) for row in results]
    return jsonify(days)

@app.route('/data_by_day/<date_str>', methods=['GET'])
def data_by_day(date_str):
    """
    Returns all rows for the given day in chronological order.
    Each row has Time_Frame, Low, High, Weight_Avg.
    """
    # IMPORTANT: Use parameterization or carefully escape user input
    # For simplicity, we'll just safely format the string, 
    # but watch out for injection if you handle input differently.
    query = f"""
        SELECT Time_Frame, Low, High, Weight_Avg
        FROM `capstone-henry.capstone_db.Intraday_Germany_15mins`
        WHERE Date = '{date_str}'
        ORDER BY Time_Frame
    """
    query_job = client.query(query)
    results = query_job.result()

    data = []
    for row in results:
        data.append({
            "Time_Frame": row.Time_Frame,
            "Low": row.Low,
            "High": row.High,
            "Weight_Avg": row.Weight_Avg
        })
    return jsonify(data)

@app.route('/graph', methods=['GET'])
def graph_route():
    # Renders our advanced Graph.html
    return render_template('Graph.html')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
