from google.auth import default
from googleapiclient.discovery import build

def main():
    credentials, _ = default(scopes=[
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/cloud-billing.readonly"
    ])

    billing = build("cloudbilling", "v1", credentials=credentials)

    print("🔍 Fetching billing accounts...")
    accounts = billing.billingAccounts().list().execute()
    if not accounts.get("billingAccounts"):
        print("❌ No billing accounts found or access denied.")
        return

    for acct in accounts["billingAccounts"]:
        print(f"\n✅ Billing Account: {acct['name']}")
        print(f"  Display Name: {acct.get('displayName')}")
        print(f"  Open: {acct.get('open')}")
    
    # This next part would typically call BigQuery to get usage data
    print("\n�� To get actual usage (charges and credits), you'll need to enable the Cloud Billing export to BigQuery.")
    print("Visit: https://console.cloud.google.com/billing → 'Billing export' → enable BigQuery export.")
    print("Then you can query cost and credits via SQL.")

if __name__ == "__main__":
    main()
