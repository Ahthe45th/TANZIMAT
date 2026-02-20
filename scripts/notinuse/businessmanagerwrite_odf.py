import os
import subprocess
import json 
import datetime
import math 
from dotenv import load_dotenv
import logging
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "businessmanagerwrite_odf.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

oscategoryquestion = [
    {"question": "Business type", "options": ["PENZIHALISI", "OKAGWALAOKUTUUFU", "UH"], "param": "type"},
]

def insert_multiple_rows(df, data_list):
    """
    Inserts multiple rows of data into a pandas DataFrame.

    :param df: pandas DataFrame object
    :param data_list: List of dictionaries containing data to insert
    """
    print(f"Shape of the DataFrame before insertion: {df.shape}")
    new_df = pd.DataFrame(data_list)
    print(f"Number of new rows to insert: {len(new_df)}")
    updated_df = pd.concat([df, new_df], ignore_index=True)
    print(f"Shape of the DataFrame after insertion: {updated_df.shape}")
    return updated_df

def rofioptionsget(questions: list, prompt=""):
    """
    Get the options for the rofi prompt.
    """
    answers = {}
    for question in questions:
        options = question["options"]
        questionoptions = '\n'.join(options)+'\nquit'
        result = subprocess.getoutput(f'''echo "{questionoptions}" | DISPLAY=:0.0 rofi -dmenu -p 
'{prompt}{question["question"]}
' ''')
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
    result = subprocess.getoutput(f'echo "{theinput.replace("'",'')}" | /home/mehmet/.local/bin/fabric -m nousresearch/hermes-4-70b --pattern incomelastweek').strip()
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
    # --- ODS File Configuration ---
    remote_ods_path = "/Documents/BUSINESS_MANAGER.ods"
    local_ods_path = os.path.join(script_dir, "BUSINESS_MANAGER.ods")

    # --- Download ODS file from Nextcloud ---
    print("Downloading ODS file from Nextcloud...")
    download_script = os.path.join(script_dir, "get_ods_from_nextcloud.sh")
    subprocess.run([download_script, remote_ods_path, local_ods_path])
    print("Download complete.")

    # --- Read ODS file ---
    print("Reading ODS file into pandas DataFrame...")
    try:
        df = pd.read_excel(local_ods_path, engine="odf")
        print("ODS file read successfully. Here's the head of the DataFrame:")
        print(df.head())
    except FileNotFoundError:
        print(f"Error: {local_ods_path} not found. Make sure the download was successful.")
        return

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
    #result = []

    print(result)
    reformatted = []

    for item in result:
        newitem = {}
        print(item)
        if "DATE" not in item:
            item["DATE"] = inputhandler(f'{item}\nWhat was the date for this dd/mm/yy: ', multiline=True).strip() 
        dateject = datetime.datetime.strptime(item["DATE"], "%d/%m/%y") # 2 digit yr
        item["DAY"] = dateject.strftime("%A")
        item['MONTH'] = dateject.strftime("%m/" ).lstrip('0')+f"{dateject.year-2000}"
        item['QUARTER'] = f"Q{math.ceil(dateject.month/3.)}{dateject.year}"
        if "BUSINESS" not in item:
            item['BUSINESS'] = promptforquestion(oscategoryquestion, ["type"], prompt=f"{item['PERSON']} {item['AMOUNT']}:")["type"][0]

        # The original script used column letters, here we use column names
        # Make sure your ODS file has these column names in the first row
        for col_name in columns.keys():
            newitem[col_name] = item.get(col_name)

        reformatted.append(newitem)

    print(reformatted)

    # --- Insert data into DataFrame ---
    updated_df = insert_multiple_rows(df, reformatted)

    # --- Write updated DataFrame to ODS file ---
    print("Writing updated DataFrame to ODS file...")
    updated_df.to_excel(local_ods_path, index=False, engine="odf")
    print(f"Successfully saved updated data to {local_ods_path}")

    sendnotification("Data inserted successfully into ODS file.")

    # --- (Optional) Upload updated ODS file to Nextcloud ---
    # To enable this, you need to have the nextcloudcmd client installed and configured.
    # You can then uncomment the following lines.
    # print("Uploading updated file to Nextcloud...")
    # upload_command = ["nextcloudcmd", "-u", "<your_username>", "-p", "<your_password>", local_ods_path, f"nextcloud://{remote_ods_path}"]
    # print(f"Executing: {' '.join(upload_command)}")
    # subprocess.run(upload_command)
    # print("Upload complete.")


if __name__ == '__main__':
    main()
