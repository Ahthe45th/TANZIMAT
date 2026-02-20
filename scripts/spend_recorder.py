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

script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, 'tanzimat.env')

load_dotenv(env_path)

# --- LOGGING CONFIGURATION ---
LOG_DIR = os.path.join(script_dir, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "spendaggregation_nextcloud.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Starting spendaggregation_nextcloud.py script.")

from bs4 import BeautifulSoup

# ----------------- CONFIG -----------------
# Nextcloud paths
REMOTE_XLSX_PATH = "/Documents/BUSINESSMANAGER.xlsx"
LOCAL_XLSX_PATH  = os.path.join(script_dir, "BUSINESSMANAGER.xlsx")

GET_FROM_NC = os.path.join(script_dir, "get_from_nextcloud.sh")
PUT_TO_NC   = os.path.join(script_dir, "put_to_nextcloud.sh")

TARGET_SHEET = "SPEND DATA"
COL_ORDER = ["DATE", "SPEND", "DOMESTIC SPEND", "TAG", "S2", "S3", "S4", "R", "AD SPEND", "MONTH", "BIZ COSTS"]

processeddata = []

def getnuancedspendingcategories():
    if os.path.exists('/home/mehmet/.config/scripts/nuancedspendingcategories.json'):
        pth = open('/home/mehmet/.config/scripts/nuancedspendingcategories.json', 'r').read()
        return json.loads(pth)
    else:
        categories = ["rent", "electricity", "transaction costs", "groceries", "bills", "other", "social media", "airtime"]
        with open('/home/mehmet/.config/scripts/nuancedspendingcategories.json', 'w') as f:
            f.write(json.dumps(categories))
        return categories
    
def getpredefinedspendingmatchers():
    if os.path.exists('/home/mehmet/.config/scripts/nuancedspendingmatches.json'):
        pth = open('/home/mehmet/.config/scripts/nuancedspendingmatches.json', 'r').read()
        return json.loads(pth)
    else:
        sample = ["charges", "transfer cost", "transaction cost", "airtime"]
        matches = [{"type": "BIZ COSTS", "nuancedtype": "transaction costs", "matcher": x} for x in sample]
        with open('/home/mehmet/.config/scripts/nuancedspendingmatches.json', 'w') as f:
            f.write(json.dumps(matches))
        return matches

spendcategories = ["DOMESTIC SPEND", "AD SPEND", "BIZ COSTS"]
nuancedspendcategories = getnuancedspendingcategories()
allpredefinedmatches = getpredefinedspendingmatchers()
oscategoryquestion = [
    {"question": "Type of expenditure", "options": spendcategories, "param": "type"},
    {"question": "More nuanced category for tracking purposes", "options": nuancedspendcategories, "param": "nuancedtype"}
]

osdatacollectionquestion = [
    {"question": "Type of data collection", "options": ["sequential", "batch", "prayer", "balance"], "param": "type"}
]

def sendnotification(text: str):
    """
    Get the options for the rofi prompt.
    """
    result = subprocess.getoutput(f"DISPLAY=:0.0 notify-send '{text}'")


def rofioptionsget(questions: list, prompt=""):
    """
    Get the options for the rofi prompt.
    """

    answers = {}
    for question in questions:
        cmd = [
            "rofi",
            "-dmenu",
            "-p",
            f"{prompt} {question['question']}"
        ]
        options = question["options"]
        questionoptions = '\n'.join(options)+'\nquit'
        output = subprocess.run(
            cmd,
            input=questionoptions,
            text=True,
            capture_output=True,
            env={"DISPLAY": ":1"}
        )

        result = output.stdout
        if result != "quit":
            answers[question["param"]] = [result]
        else: 
            quit()
    return answers

def inputget(question, multiline=False):
    """
    Get the input for the zenity prompt.
    """
    if multiline:
        prompt_message = f"{question}\n\nMake sure to delete everything here before inputting your own data."
        result = subprocess.run(['zenity', '--text-info', '--editable', '--title', 'Multiline Input', '--width', '400', '--height', '300', '--filename=/dev/stdin'], input=prompt_message, capture_output=True, text=True).stdout.strip()
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

def getdaydata():
    contents = inputhandler("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.\nIf in batch make sure to put a * before each phone and add metadata i.e *Phone Balances 17/2/90 0+23+39", multiline=True).replace("*","")
    print("The day data")
    print(contents)
    print("-------------")
    return contents

