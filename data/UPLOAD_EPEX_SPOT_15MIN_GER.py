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

    # 1) Get existing Time_Frame + Date from BigQuery and standardize
    # -------------------------------------------------------------------
    query = f"SELECT Time_Frame, Date FROM `{final_table_id}`"
    existing_df = client.query(query).to_dataframe()

    # Convert to consistent types
    # a) Make Time_Frame lowercase & strip spaces
    existing_df["Time_Frame"] = existing_df["Time_Frame"].astype(str).str.strip().str.lower()

    # b) Convert Date column to a Python date (not datetime)
    existing_df["Date"] = pd.to_datetime(existing_df["Date"], errors="coerce").dt.date

    # Create a set of (Time_Frame, Date) for fast membership testing
    existing_pairs = set(zip(existing_df["Time_Frame"], existing_df["Date"]))

    # Optional debug: print first few existing keys
    print(f"Found {len(existing_pairs)} existing rows in {final_table_id}.")
    few_existing_keys = list(existing_pairs)[:5]
    print("First few existing (Time_Frame, Date) keys from BigQuery:", few_existing_keys, "\n")

    # Folder where your CSVs live
    data_dir = r"C:\Users\henry\OneDrive\Desktop\Capstone\Capstone\data"

    # 2) Configure how we load data
    # -------------------------------------------------------------------
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.CSV,  # We'll load from a DataFrame => CSV in memory
        autodetect=True,
    )

    # 3) Process each CSV in the folder
    # -------------------------------------------------------------------
    for filename in os.listdir(data_dir):
        if not filename.lower().endswith(".csv"):
            continue  # skip non-CSV files

        csv_path = os.path.join(data_dir, filename)
        print(f"Reading CSV: {csv_path}")

        # (a) Read the CSV with Pandas
        df = pd.read_csv(csv_path, header=0, sep=",")

        # (b) Standardize Time_Frame: str, strip, lower
        if "Time_Frame" in df.columns:
            df["Time_Frame"] = df["Time_Frame"].astype(str).str.strip().str.lower()

        # (c) Convert Date to actual Python date
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

        # (d) Add any missing columns as None
        for col in master_columns:
            if col not in df.columns:
                df[col] = None

        # (e) Drop columns that are not in master_columns
        df = df[[c for c in df.columns if c in master_columns]]

        # (f) Reorder columns to match the official order
        df = df[master_columns]

        # Optional debug: Show first few (Time_Frame, Date) from CSV
        df["unique_key"] = list(zip(df["Time_Frame"], df["Date"]))
        print("First few new CSV keys:", df["unique_key"].head(5).tolist())

        # (g) Filter out rows that already exist in BigQuery (Time_Frame+Date)
        before_count = len(df)
        df = df[~df["unique_key"].isin(existing_pairs)]
        after_count = len(df)
        df = df.drop(columns=["unique_key"])  # remove the helper column

        if after_count == 0:
            print(f"All {before_count} rows in {filename} already exist in BigQuery. Skipping.\n")
            continue

        # (h) Actually load the new rows to BigQuery
        print(f"Uploading {after_count} new rows to {final_table_id} ...")
        load_job = client.load_table_from_dataframe(df, final_table_id, job_config=job_config)
        load_job.result()  # Wait for upload to finish
        print(f"Finished uploading {filename}.\n")

        # (i) Update the local set of existing_pairs
        new_pairs = set(zip(df["Time_Frame"], df["Date"]))
        existing_pairs.update(new_pairs)

    print("All CSVs processed. Done!")


if __name__ == "__main__":
    main()
