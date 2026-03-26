import os, math, json, datetime, logging, subprocess, shutil, sys
import pandas as pd
from dotenv import load_dotenv

# Get the absolute path of the directory containing THIS script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import gui_utils

# ----------------- CONFIG -----------------
ENV_PATH = os.path.join(SCRIPT_DIR, "tanzimat.env")
load_dotenv(ENV_PATH)

LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "businessmanager_write_xlsx.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Nextcloud paths
REMOTE_XLSX_PATH = "/Documents/BUSINESSMANAGER.xlsx"
REMOTE_ODS_PATH  = "/Documents/BUSINESSMANAGER.ods"

LOCAL_XLSX_PATH  = os.path.join(SCRIPT_DIR, "BUSINESSMANAGER.xlsx")
LOCAL_ODS_PATH   = os.path.join(SCRIPT_DIR, "BUSINESSMANAGER.ods")

TARGET_SHEET = "İNCOME DATA"
COL_ORDER = ["DATE","PERSON","AMOUNT","TYPE","DAY","MONTH","QUARTER","BUSINESS"]

OSCATEGORY_QUESTIONS = [
    {"question": "Business type", "options": ["PENZIHALISI", "OKAGWALAOKUTUUFU", "UH"], "param": "type"},
]

# ----------------- DESKTOP UI HELPERS -----------------
def rofioptionsget(questions: list, prompt: str = ""):
    answers = {}
    for q in questions:
        options = q["options"] + ["quit"]
        result = gui_utils.get_rofi_menu(f"{prompt}{q['question']}", options)
        if result and result != "quit":
            answers[q["param"]] = [result]
        else:
            sys.exit(0)
    return answers

def inputget(question, multiline=False):
    if multiline:
        prompt_message = f"{question}\n\nMake sure to delete everything here before inputting your own data."
        # Custom zenity for multiline with specific dimensions
        try:
            r = subprocess.run(
                ['zenity','--text-info','--editable','--title','Multiline Input',
                 '--width','500','--height','350'],
                input=prompt_message, capture_output=True, text=True
            )
            return r.stdout.strip()
        except Exception:
            return None
    else:
        return gui_utils.get_rofi_input(question)

def clipboardread():
    theinput = inputget("Paste the income text you copied:", multiline=True)
    if not theinput:
        return []
    # Call your LLM formatter.
    cmd = f'''echo "{theinput.replace("'", "")}" | /home/mehmet/.local/bin/fabric -m nousresearch/hermes-4-70b --pattern incomelastweek'''
    result = subprocess.getoutput(cmd).strip()
    try:
        return json.loads(result)
    except Exception:
        return []

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

# ----------------- CLOUD I/O -----------------
def download_from_nextcloud(remote_path, local_path):
    logging.info(f"Downloading {remote_path} -> {local_path}")
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
    logging.info(f"Uploading {local_path} -> {remote_path}")
    subprocess.run(
        [
            "scp",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=yes",
            LOCAL_XLSX_PATH,
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx",
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

# ----------------- DATA NORMALIZATION -----------------
def parse_date_flex(s: str) -> datetime.date:
    s = s.strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized DATE: {s}")

def normalize_rows(raw_rows):
    out = []
    for item in raw_rows:
        row = {k: item.get(k) for k in COL_ORDER}
        if not row.get("DATE"):
            row["DATE"] = inputget(f"{item}\nEnter date dd/mm/yy or dd/mm/yyyy:").strip()
        d = parse_date_flex(str(row["DATE"]))

        amt_raw = item.get("AMOUNT")
        if amt_raw is None or str(amt_raw).strip() == "":
            raise ValueError(f"AMOUNT missing in row: {item}")
        amt = float(str(amt_raw).replace(",", "").strip())
        row["AMOUNT"] = amt

        row["TYPE"] = (row.get("TYPE") or "").strip()
        row["PERSON"] = (row.get("PERSON") or "").strip()

        if not row.get("BUSINESS"):
            ans = promptforquestion(OSCATEGORY_QUESTIONS, ["type"], prompt=f'{row["PERSON"]} {amt}: ')
            row["BUSINESS"] = ans["type"][0]

        row["DAY"] = d.strftime("%A")
        row["MONTH"] = f"{d.month}/{d.year - 2000}"
        row["QUARTER"] = f"Q{math.ceil(d.month/3)}{d.year}"

        row = {c: row.get(c) for c in COL_ORDER}
        out.append(row)
    return out

# ----------------- SHEET UPDATE -----------------
def append_rows_to_sheet(xlsx_path, sheet_name, new_rows):
    df_existing = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")
    for c in COL_ORDER:
        if c not in df_existing.columns:
            df_existing[c] = pd.NA

    ordered = [c for c in COL_ORDER if c in df_existing.columns]
    extras = [c for c in df_existing.columns if c not in COL_ORDER]
    df_existing = df_existing[ordered + extras]

    df_new = pd.DataFrame(new_rows, columns=COL_ORDER)
    df_updated = pd.concat([df_existing, df_new], ignore_index=True)
    df_updated.drop_duplicates(subset=COL_ORDER, inplace=True)

    with pd.ExcelWriter(xlsx_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_updated.to_excel(w, sheet_name=sheet_name, index=False)
    return len(df_new)

def convert_local_ods_to_xlsx(ods_path, xlsx_path):
    sheets = pd.read_excel(ods_path, sheet_name=None, engine="odf")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if df is None:
                df = pd.DataFrame()
            df.to_excel(writer, sheet_name=name, index=False)

# ----------------- MAIN -----------------
if __name__ == "__main__":
    try:
        download_from_nextcloud(REMOTE_XLSX_PATH, LOCAL_XLSX_PATH)

        if not os.path.exists(LOCAL_XLSX_PATH):
            logging.warning("XLSX not found after download. Trying ODS then convert.")
            download_from_nextcloud(REMOTE_ODS_PATH, LOCAL_ODS_PATH)
            if not os.path.exists(LOCAL_ODS_PATH):
                raise FileNotFoundError("Neither XLSX nor ODS found locally.")
            convert_local_ods_to_xlsx(LOCAL_ODS_PATH, LOCAL_XLSX_PATH)

        atomic_backup(LOCAL_XLSX_PATH)
        raw_rows = clipboardread()

        if not raw_rows:
            print("No rows to add. Exiting.")
            gui_utils.notify("Income Recorder", "No income rows added.")
            sys.exit(0)

        rows = normalize_rows(raw_rows)
        added = append_rows_to_sheet(LOCAL_XLSX_PATH, TARGET_SHEET, rows)
        logging.info(f"Inserted {added} rows into {TARGET_SHEET}")
        gui_utils.notify("Income Recorder", f"Inserted {added} income rows")

        upload_to_nextcloud(LOCAL_XLSX_PATH, REMOTE_XLSX_PATH)
        gui_utils.notify("Income Recorder", "BusinessManager sync complete")

    except Exception as e:
        logging.exception("Failure")
        print(f"Error: {e}")
        gui_utils.notify("Income Recorder Error", str(e))