def sequentialcollection():
    data = []
    gettingdata = True
    
    print("Enter the day data")
    while gettingdata:
        daydata = getdaydata()
        if daydata:
            print("The day data")
            print(daydata)
            print("----------------------")
            expenditureitems = daydata.split("Expenditure")[1]
            print("_____ EXPENDITURE ITEMS ______")
            print(expenditureitems)
            date = inputhandler("Enter the date for the day:")
            otheritems=inputhandler("Enter any other items for the day {date} in the format: amount+amount+amount\nInput: ")
            data.append({"date":date,"expenditure":expenditureitems,"otheritems":otheritems})
        else:
            gettingdata = False
    return data

def batchcollection():
    def get_metadata(daydata):
        firstline = daydata.split("\n")[0]
        items = [x for x in firstline.split(" ") if x]
        print(items)
        otheritems = items[-1]
        date = items[1]
        expenditureitems = daydata.split("Expenditure")[1]
        print(date)
        print(otheritems)
        return {"date":date,"expenditure":expenditureitems,"otheritems":otheritems}
    
    rawdata = [x for x in getdaydata().replace("Expenditure:", "Expenditure").split("*Phone") if x]
    print(rawdata)
    data = [get_metadata(x) for x in rawdata if 'Expenditure' in x if x]
    return data

def promptforquestion(questions: list, checklist: list, prompt="N:"):
    answeredproperly = False
    answers = {}
    unansweredchecklist = checklist
    while not answeredproperly:
        answers = rofioptionsget(questions, prompt=prompt)
        for item in unansweredchecklist:
            if len(answers[item]) == 0:
                print(f"Please answer the question for {item}")
                sendnotification(f"Please answer the question for {item}")
                break
            else:
                if not answers[item][0]:
                    break
                elif answers[item][0].strip() == '':
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

def getamount(expenditureitem):
    for line in expenditureitem.split("\n"):
        if 'Amount:' in line:
            try:
                theamountstr = line.split(": ")[1].strip().replace(",","")
                amount = sum([float(x) for x in theamountstr.split("+")])
                return amount
            except: 
                print(expenditureitem)
                print("Error in getting amount")
                amount = inputhandler(f"{expenditureitem}\nEnter the amount:")
                return amount

def processthespendingdata(data):
    def checkifspendisalreadymatched(item, processeddataitem):
        try:
            # replaces turkish I with english I
            spendpartofitem = item.split('\n')[0].replace("İ", "I").replace(";", ":").split("Item: ")[1].lower().strip()

            for costitem in allpredefinedmatches:
                if costitem['matcher'] in spendpartofitem and costitem['type'] != '' and costitem['nuancedtype'] != '':
                    processeddataitem[costitem['type']] = getamount(item)
                    processeddataitem['TAG'] = costitem['nuancedtype']
                    return processeddataitem
            return processeddataitem
        except:
            print(traceback.format_exc())
            return processeddataitem

            
    processeddata = []
    for day in data:
        print(day["date"])
        expenditureitems = day["expenditure"].replace('*', '').split("\n\n")
        expenditureitems = [x for x in expenditureitems if "Item" in x]
        
        for item in expenditureitems:
            print("The item")
            print(f"'{item}'")
            processdataitem = dict.fromkeys(spendcategories,0)
            processdataitem['DATE'] = day["date"]
            dateject = datetime.datetime.strptime(day["date"], "%d/%m/%y")
            processdataitem['MONTH'] = f"{dateject.strftime('%m/').lstrip('0')}{dateject.year-2000}"
            
            amount = getamount(item)
            processdataitem["SPEND"] = amount
            processdataitem = checkifspendisalreadymatched(item, processdataitem)
                
            if "TAG" not in processdataitem:
                answers = promptforquestion(oscategoryquestion, ["type", "nuancedtype"], prompt=item)
                nuancedanswers = answers['nuancedtype']
                processdataitem[answers['type'][0]] = amount
                processdataitem['TAG'] = nuancedanswers[0]
                print(answers)
                newmatch = {"type": answers['type'][0], "nuancedtype": nuancedanswers[0], "matcher": item.split('\n')[0].replace("İ", "I").split("Item: ")[1].lower().strip()}
                
                if newmatch not in allpredefinedmatches:
                    allpredefinedmatches.append(newmatch)
                    with open('/home/mehmet/.config/scripts/nuancedspendingmatches.json', 'w') as f:
                        f.write(json.dumps(allpredefinedmatches, indent=2))

                if nuancedanswers[0] not in nuancedspendcategories and nuancedanswers[0].strip() != "quit":
                    nuancedspendcategories.append(nuancedanswers[0])
                    with open('/home/mehmet/.config/scripts/nuancedspendingcategories.json', 'w') as f:
                        f.write(json.dumps(nuancedspendcategories))

            processeddata.append(processdataitem)
            processeddata.append({"DATE":day["date"]})
        
        processdataitem = dict.fromkeys(spendcategories, 0)
        processdataitem['DATE'] = day["date"]
        dateject = datetime.datetime.strptime(day["date"], "%d/%m/%y")
        processdataitem['MONTH'] = f"{dateject.strftime('%m/').lstrip('0')}{dateject.year-2000}"
        processdataitem["BIZ COSTS"] = sum([float(x) for x in day["otheritems"].split("+")]) + processdataitem["BIZ COSTS"]
        processdataitem["SPEND"] = processdataitem["BIZ COSTS"]
        processdataitem['TAG'] = "transaction costs"

        processeddata.append(processdataitem)
        processeddata.append({"DATE":day["date"]})
    return processeddata

