import requests
from bs4 import BeautifulSoup
import pandas as pd

final_date_str = "2025-02-14"

def main():
    # -------------------------------------------------------------------------
    # 1) POST request as before
    # -------------------------------------------------------------------------
    url = (
        "https://www.epexspot.com/en/market-results"
        f"?market_area=DE&auction=&trading_date=&delivery_date={final_date_str}"
        "&underlying_year=&modality=Continuous&sub_modality=&technology="
        "&data_mode=table&period=&production_period=&product=15"
        "&ajax_form=1&_wrapper_format=drupal_ajax"
    )
    
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/132.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }

    data = {
        "filters[modality]": "Continuous",
        "filters[delivery_date]": f"{final_date_str}",
        "filters[product]": "15",
        "filters[data_mode]": "table",
        "filters[market_area]": "DE",
        "triggered_element": "filters[delivery_date]",
        "first_triggered_date": "filters[delivery_date]",
        "form_id": "market_data_filters_form",
        "_triggering_element_name": "submit_js",
        "_drupal_ajax": "1",
    }

    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()
    print("Request successful!")

    # -------------------------------------------------------------------------
    # 2) Extract the HTML snippet
    # -------------------------------------------------------------------------
    json_resp = resp.json()
    html_content = None
    for cmd in json_resp:
        if cmd.get("command") == "invoke" and cmd.get("selector") == ".js-md-widget":
            html_content = cmd.get("args", [""])[0]
            break
    if not html_content:
        print("No HTML snippet found. Possibly no data for that date.")
        return

    # -------------------------------------------------------------------------
    # 3) Parse the table
    # -------------------------------------------------------------------------
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")
    if not table:
        print("No <table> found.")
        return

    tbody = table.find("tbody")
    if not tbody:
        print("No <tbody> found.")
        return

    # -------------------------------------------------------------------------
    # 4) Extract ALL rows
    # -------------------------------------------------------------------------
    rows_all = []
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        # The first cell is timeframe or lumps, then 10 numeric-ish columns
        cells = [td.get_text(strip=True).replace(",", "") for td in tds]
        rows_all.append(cells)

    if not rows_all:
        print("No rows in the table => possibly no data.")
        return

    # -------------------------------------------------------------------------
    # 5) Group the data by "hour block" (assuming 7 rows per hour as in your Excel)
    #    Skip indices 0,1,4 in each group; keep indices 2,3,5,6.
    # -------------------------------------------------------------------------
    chunk_size = 7
    keep_indices = [2, 3, 5, 6]

    rows_15 = []
    for i in range(0, len(rows_all), chunk_size):
        chunk = rows_all[i : i + chunk_size]
        if len(chunk) < 7:
            continue  # skip incomplete chunks
        hour_subset = []
        for ki in keep_indices:
            hour_subset.append(chunk[ki])
        rows_15.extend(hour_subset)

    if not rows_15:
        print("After skipping lumps, no 15-min intervals remain. Possibly no data or pattern mismatch.")
        return

    # -------------------------------------------------------------------------
    # 6) Insert static time labels at the front of each row,
    #    shifting all other columns (including "Low") to the right.
    #
    # For each hour block (4 rows per hour):
    #   new row0 => "HH:00 - HH:15"
    #   new row1 => "HH:15 - HH:30"
    #   new row2 => "HH:30 - HH:45"
    #   new row3 => "HH:45 - HH+1:00"
    #
    # Instead of deleting any existing value, we simply insert the new label at index 0.
    # -------------------------------------------------------------------------
    labeled_rows = []
    hours_found = len(rows_15) // 4  # each hour has 4 rows
    for h in range(hours_found):
        base = 4 * h
        row0 = rows_15[base + 0]
        row1 = rows_15[base + 1]
        row2 = rows_15[base + 2]
        row3 = rows_15[base + 3]

        h_str = f"{h:02d}"
        h_plus_1_str = f"{(h+1):02d}"

        # Insert the new static label at index 0; existing numeric data shifts right.
        row0.insert(0, f"{h_str}:00 - {h_str}:15")
        row1.insert(0, f"{h_str}:15 - {h_str}:30")
        row2.insert(0, f"{h_str}:30 - {h_str}:45")
        row3.insert(0, f"{h_str}:45 - {h_plus_1_str}:00")
        
        labeled_rows.extend([row0, row1, row2, row3])

    # -------------------------------------------------------------------------
    # 7) Append "Date" as the last column.
    #    The expected final columns are:
    #    [Time Frame, Low, High, Last, Weight Avg, ID Full, ID1, ID3, Buy Volume, Sell Volume, Volume, Date]
    # -------------------------------------------------------------------------
    #Time_Frame,Low,High,Last,Weight_Avg,ID_Full,ID1,ID3,Buy_Volume,Sell_Volume,Volume,Date
    columns = [
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
        "Date"
    ]

    final_data = []
    for row in labeled_rows:
        # Ensure each row has at least 11 columns (the numeric data)
        while len(row) < 11:
            row.append("")
        row = row[:11]
        row.append(final_date_str)
        final_data.append(row)

    df = pd.DataFrame(final_data, columns=columns)

    print("\nFinal DataFrame (static 15-min labels inserted, original numeric data shifted right):")
    print(df.to_string(index=False))
    
    # Automatically name the output CSV file based on the final date and append EPEX_SPOT_15MIN_GER.
    out_csv = fr"C:\Users\henry\OneDrive\Desktop\Capstone\Capstone\data\{final_date_str}_EPEX_SPOT_15MIN_GER.csv"
    df.to_csv(out_csv, index=False)

    print(f"Saved CSV: {out_csv}")

if __name__ == "__main__":
    main()
