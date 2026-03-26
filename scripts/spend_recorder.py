import datetime
import pyperclip
import requests
import json
import os
import subprocess
import traceback
from dotenv import load_dotenv
import logging
import pandas as pd
import shutil
import sys

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

env_path = os.path.join(SCRIPT_DIR, 'tanzimat.env')
load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "spendaggregation_nextcloud.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from bs4 import BeautifulSoup

# ----------------- CONFIG -----------------
# Nextcloud paths
REMOTE_XLSX_PATH = "/Documents/BUSINESSMANAGER.xlsx"
LOCAL_XLSX_PATH  = os.path.join(SCRIPT_DIR, "BUSINESSMANAGER.xlsx")

TARGET_SHEET = "SPEND DATA"
COL_ORDER = ["DATE", "SPEND", "DOMESTIC SPEND", "TAG", "S2", "S3", "S4", "R", "AD SPEND", "MONTH", "BIZ COSTS"]

def getnuancedspendingcategories():
    path = os.path.expanduser('~/.config/scripts/nuancedspendingcategories.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        categories = ["rent", "electricity", "transaction costs", "groceries", "bills", "other", "social media", "airtime"]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(categories, f)
        return categories
    
def getpredefinedspendingmatchers():
    path = os.path.expanduser('~/.config/scripts/nuancedspendingmatches.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        sample = ["charges", "transfer cost", "transaction cost", "airtime"]
        matches = [{"type": "BIZ COSTS", "nuancedtype": "transaction costs", "matcher": x} for x in sample]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(matches, f, indent=2)
        return matches

spendcategories = ["DOMESTIC SPEND", "AD SPEND", "BIZ COSTS"]
nuancedspendcategories = getnuancedspendingcategories()
allpredefinedmatches = getpredefinedspendingmatchers()
oscategoryquestion = [
    {"question": "Type of expenditure", "options": spendcategories, "param": "type"},
    {"question": "More nuanced category for tracking purposes", "options": nuancedspendcategories, "param": "nuancedtype"}
]

def rofioptionsget(questions: list, prompt=""):
    answers = {}
    for q in questions:
        options = q["options"] + ["quit"]
        result = gui_utils.get_rofi_menu(f"{prompt} {q['question']}", options)
        if result and result != "quit":
            answers[q["param"]] = [result]
        else:
            sys.exit(0)
    return answers

def inputget(question, multiline=False):
    if multiline:
        prompt_message = f"{question}\n\nMake sure to delete everything here before inputting your own data."
        try:
            r = subprocess.run(
                ['zenity', '--text-info', '--editable', '--title', 'Multiline Input', '--width', '400', '--height', '300'],
                input=prompt_message, capture_output=True, text=True
            )
            return r.stdout.strip()
        except Exception:
            return None
    else: 
        return gui_utils.get_rofi_input(question)

def getdaydata():
    return inputget("Enter/Paste your content:", multiline=True)

def sequentialcollection():
    data = []
    while True:
        daydata = getdaydata()
        if not daydata: break
        
        daydata = daydata.replace("*", "")
        if "Expenditure" not in daydata:
            gui_utils.notify("Error", "No 'Expenditure' header found in data.")
            continue
            
        expenditureitems = daydata.split("Expenditure")[1]
        date = gui_utils.get_rofi_input("Enter the date for the day (dd/mm/yy):")
        if not date: break
        
        otheritems = gui_utils.get_rofi_input(f"Enter any other items for {date} (amount+amount):")
        if otheritems is None: break
        
        data.append({"date": date, "expenditure": expenditureitems, "otheritems": otheritems or "0"})
    return data

def promptforquestion(questions: list, checklist: list, prompt="N:"):
    answeredproperly = False
    answers = {}
    unanswered = checklist[:]
    while not answeredproperly:
        answers = rofioptionsget(questions, prompt=prompt)
        for item in checklist:
            if item in answers and answers[item] and answers[item][0]:
                if item in unanswered:
                    unanswered.remove(item)
        if not unanswered:
            answeredproperly = True
    return answers

def getamount(expenditureitem):
    for line in expenditureitem.split("\n"):
        if 'Amount:' in line:
            try:
                theamountstr = line.split(": ")[1].strip().replace(",","")
                return sum([float(x) for x in theamountstr.split("+")])
            except: 
                amt = gui_utils.get_rofi_input(f"{expenditureitem}\nEnter the amount:")
                return float(amt) if amt else 0.0
    return 0.0

def processthespendingdata(data):
    processeddata = []
    for day in data:
        expenditureitems = [x for x in day["expenditure"].replace('*', '').split("\n\n") if "Item" in x]
        
        for item in expenditureitems:
            processdataitem = dict.fromkeys(spendcategories, 0)
            processdataitem['DATE'] = day["date"]
            dateject = datetime.datetime.strptime(day["date"], "%d/%m/%y")
            processdataitem['MONTH'] = f"{dateject.strftime('%m/').lstrip('0')}{dateject.year-2000}"
            
            amount = getamount(item)
            processdataitem["SPEND"] = amount
            
            # Auto-match logic
            spendpart = item.split('\n')[0].replace("İ", "I").replace(";", ":").split("Item: ")[1].lower().strip()
            matched = False
            for costitem in allpredefinedmatches:
                if costitem['matcher'] in spendpart:
                    processdataitem[costitem['type']] = amount
                    processdataitem['TAG'] = costitem['nuancedtype']
                    processdataitem['S2'] = spendpart
                    matched = True
                    break
            
            if not matched:
                answers = promptforquestion(oscategoryquestion, ["type", "nuancedtype"], prompt=item)
                nuanced_type = answers['nuancedtype'][0]
                spend_type = answers['type'][0]
                processdataitem[spend_type] = amount
                processdataitem['TAG'] = nuanced_type
                
                # Save new matcher
                newmatch = {"type": spend_type, "nuancedtype": nuanced_type, "matcher": spendpart}
                if newmatch not in allpredefinedmatches:
                    allpredefinedmatches.append(newmatch)
                    path = os.path.expanduser('~/.config/scripts/nuancedspendingmatches.json')
                    with open(path, 'w') as f:
                        json.dump(allpredefinedmatches, f, indent=2)

                if nuanced_type not in nuancedspendcategories:
                    nuancedspendcategories.append(nuanced_type)
                    path = os.path.expanduser('~/.config/scripts/nuancedspendingcategories.json')
                    with open(path, 'w') as f:
                        json.dump(nuancedspendcategories, f)

            processeddata.append(processdataitem)
            processeddata.append({"DATE": day["date"]})
        
        # Add other items (biz costs)
        processdataitem = dict.fromkeys(spendcategories, 0)
        processdataitem['DATE'] = day["date"]
        dateject = datetime.datetime.strptime(day["date"], "%d/%m/%y")
        processdataitem['MONTH'] = f"{dateject.strftime('%m/').lstrip('0')}{dateject.year-2000}"
        other_amt = sum([float(x) for x in day["otheritems"].split("+")])
        processdataitem["BIZ COSTS"] = other_amt
        processdataitem["SPEND"] = other_amt
        processdataitem['TAG'] = "transaction costs"
        processeddata.append(processdataitem)
        processeddata.append({"DATE": day["date"]})
        
    return processeddata

# ----------------- CLOUD I/O -----------------
def download_from_nextcloud(remote_path, local_path):
    subprocess.run(
        [
            "scp",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx",
            LOCAL_XLSX_PATH,
        ],
        check=True,
    )

def upload_to_nextcloud(local_path, remote_path):
    subprocess.run(
        [
            "scp",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            LOCAL_XLSX_PATH,
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx"
        ],
        check=True,
    )

def atomic_backup(path):
    if os.path.exists(path):
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = f"{path}.{ts}.bak"
        shutil.copy2(path, bak)
        logging.info(f"Backup created: {bak}")
        return bak

# ----------------- SHEET UPDATE -----------------
def append_rows_to_sheet(xlsx_path, sheet_name, new_rows):
    try:
        df_existing = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
    except Exception:
        df_existing = pd.DataFrame(columns=COL_ORDER)

    for c in COL_ORDER:
        if c not in df_existing.columns:
            df_existing[c] = pd.NA

    df_new = pd.DataFrame(new_rows, columns=COL_ORDER)
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    with pd.ExcelWriter(xlsx_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_updated.to_excel(w, sheet_name=sheet_name, index=False)
    return len(df_new)

def main():
    if os.path.exists(LOCAL_XLSX_PATH):
        os.remove(LOCAL_XLSX_PATH)

    try:
        download_from_nextcloud(REMOTE_XLSX_PATH, LOCAL_XLSX_PATH)
        atomic_backup(LOCAL_XLSX_PATH)

        data = sequentialcollection()
        if not data:
            gui_utils.notify("Spend Recorder", "No rows added.")
            return

        rows = processthespendingdata(data)
        added = append_rows_to_sheet(LOCAL_XLSX_PATH, TARGET_SHEET, rows)
        gui_utils.notify("Spend Recorder", f"Inserted {added} spend rows")

        upload_to_nextcloud(LOCAL_XLSX_PATH, REMOTE_XLSX_PATH)
        gui_utils.notify("Spend Recorder", "Sync complete")

    except Exception as e:
        logging.exception("Failure")
        gui_utils.notify("Spend Recorder Error", str(e))
    finally:
        if os.path.exists(LOCAL_XLSX_PATH):
            os.remove(LOCAL_XLSX_PATH)

if __name__ == '__main__':
    main()
