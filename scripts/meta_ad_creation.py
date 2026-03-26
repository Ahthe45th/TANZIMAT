import json
import mimetypes
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests


API_VERSION = "v25.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
TIMEZONE = ZoneInfo("Africa/Nairobi")


def choose_env_file(script_dir: Path) -> Path:
    """
    Ask via rofi whether to use ph_ad.env or uh_ad.env.
    Defaults to ph_ad.env if rofi is unavailable or selection is cancelled.
    """
    options = ["ph_ad.env", "uh_ad.env"]
    prompt = "Choose env"

    try:
        proc = subprocess.run(
            ["rofi", "-dmenu", "-i", "-p", prompt],
            input="\n".join(options),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return script_dir / "ph_ad.env"

    choice = (proc.stdout or "").strip()
    if choice not in options:
        choice = "ph_ad.env"

    return script_dir / choice


def load_env_file(env_path: Path) -> None:
    """
    Minimal .env loader using only the standard library.
    Loads variables from the selected env file in the same directory as this script.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and (
            (value.startswith('"') and value.endswith('"')) or
            (value.startswith("'") and value.endswith("'"))
        ):
            value = value[1:-1]

        os.environ[key] = value


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = choose_env_file(SCRIPT_DIR)
load_env_file(ENV_PATH)


ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
AD_ACCOUNT_ID = os.environ["META_AD_ACCOUNT_ID"]   # no act_ prefix
PAGE_ID = os.environ["META_PAGE_ID"]
IG_ACTOR_ID = os.environ["META_IG_ACTOR_ID"]
VIDEO_PATH = Path(os.environ["VIDEO_PATH"]).expanduser().resolve()

# Optional knobs
COUNTRY = os.environ.get("COUNTRY", "KE")
OBJECTIVE = os.environ.get("OBJECTIVE", "OUTCOME_ENGAGEMENT")  # or OUTCOME_SALES
ADSET_NAME = os.environ.get("ADSET_NAME", "IG Inbox Ad Set")
CREATIVE_MESSAGE = os.environ.get("CREATIVE_MESSAGE", "Send us a message on Instagram.")
STATUS = os.environ.get("STATUS", "PAUSED")
THUMBNAIL_OFFSET_SECONDS = os.environ.get("THUMBNAIL_OFFSET_SECONDS", "1")

# Meta budget fields are in the ad account currency's minimum denomination.
# For KES 17,640.00, this is typically 1,764,000 if your account uses 2 decimals.
LIFETIME_BUDGET_MINOR = int(os.environ.get("LIFETIME_BUDGET_MINOR", "1764000"))

ACCOUNT_PATH = f"act_{AD_ACCOUNT_ID}"


def post(path: str, data: dict, files=None) -> dict:
    url = f"{BASE_URL}/{path}"
    payload = dict(data)
    payload["access_token"] = ACCESS_TOKEN

    response = requests.post(url, data=payload, files=files, timeout=120)
    try:
        result = response.json()
    except Exception:
        response.raise_for_status()
        raise RuntimeError(f"Non-JSON response from Meta: {response.text}")

    if response.status_code >= 400 or "error" in result:
        raise RuntimeError(json.dumps(result, indent=2))

    return result


def get_schedule() -> tuple[str, str, str]:
    """
    Returns:
      campaign_date_str -> YYYY-MM-DD based on start date
      start_time_str    -> string Meta accepts
      end_time_str      -> string Meta accepts
    """
    now = datetime.now(TIMEZONE)
    tomorrow = (now + timedelta(days=1)).date()

    start_dt = datetime(
        tomorrow.year, tomorrow.month, tomorrow.day, 6, 0, 0, tzinfo=TIMEZONE
    )
    end_dt = start_dt + timedelta(days=7)

    campaign_date_str = start_dt.strftime("%Y-%m-%d")
    start_time_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    end_time_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

    return campaign_date_str, start_time_str, end_time_str


def build_names(video_path: Path) -> tuple[str, str]:
    filename = video_path.name
    campaign_date_str, _, _ = get_schedule()
    campaign_name = f"{campaign_date_str} {filename}"
    ad_name = filename
    return campaign_name, ad_name


def upload_video(video_path: Path) -> str:
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    mime_type, _ = mimetypes.guess_type(str(video_path))
    mime_type = mime_type or "video/mp4"

    with video_path.open("rb") as f:
        files = {
            "source": (video_path.name, f, mime_type),
        }
        result = post(f"{ACCOUNT_PATH}/advideos", data={}, files=files)

    video_id = result.get("id")
    if not video_id:
        raise RuntimeError(f"Unexpected advideos response: {json.dumps(result, indent=2)}")

    return video_id


def extract_thumbnail(video_path: Path, output_path: Path, offset_seconds: str = "1") -> Path:
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", str(offset_seconds),
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",
        str(output_path),
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed or not in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffmpeg failed while extracting thumbnail:\n{exc.stderr}"
        ) from exc

    if not output_path.exists():
        raise RuntimeError(f"Thumbnail was not created: {output_path}")

    return output_path


def upload_image(image_path: Path) -> str:
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(str(image_path))
    mime_type = mime_type or "image/jpeg"

    with image_path.open("rb") as f:
        files = {
            "filename": (image_path.name, f, mime_type),
        }
        result = post(f"{ACCOUNT_PATH}/adimages", data={}, files=files)

    images = result.get("images", {})
    if not images:
        raise RuntimeError(f"Unexpected adimages response: {json.dumps(result, indent=2)}")

    first_image = next(iter(images.values()))
    image_hash = first_image.get("hash")
    if not image_hash:
        raise RuntimeError(f"Image hash missing in adimages response: {json.dumps(result, indent=2)}")

    return image_hash


def create_campaign(name: str) -> str:
    result = post(
        f"{ACCOUNT_PATH}/campaigns",
        {
            "name": name,
            "objective": OBJECTIVE,
            "status": STATUS,
            "special_ad_categories": "[]",
            "is_adset_budget_sharing_enabled": "false",
        },
    )
    return result["id"]


def create_ad_set(name: str, campaign_id: str, start_time: str, end_time: str) -> str:
    targeting = {
        "geo_locations": {"countries": [COUNTRY]},
        "publisher_platforms": ["instagram"],
        "instagram_positions": ["stream", "story", "reels"],
    }

    # Monday-Sunday, 07:00-22:00
    # Meta dayparting uses minutes from midnight.
    adset_schedule = [
        {"start_minute": 420, "end_minute": 1320, "days": [1]},  # Monday
        {"start_minute": 420, "end_minute": 1320, "days": [2]},  # Tuesday
        {"start_minute": 420, "end_minute": 1320, "days": [3]},  # Wednesday
        {"start_minute": 420, "end_minute": 1320, "days": [4]},  # Thursday
        {"start_minute": 420, "end_minute": 1320, "days": [5]},  # Friday
        {"start_minute": 420, "end_minute": 1320, "days": [6]},  # Saturday
        {"start_minute": 420, "end_minute": 1320, "days": [0]},  # Sunday
    ]

    promoted_object = {
        "page_id": PAGE_ID,
    }

    result = post(
        f"{ACCOUNT_PATH}/adsets",
        {
            "name": name,
            "campaign_id": campaign_id,
            "lifetime_budget": str(LIFETIME_BUDGET_MINOR),
            "start_time": start_time,
            "end_time": end_time,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "CONVERSATIONS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "destination_type": "INSTAGRAM_DIRECT",
            "status": STATUS,
            "targeting": json.dumps(targeting),
            "adset_schedule": json.dumps(adset_schedule),
            "pacing_type": json.dumps(["day_parting"]),
            "promoted_object": json.dumps(promoted_object),
        },
    )
    return result["id"]


def create_video_creative(video_id: str, image_hash: str, creative_name: str) -> str:
    object_story_spec = {
        "page_id": PAGE_ID,
        "instagram_user_id": IG_ACTOR_ID,
        "video_data": {
            "video_id": video_id,
            "image_hash": image_hash,
            "message": CREATIVE_MESSAGE,
            "call_to_action": {
                "type": "MESSAGE_PAGE"
            },
        },
    }

    result = post(
        f"{ACCOUNT_PATH}/adcreatives",
        {
            "name": creative_name,
            "object_story_spec": json.dumps(object_story_spec),
        },
    )
    return result["id"]


def main() -> None:
    campaign_name, ad_name = build_names(VIDEO_PATH)
    creative_name = f"{VIDEO_PATH.name} creative"
    _, start_time, end_time = get_schedule()

    thumbnail_path = VIDEO_PATH.with_suffix(".jpg")

    print(f"Using env file: {ENV_PATH.name}")

    #print("Uploading video...")
    #video_id = upload_video(VIDEO_PATH)
    #print("video_id:", video_id)

    #print("Extracting thumbnail...")
    #extract_thumbnail(
    #    VIDEO_PATH,
    #    thumbnail_path,
    #    offset_seconds=THUMBNAIL_OFFSET_SECONDS,
    #)
    #print("thumbnail_path:", thumbnail_path)

    #print("Uploading thumbnail...")
    #image_hash = upload_image(thumbnail_path)
    #print("image_hash:", image_hash)

    print("Creating campaign...")
    campaign_id = create_campaign(campaign_name)
    print("campaign_id:", campaign_id)

    print("Creating ad set...")
    adset_id = create_ad_set(ADSET_NAME, campaign_id, start_time, end_time)
    print("adset_id:", adset_id)

    #print("Creating creative...")
    #creative_id = create_video_creative(video_id, image_hash, creative_name)
    #print("creative_id:", creative_id)

    print("\nStopped before final ad creation.")
    print("Campaign name:", campaign_name)
    print("Ad name that would have been used:", ad_name)
    print("Start:", start_time)
    print("End:", end_time)
    print("Lifetime budget (minor units):", LIFETIME_BUDGET_MINOR)
    #print("Thumbnail image hash:", image_hash)
    print("No /ads call was made.")


if __name__ == "__main__":
    main()