def getbalance():
    balance = inputhandler("Enter the report:", multiline=True)
    relevantreport = [x for x in balance.split("Limit")[0].split("Balances")[1].split('\n') if x]

    print(relevantreport)
    total = 0
    for line in relevantreport:
        print(line)
        amountandother = ""
        if ":" in line:
            amountandother = line.split(":")[1].strip()
        else: 
            amountandother = line.split('-')[1].strip()
        print(amountandother)
        amount = amountandother.split(" ")[0].replace(",","")
        amount = float(amount)
        total += amount
    
    sendnotification(f"Total balance is {total}")
    print(f"Total balance is {total}")
    
def get_prayer_times():
    zawalurl = "https://www.urdupoint.com/islam/nairobi-sunrise-zawal-timings.html"
    url = f"https://api.aladhan.com/v1/timingsByCity/{datetime.datetime.now().strftime('%d-%m-%Y')}?city=Nairobi&country=KE&state=Nairobi&method=4&shafaq=general&tune=5%2C3%2C5%2C7%2C9%2C-1%2C0%2C8%2C-6&timezonestring=UTC&calendarMethod=UAQ"
    
    stacklist = []
    
    zawalcontent = requests.get(zawalurl).content
    soup = BeautifulSoup(zawalcontent, "html.parser")
    
    zawaldiv = soup.find("div", {"class": "zawal_box"})
    zawaltable = zawaldiv.find("table", {"class": "spec_table"})
    zawaltimings = zawaltable.find_all("td")
    
    starttiming = zawaltimings[1].getText().replace("PM", "").strip()
    endtiming = zawaltimings[3].getText().replace("PM", "").strip()
    
    document = requests.get(url).content.decode("utf-8")
    document = json.loads(document)['data']['timings']
    
    print("*Prayer times Nairobi*")
    stacklist.append("*Prayer times Nairobi*")
    print(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}")
    stacklist.append(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}")
    print(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}")
    stacklist.append(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}")
    print(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}\n")
    stacklist.append(f"Fajr: {document['Fajr']} Maghrib {document['Maghrib']}\n")

    print("*Zawal:*")
    stacklist.append("*Zawal:*")
    startishraqtime2 = datetime.datetime.strptime(starttiming, "%H:%M") - datetime.timedelta(minutes=6)
    print(f"{datetime.datetime.strftime(startishraqtime2, '%H:%M')} - {endtiming}")
    stacklist.append(f"{datetime.datetime.strftime(startishraqtime2, '%H:%M')} - {endtiming}")
    print(f"{starttiming} - {endtiming}")
    stacklist.append(f"{starttiming} - {endtiming}")
    print("\n")
    stacklist.append('\n')

    print("*Ishraq:*")
    stacklist.append("*Ishraq:*")
    startishraqtime = datetime.datetime.strptime(document['Sunrise'], "%H:%M") + datetime.timedelta(minutes=167)
    print(f"{document['Sunrise']} - {datetime.datetime.strftime(startishraqtime, '%H:%M')}")
    stacklist.append(f"{document['Sunrise']} - {datetime.datetime.strftime(startishraqtime, '%H:%M')}")

    pyperclip.copy('\n'.join(stacklist))
    os.system('notify send "Prayer times copied"')

