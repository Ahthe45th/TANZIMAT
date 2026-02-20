
import re
import datetime
import calendar
import sys
import json

def update_passed_due_dates(bill_data: str, current_date: datetime.date) -> str:
    """
    Parses bill data, and for any bill whose due date has passed, updates the date
    to the same day of the nearest upcoming month.
    """
    updated_lines = []
    # This regex is designed for the format: NAME DD/MM/YY - KSH AMOUNT
    # It seems the webhook data sometimes lacks the '(Due: ...)' part, so we need a more flexible regex.
    # New Regex: handles optional '(Due: ...)' and varying whitespace.
    bill_pattern = re.compile(r"^(.*?)(?:\(Due: (\d{2}/\d{2}/\d{2})\))?\s+-\s+KSH\s+([\d,]+)$")

    raw_lines = bill_data.strip().replace('\n', '\n').split('\n')

    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("Total Expenses"):
            continue

        # The webhook data doesn't have the (Due: ) part, so we need to adjust the parsing
        # Let's create a simpler parser for the format: NAME DD/MM/YY - KSH AMOUNT
        parts = line.split()
        try:
            amount = parts[-1]
            currency = parts[-2]
            date_str = parts[-4] # The date is now at a different position
            item_name = " ".join(parts[:-4])

            if currency != "KSH":
                updated_lines.append(line) # Not a bill line, keep as is
                continue

            due_date = datetime.datetime.strptime(date_str, "%d/%m/%y").date()

            if due_date < current_date:
                new_year = due_date.year
                new_month = due_date.month + 1
                if new_month > 12:
                    new_month = 1
                    new_year += 1
                last_day_of_new_month = calendar.monthrange(new_year, new_month)[1]
                new_day = min(due_date.day, last_day_of_new_month)
                due_date = datetime.date(new_year, new_month, new_day)

            new_date_str = due_date.strftime("%d/%m/%y")
            # Reconstruct the line in the original format
            updated_line = f"{item_name} {new_date_str} - {currency} {amount}"
            updated_lines.append(updated_line)

        except (ValueError, IndexError):
            # If parsing fails, add the original line back
            updated_lines.append(line)

    return "\n".join(updated_lines)

if __name__ == '__main__':
    try:
        # Read the full input from stdin
        raw_input = sys.stdin.read()
        
        # Parse the input as JSON
        input_json = json.loads(raw_input)
        
        # Extract the string from the 'data' key
        bill_data_from_webhook = input_json['data']

    except (json.JSONDecodeError, KeyError):
        # If input is not valid JSON or doesn't have a 'data' key,
        # treat the input as plain text as a fallback.
        bill_data_from_webhook = raw_input

    # Set the current date for comparison
    today = datetime.date.today()

    # Process the data
    updated_bill_data = update_passed_due_dates(bill_data_from_webhook, today)

    # Print the final result to standard output
    print(updated_bill_data)
