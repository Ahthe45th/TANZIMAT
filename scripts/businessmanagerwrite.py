import os
import gspread
import subprocess
import json 
import datetime
import math 
from dotenv import load_dotenv
import logging

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "businessmanagerwrite.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from oauth2client.service_account import ServiceAccountCredentials

oscategoryquestion = [
    {"question": "Business type", "options": ["PENZIHALISI", "OKAGWALAOKUTUUFU", "UH"], "param": "type"},
]

def collect_data():
    """
    Collects user input for multiple records based on predefined columns
    and stores them in a list of dictionaries.
    
    Returns:
        List of dictionaries with user input data.
    """
    columns = {
        "DATE": "A",
        "PERSON": "B",
        "AMOUNT": "C",
        "TYPE": "D",
        "DAY": "E",
        "MONTH": "F",
        "QUARTER": "G",
        "BUSINESS": "H"
    }
    
    data_list = []

    while True:
        print("\nEnter data for a new record (or type 'stop' to finish):")

        # Collect input for each field
        record = {}
        for field in columns.keys():
            value = inputhandler(f"Enter data for a new record (or type 'stop' to finish):\n{field}: ").strip()
            if value.lower() == "stop":
                print("\nData collection stopped.")
                return data_list  # Stop and return the collected data
            record[field] = value

        # Append the record to the list
        data_list.append(record)
        print("\nRecord added! Add another or type 'stop'.")

def insert_multiple_rows(sheet, data_list):
    """
    Inserts multiple rows of data into the first available empty rows in columns A-h.

    :param sheet: gspread worksheet object
    :param data_list: List of dictionaries containing data to insert
    """
    # Get all values in columns A-D
    col_range = sheet.range("A:D")
    
    # Find the first empty row in column A-D
    first_empty_row = 1  # Default to first row
    for i in range(len(col_range)):  
        if all(cell.value == '' for cell in col_range[i::4]):  # Check A-D for empty row
            first_empty_row = (i // 4) + 1
            break

    # Prepare data for batch update
    batch_data = []
    for data_dict in data_list:
        row_data = [data_dict.get(x, "") for x in data_dict]
        batch_data.append(row_data)
        first_empty_row += 1  # Move to the next row for the next dictionary

    # Update the sheet with batch data
    sheet.update(batch_data, f"A{first_empty_row - len(data_list)}:H{first_empty_row - 1}", value_input_option='USER_ENTERED')
    print(f"{len(data_list)} rows inserted starting from row {first_empty_row - len(data_list)}")

def rofioptionsget(questions: list, prompt=""):
    """
    Get the options for the rofi prompt.
    """
    answers = {}
    for question in questions:
        options = question["options"]
        questionoptions = '\n'.join(options)+'\nquit'
        result = subprocess.getoutput(f"""echo "{questionoptions}" | DISPLAY=:0.0 rofi -dmenu -p '{prompt}{question["question"]}'""")
        if result != "quit":
            answers[question["param"]] = [result]
        else: 
            quit()
    return answers

def sendnotification(text: str):
    """
    Get the options for the rofi prompt.
    """
    result = subprocess.getoutput(f"DISPLAY=:0.0 notify-send '{text}'")

def inputget(question, multiline=False):
    """
    Get the input for the zenity prompt.
    """
    if multiline:
        prompt_message = f"{question}\n\nMake sure to delete everything here before inputting your own data."
        result = subprocess.run(['zenity', '--text-info', '--editable', '--title', 'Multiline Input', '--width', '400', '--height', '300', '--filename=/dev/stdin'], input=prompt_message, capture_output=True, text=True).stdout.strip().strip()
    else: 
        result = subprocess.getoutput(f"echo '' | DISPLAY=:0.0 rofi -dmenu -p '{question}'").rstrip()
        
    return result

def inputhandler(prompt, multiline=False): 
    try:
        result = inputget(prompt, multiline=multiline)
        return result
    except: 
        result = input(prompt)
        return result

def clipboardread():
    theinput = inputhandler("Please paste the data you copied: ", multiline=True)
    print(theinput)
    result = subprocess.getoutput(f'echo "{theinput.replace("'","")}" | /home/mehmet/.local/bin/fabric --pattern incomelastweek').strip()
    result = json.loads(result)
    return result

def promptforquestion(questions: list, checklist: list, prompt="N:"):
    answeredproperly = False
    answers = {}
    unansweredchecklist = checklist
    while not answeredproperly:
        answers = rofioptionsget(questions, prompt=prompt)
        for item in unansweredchecklist:
            if len(answers[item]) == 0:
                print(f"Please answer the question for {item}")
                break
            else:
                if not answers[item][0]:
                    break
                else:
                    unansweredchecklist.remove(item)
        numofitems = len(checklist)
        for item in checklist:
            if len(answers[item]) == 0:
                numofitems -= 1
        if numofitems == len(checklist):
            answeredproperly = True
    return answers

def main():
    columns = {
        "DATE": "A",
        "PERSON": "B",
        "AMOUNT": "C",
        "TYPE": "D",
        "DAY": "E",
        "MONTH": "F",
        "QUARTER": "G",
        "BUSINESS": "H"
    }

    result = clipboardread()

    print(result)
    reformatted = []

    for item in result:
        newitem = {}
        print(item)
        if "DATE" not in item:
            item["DATE"] = inputhandler(f"{item}\nWhat was the date for this dd/mm/yy: ", multiline=True).strip() 
        dateject = datetime.datetime.strptime(item["DATE"], "%d/%m/%y") # 2 digit yr
        item["DAY"] = dateject.strftime("%A")
        item['MONTH'] = dateject.strftime("%m/").lstrip('0')+f"{dateject.year-2000}"
        item['QUARTER'] = f"Q{math.ceil(dateject.month/3.)}{dateject.year}"
        item['BUSINESS'] = promptforquestion(oscategoryquestion, ["type"], prompt=f"{item['PERSON']} {item['AMOUNT']}:")["type"][0]

        for property in columns:
            newitem[columns[property]] = item[property]
        reformatted.append(newitem)

    print(reformatted)
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(script_dir, "sheets-449816-4627e45280c5.json"), scope)
    # Authorize the clientsheet 
    client = gspread.authorize(creds)
    # Get the instance of the Spreadsheet
    sheet = client.open("BUSINESS MANAGER")
    # Get the first sheet of the Spreadsheet
    incomeandspendworksheet = sheet.get_worksheet(0)
    insert_multiple_rows(incomeandspendworksheet, reformatted)
    sendnotification("Data inserted successfully.")

if __name__ == '__main__':
    main()
