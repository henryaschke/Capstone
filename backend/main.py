from flask import Flask, jsonify
from google.cloud import bigquery
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Initialize the BigQuery client.
# It will automatically use the Application Default Credentials.
client = bigquery.Client(project="capstone-henry")

def read_data():
    # Query selects the Time_Frame, Low, and High columns.
    query = """
        SELECT Time_Frame, Low, High 
        FROM `capstone-henry.capstone_db.Intraday_Germany_15mins`
        ORDER BY Time_Frame
    """
    query_job = client.query(query)
    results = query_job.result()
    return results

@app.route('/read_data', methods=['GET'])
def read_data_route():
    data = read_data()
    # Build a JSON-friendly list of dictionaries.
    result = [
        {"Time_frame": row.Time_Frame, "Low": row.Low, "High": row.High}
        for row in data
    ]
    return jsonify(result)

@app.route('/graph', methods=['GET'])
def graph_route():
    data = read_data()
    time_frames = []
    lows = []
    highs = []
    
    # Extract data from query results.
    for row in data:
        time_frames.append(row.Time_Frame)
        lows.append(row.Low)
        highs.append(row.High)
    
    # Render the graph template, passing the lists to it.
    return render_template('Graph.html', time_frames=time_frames, lows=lows, highs=highs)



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
