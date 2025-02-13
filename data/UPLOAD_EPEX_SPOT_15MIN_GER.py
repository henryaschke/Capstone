import os
import pandas as pd
from google.cloud import bigquery

def main():
    # Adjust to your specific project and dataset
    project_id = "capstone-henry"
    dataset_id = "capstone_db"
    table_name = "Intraday_Germany_15mins"

    final_table_id = f"{project_id}.{dataset_id}.{table_name}"

    # The "master" columns that match your BigQuery table schema
    # (You said you want up to these 12 possible columns.)
    master_columns = [
        "Time_Frame",
        "Low",
        "High",
        "Last",
        "Weight_Avg",
        "ID_Full",
        "ID1",
        "ID3",
        "Buy_Volume",
        "Sell_Volume",
        "Volume",
        "Date",
    ]

    # Initialize the BigQuery client
    client = bigquery.Client(project=project_id)

    # Folder where your CSVs live
    data_dir = r"C:\Users\henry\OneDrive\Desktop\Capstone\Capstone\data"

    # Load config: set how we load data into BigQuery
    # Here we just do append, not merges. If you need merges, see the MERGE example from before.
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.CSV,  # We'll load from a DataFrame => CSV in memory
        autodetect=True,  # or specify a schema if you prefer
        skip_leading_rows=0,
    )

    # Process each CSV in the folder
    for filename in os.listdir(data_dir):
        if not filename.lower().endswith(".csv"):
            continue  # skip non-CSV files

        csv_path = os.path.join(data_dir, filename)
        print(f"Reading CSV: {csv_path}")

        # 1) Read the CSV with Pandas (assuming comma-delimited). 
        #    If semicolon-delimited, do sep=";"
        df = pd.read_csv(csv_path, header=0, sep=",")

        # 2) For any column in master_columns that's missing, fill it with None
        for col in master_columns:
            if col not in df.columns:
                df[col] = None

        # 3) Drop columns that are not in master_columns
        #    (in case the CSV has extra columns we don't want)
        df = df[[c for c in df.columns if c in master_columns]]

        # 4) Reorder columns to match the official order
        df = df[master_columns]

        # 5) Append data to BigQuery
        print(f"Uploading {len(df)} rows to {final_table_id} ...")
        load_job = client.load_table_from_dataframe(df, final_table_id, job_config=job_config)
        load_job.result()  # Wait for upload to finish
        print(f"Finished uploading {filename}.\n")

    print("All CSVs processed. Done!")

if __name__ == "__main__":
    main()
