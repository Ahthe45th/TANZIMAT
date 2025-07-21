from google.cloud import bigquery

# Update with your project and dataset
PROJECT_ID = "pimpting"
DATASET_ID = "standardusage"

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)

# --- Query 1: Total spend by service ---
sql_spend = f"""
SELECT
  service.description AS service,
  ROUND(SUM(cost), 2) AS total_cost_usd
FROM
  `{PROJECT_ID}.{DATASET_ID}.gcp_billing_export_v1_*`
WHERE
  usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY
  service
ORDER BY
  total_cost_usd DESC
"""

# --- Query 2: Credit usage (like free trial) ---
sql_credits = f"""
SELECT
  sku.description AS sku,
  ROUND(SUM(credits.amount), 2) AS credit_used,
  credits.name AS credit_name
FROM
  `{PROJECT_ID}.{DATASET_ID}.gcp_billing_export_v1_*`
WHERE
  credits.amount IS NOT NULL
  AND usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY
  credit_name, sku
ORDER BY
  credit_used DESC
"""

def run_query(sql, label):
    print(f"\n🔍 {label}")
    query_job = client.query(sql)
    results = query_job.result()
    for row in results:
        print(dict(row))

run_query(sql_spend, "Total Spend by Service (last 30 days)")
run_query(sql_credits, "Credits Used (last 90 days)")
