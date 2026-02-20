import os, math, json, datetime, logging, subprocess, shutil
import pandas as pd
from dotenv import load_dotenv

# ----------------- CONFIG -----------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(SCRIPT_DIR, "tanzimat.env")
load_dotenv(ENV_PATH)

LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "businessmanager_write_xlsx.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Nextcloud paths (edit to match your setup)
REMOTE_XLSX_PATH = "/Documents/BUSINESSMANAGER.xlsx"  # keep master as .xlsx in Nextcloud
REMOTE_ODS_PATH  = "/Documents/BUSINESSMANAGER.ods"   # only used if you still keep an .ods upstream

LOCAL_XLSX_PATH  = os.path.join(SCRIPT_DIR, "BUSINESSMANAGER.xlsx")
LOCAL_ODS_PATH   = os.path.join(SCRIPT_DIR, "BUSINESSMANAGER.ods")

GET_FROM_NC = os.path.join(SCRIPT_DIR, "get_from_nextcloud.sh")
PUT_TO_NC   = os.path.join(SCRIPT_DIR, "put_to_nextcloud.sh")

TARGET_SHEET = "İNCOME DATA"   # dotted capital İ
COL_ORDER = ["DATE","PERSON","AMOUNT","TYPE","DAY","MONTH","QUARTER","BUSINESS"]

# Business classification prompt
OSCATEGORY_QUESTIONS = [
    {"question": "Business type", "options": ["PENZIHALISI", "OKAGWALAOKUTUUFU", "UH"], "param": "type"},
]

# ----------------- DESKTOP UI HELPERS -----------------
def rofioptionsget(questions: list, prompt: str = ""):
    answers = {}
    for q in questions:
        options = q["options"]
        questionoptions = "\n".join(options) + "\nquit"
        cmd = f'''echo "{questionoptions}" | DISPLAY=:0.0 rofi -dmenu -p '{prompt}{q["question"]}\n' '''
        result = subprocess.getoutput(cmd).strip()
        if result != "quit":
            answers[q["param"]] = [result]
        else:
            raise SystemExit(0)
    return answers

def sendnotification(text: str):
    subprocess.getoutput(f"DISPLAY=:0.0 notify-send '{text}'")

def inputget(question, multiline=False):
    if multiline:
        prompt_message = f"{question}\n\nMake sure to delete everything here before inputting your own data."
        r = subprocess.run(
            ['zenity','--text-info','--editable','--title','Multiline Input',
             '--width','500','--height','350','--filename=/dev/stdin'],
            input=prompt_message, capture_output=True, text=True
        )
        return r.stdout.strip()
    else:
        return subprocess.getoutput(f"echo '' | DISPLAY=:0.0 rofi -dmenu -p '{question}'").rstrip()

def inputhandler(prompt, multiline=False):
    try:
        return inputget(prompt, multiline=multiline)
    except Exception:
        return input(prompt)

def clipboardread():
    theinput = inputhandler("Paste the income text you copied:", multiline=True)
    # Call your LLM formatter. Keep your exact binary and pattern.
    cmd = f'''echo "{theinput.replace("'", "")}" | /home/mehmet/.local/bin/fabric -m nousresearch/hermes-4-70b --pattern incomelastweek'''
    result = subprocess.getoutput(cmd).strip()
    return json.loads(result)

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
            "jazeelakarima@expatelitesingles.com:/home/jazeelakarima/RAHIB/RAHIB/STORAGE/BUSINESSMANAGER.xlsx",
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
            # ask for missing date if your LLM output omitted it
            row["DATE"] = inputhandler(f"{item}\nEnter date dd/mm/yy or dd/mm/yyyy:", multiline=False).strip()
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

        # enforce column order
        row = {c: row.get(c) for c in COL_ORDER}
        out.append(row)
    return out

# ----------------- SHEET UPDATE -----------------
def append_rows_to_sheet(xlsx_path, sheet_name, new_rows):
    # Read target sheet only
    df_existing = pd.read_excel(xlsx_path, sheet_name=sheet_name, engine="openpyxl")

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
    df_updated.drop_duplicates(subset=COL_ORDER, inplace=True)

    # Write back only this sheet
    with pd.ExcelWriter(xlsx_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_updated.to_excel(w, sheet_name=sheet_name, index=False)

    return len(df_new)

# ----------------- OPTIONAL ODS -> XLSX ONE-TIME CONVERSION -----------------
def convert_local_ods_to_xlsx(ods_path, xlsx_path):
    # Reads all sheets from ODS and writes to XLSX once
    sheets = pd.read_excel(ods_path, sheet_name=None, engine="odf")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            if df is None:
                df = pd.DataFrame()
            df.to_excel(writer, sheet_name=name, index=False)

# ----------------- MAIN -----------------
if __name__ == "__main__":
    try:
        # 1) Pull the latest .xlsx from Nextcloud.
        #    If you have not yet switched to xlsx upstream, you can comment this line
        #    and instead download the .ods, then run the one-time conversion below.
        download_from_nextcloud(REMOTE_XLSX_PATH, LOCAL_XLSX_PATH)

        if not os.path.exists(LOCAL_XLSX_PATH):
            # Fallback if you still keep only ODS upstream
            logging.warning("XLSX not found after download. Trying ODS then convert.")
            download_from_nextcloud(REMOTE_ODS_PATH, LOCAL_ODS_PATH)
            if not os.path.exists(LOCAL_ODS_PATH):
                raise FileNotFoundError("Neither XLSX nor ODS found locally.")
            convert_local_ods_to_xlsx(LOCAL_ODS_PATH, LOCAL_XLSX_PATH)

        # 2) Backup
        atomic_backup(LOCAL_XLSX_PATH)

        # 3) Get data from your desktop flow
        raw_rows = clipboardread()  # list of dicts from your LLM pattern
        # If you want to test quickly without LLM, uncomment:
        # raw_rows = [
        #   {"DATE":"29/10/2025","PERSON":"Jane","AMOUNT":"3187","TYPE":"SALE","BUSINESS":"PENZIHALISI"},
        #   {"DATE":"29/10/2025","PERSON":"Mary","AMOUNT":"5800","TYPE":"SALE","BUSINESS":"PENZIHALISI"},
        # ]

        if not raw_rows:
            print("No rows to add. Exiting without changes.")
            sendnotification("No income rows added.")
            raise SystemExit(0)

        # 4) Normalize rows, fill DAY/MONTH/QUARTER, classify BUSINESS if missing
        rows = normalize_rows(raw_rows)

        # 5) Append only to INCOME DATA
        added = append_rows_to_sheet(LOCAL_XLSX_PATH, TARGET_SHEET, rows)
        logging.info(f"Inserted {added} rows into {TARGET_SHEET}")
        print(f"Inserted {added} rows.")
        sendnotification(f"Inserted {added} income rows")

        # 6) Push back to Nextcloud
        upload_to_nextcloud(LOCAL_XLSX_PATH, REMOTE_XLSX_PATH)
        print("Sync complete.")
        sendnotification("BusinessManager sync complete")

    except Exception as e:
        logging.exception("Failure")
        print(f"Error: {e}")
        sendnotification(f"Error: {e}")
