import datetime
import pyperclip 
import requests 
import json 
import os 
import gspread
import subprocess
import traceback 

from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

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
        options = question["options"]
        questionoptions = '\n'.join(options)+'\nquit'
        result = subprocess.getoutput(f"""echo "{questionoptions}" | DISPLAY=:0.0 rofi -dmenu -p '{prompt} {question["question"]}'""")
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

def getdaydata():
    contents = inputhandler("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.\nIf in batch make sure to put a * before each phone and add metadata i.e *Phone Balances 17/2/90 0+23+39", multiline=True)
    return contents

def sequentialcollection():
    data = []
    gettingdata = True
    
    print("Enter the day data")
    while gettingdata:
        daydata = getdaydata()
        if daydata:
            print(daydata)
            expenditureitems = daydata.split("Expenditure")[1]
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

def insert_multiple_rows(sheet, data_list):
    """
    Inserts multiple rows of data into the first available empty rows where columns K and L are empty,
    filling data into columns A-H.

    :param sheet: gspread worksheet object
    :param data_list: List of dictionaries containing data to insert
    """
    # Get all values in columns K and L
    col_k_l = sheet.range("K1:L" + str(sheet.row_count))  # Fetch K and L values for all rows
    
    # Convert to row-wise structure
    col_k_l_rows = [col_k_l[i:i+2] for i in range(0, len(col_k_l), 2)]  # Group into row pairs

    # Find the first empty row in columns K and L
    first_empty_row = 1  # Default to first row
    for idx, row in enumerate(col_k_l_rows, start=1):
        if all(cell.value in (None, '') for cell in row):  # Check if both K and L are empty
            first_empty_row = idx
            break

    # Prepare data for batch update
    batch_data = []
    for data_dict in data_list:
        row_data = [data_dict.get(x, "") for x in data_dict]  # Extract values in order
        batch_data.append(row_data)
        first_empty_row += 1  # Move to the next row for the next dictionary

    # Update the sheet with batch data
    sheet.update(batch_data, f"J{first_empty_row - len(data_list)}:T{first_empty_row - 1}", value_input_option='USER_ENTERED')
    print(f"{len(data_list)} rows inserted starting from row {first_empty_row - len(data_list)}")

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
            spendpartofitem = item.split('\n')[0].replace("İ", "I").split("Item: ")[1].lower().strip()

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
        expenditureitems = [x for x in expenditureitems if x]
        
        for item in expenditureitems:
            print("The item")
            print(item)
            processdataitem = dict.fromkeys(spendcategories,0)
            processdataitem['DATE'] = day["date"]
            dateject = datetime.datetime.strptime(day["date"], "%d/%m/%y")
            processdataitem['MONTH'] = f"{dateject.strftime("%m/").lstrip('0')}{dateject.year-2000}"
            
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
        processdataitem['MONTH'] = f"{dateject.strftime("%m/").lstrip('0')}{dateject.year-2000}"
        processdataitem["BIZ COSTS"] = sum([float(x) for x in day["otheritems"].split("+")]) + processdataitem["BIZ COSTS"]
        processdataitem["SPEND"] = processdataitem["BIZ COSTS"]
        processdataitem['TAG'] = "transaction costs"

        processeddata.append(processdataitem)
        processeddata.append({"DATE":day["date"]})
    return processeddata

def reformatdata(processeddata, columns):
    reformatted = []
    for dataitem in processeddata:
        newitem = {}
        for property in columns:
            newitem[columns[property]] = dataitem.get(property, "0")
        reformatted.append(newitem)
    return reformatted 

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

def main():
    collectiontype = promptforquestion(osdatacollectionquestion, ["type"])["type"][0]
    if collectiontype == "sequential":
        data = sequentialcollection()
    elif collectiontype == "prayer":
        get_prayer_times()
    elif collectiontype == "balance":
        getbalance()
    else: 
        data = batchcollection()
    processeddata = processthespendingdata(data)
    
    columns = {
        "DATE": "J",
        "SPEND": "K",
        "DOMESTIC SPEND": "L",
        "TAG": "M",
        "S2": "N",
        "S3": "O",
        "S4": "P",
        "R": "Q",
        "AD SPEND": "R",
        "MONTH": "S",
        "BIZ COSTS": "T"
    }

    reformatted = reformatdata(processeddata, columns)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name("/home/mehmet/.config/automationscripts/sheets-449816-6fd98df406c1.json", scope)
    # Authorize the clientsheet 
    client = gspread.authorize(creds)
    # Get the instance of the Spreadsheet
    sheet = client.open("BUSINESS MANAGER")
    # Get the first sheet of the Spreadsheet
    incomeandspendworksheet = sheet.get_worksheet(0)

    insert_multiple_rows(incomeandspendworksheet, reformatted)
    get_prayer_times()
    sendnotification("Data inserted successfully.")

if __name__ == '__main__':
    main()