# ----------------- CLOUD I/O -----------------
def download_from_nextcloud(remote_path, local_path):
    logging.info(f"Downloading {remote_path} -> {local_path}")
    r = subprocess.run(
        [
            "scp",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx",
            "/home/mehmet/Proyectos/TANZIMAT/scripts/BUSINESSMANAGER.xlsx",
        ],
        check=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Download failed: {remote_path}")

def upload_to_nextcloud(local_path, remote_path):
    logging.info(f"Uploading {local_path} -> {remote_path}")
    r = subprocess.run(
        [
            "scp",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            "/home/mehmet/Proyectos/TANZIMAT/scripts/BUSINESSMANAGER.xlsx",
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx"
        ],
        check=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Upload failed: {remote_path}")

def atomic_backup(path):
    if os.path.exists(path):
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = f"{path}.{ts}.bak"
        with open(path, "rb") as src, open(bak, "wb") as dst:
            dst.write(src.read())
        logging.info(f"Backup created: {bak}")
        return bak

# ----------------- SHEET UPDATE -----------------
def append_rows_to_sheet(xlsx_path, sheet_name, new_rows):
    try:
        df_existing = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
    except FileNotFoundError:
        df_existing = pd.DataFrame(columns=COL_ORDER)
    except ValueError: # Sheet does not exist
        df_existing = pd.DataFrame(columns=COL_ORDER)


    # Ensure required columns exist
    for c in COL_ORDER:
        if c not in df_existing.columns:
            df_existing[c] = pd.NA

    ordered = [c for c in COL_ORDER if c in df_existing.columns]
    extras = [c for c in df_existing.columns if c not in COL_ORDER]
    df_existing = df_existing[ordered + extras]

    df_new = pd.DataFrame(new_rows, columns=COL_ORDER)
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)

    # Optional de-dup across canonical columns
    #df_updated.drop_duplicates(subset=COL_ORDER, inplace=True, keep='last')

    # Write back to the sheet
    with pd.ExcelWriter(xlsx_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_updated.to_excel(w, sheet_name=sheet_name, index=False)
    
    # If the sheet was new, we need to re-save the whole workbook
  
    if not sheet_name in pd.ExcelFile(xlsx_path).sheet_names:
        with pd.ExcelWriter(xlsx_path, engine='openpyxl', mode='a') as writer:
            df_updated.to_excel(writer, sheet_name=sheet_name, index=False)


    return len(df_new)

def main():
    if os.path.exists(LOCAL_XLSX_PATH):
        os.remove(LOCAL_XLSX_PATH)

    try:
        # 1) Pull the latest .xlsx from Nextcloud.
        download_from_nextcloud(REMOTE_XLSX_PATH, LOCAL_XLSX_PATH)

        if not os.path.exists(LOCAL_XLSX_PATH):
             raise FileNotFoundError("Neither XLSX nor ODS found locally.")

        # 2) Backup
        atomic_backup(LOCAL_XLSX_PATH)

        # 3) Get data from your desktop flow
        data = sequentialcollection()
        
        if not data:
            print("No rows to add. Exiting without changes.")
            sendnotification("No income rows added.")
            raise SystemExit(0)

        # 4) Normalize rows
        rows = processthespendingdata(data)

        # 5) Append to SPEND DATA sheet
        added = append_rows_to_sheet(LOCAL_XLSX_PATH, TARGET_SHEET, rows)
        logging.info(f"Inserted {added} rows into {TARGET_SHEET}")
        print(f"Inserted {added} rows.")
        sendnotification(f"Inserted {added} spend rows")

        # 6) Push back to Nextcloud
        upload_to_nextcloud(LOCAL_XLSX_PATH, REMOTE_XLSX_PATH)
        print("Sync complete.")
        sendnotification("BusinessManager spend sync complete")

    except Exception as e:
        logging.exception("Failure")
        print(f"Error: {e}")
        traceback.print_exc()
        sendnotification(f"Error: {traceback.format_exc()}")
    finally:
        # 7) Clean up local file
        if os.path.exists(LOCAL_XLSX_PATH):
            os.remove(LOCAL_XLSX_PATH)
            logging.info(f"Cleaned up local file: {LOCAL_XLSX_PATH}")


if __name__ == '__main__':
    main()
