
import requests
import argparse
from datetime import datetime

def get_prayer_times(date, city, country):
    try:
        url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2&date={date}"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        timings = data['data']['timings']

        print(f"Prayer Times for {date} in {city}, {country}:")
        for name, time in timings.items():
            print(f"{name}: {time}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching prayer times: {e}")
    except (KeyError, TypeError):
        print("Error: Could not parse prayer times from the API response.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get prayer times for a specific date.")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="Date in YYYY-MM-DD format (defaults to today).")
    parser.add_argument("--city", required=True, help="City name.")
    parser.add_argument("--country", required=True, help="Country name.")

    args = parser.parse_args()

    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        exit(1)

    get_prayer_times(args.date, args.city, args.country)
