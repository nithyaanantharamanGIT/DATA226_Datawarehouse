from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

from datetime import datetime
import requests
import pandas as pd


def return_snowflake_conn():
    hook = SnowflakeHook(snowflake_conn_id='snowflake_conn')
    conn = hook.get_conn()
    return conn.cursor()


@task
def extract():
    vantage_api_key = Variable.get('vantage_api_key')
    symbol = Variable.get('symbol', default_var='GOOG')

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_DAILY&symbol={symbol}"
        f"&apikey={vantage_api_key}&outputsize=compact"
    )

    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "Time Series (Daily)" not in data:
        raise ValueError("Invalid API response: 'Time Series (Daily)' key not found.")

    return {"symbol": symbol, "data": data["Time Series (Daily)"]}


@task
def transform(extracted_data):
    symbol = extracted_data["symbol"]
    time_series = extracted_data["data"]

    df = pd.DataFrame.from_dict(time_series, orient="index").reset_index()
    df = df.rename(columns={
        "index": "date",
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume",
    })

    df["date"] = pd.to_datetime(df["date"])
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    df["volume"] = df["volume"].astype(int)

    df = df.sort_values("date", ascending=False).head(90)
    df["date"] = df["date"].dt.strftime('%Y-%m-%d')

    records = df.to_dict(orient="records")
    return {"symbol": symbol, "records": records}


@task
def load(transformed_data, target_table):
    cur = return_snowflake_conn()
    symbol = transformed_data["symbol"]
    records = transformed_data["records"]

    try:
        cur.execute("BEGIN;")
        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {target_table} (
            symbol STRING NOT NULL,
            date DATE NOT NULL,
            open FLOAT,
            high FLOAT,
            low FLOAT,
            close FLOAT,
            volume NUMBER,
            PRIMARY KEY (symbol, date)
        )
        """
        cur.execute(create_table_query)

        delete_query = f"DELETE FROM {target_table} WHERE symbol = %s"
        cur.execute(delete_query, (symbol,))

        insert_query = f"""
            INSERT INTO {target_table} (symbol, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for r in records:
            cur.execute(insert_query, (
                symbol,
                r["date"],
                float(r["open"]),
                float(r["high"]),
                float(r["low"]),
                float(r["close"]),
                int(r["volume"]),
            ))

        cur.execute("COMMIT;")
        print(f"Data inserted successfully for {symbol}!")

    except Exception as e:
        cur.execute("ROLLBACK;")
        print("Error occurred:", e)
        raise e


with DAG(
    dag_id='Alpha_Vantage_Stock',
    start_date=datetime.today(),
    catchup=False,
    tags=['ETL'],
    schedule_interval='30 2 * * *'  # runs daily at 2:30 UTC
) as dag:
    target_table = "raw.stock_data"

    extract_task = extract()
    transform_task = transform(extract_task)
    load_task = load(transform_task, target_table)

    # Explicit dependency chain
    extract_task >> transform_task >> load_task
