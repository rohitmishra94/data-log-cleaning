import pandas as pd
import os
from pathlib import Path

SCRIPT_NAME = Path(__file__).stem
BASE_DIR = SCRIPT_NAME
PER_USER_DIR = os.path.join(BASE_DIR, "per_user_timelines")

if os.path.exists(BASE_DIR):
    raise RuntimeError(f"Output folder '{BASE_DIR}' already exists.")

os.makedirs(PER_USER_DIR)

INPUT_FILE = "pipeline_deduplication/cleaned_events.csv"

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Required input file not found: {INPUT_FILE}. "
        "Run pipeline_deduplication.py first."
    )

df = pd.read_csv(INPUT_FILE)

df["event_time"] = pd.to_datetime(
    df["event_time"],
    format="ISO8601",
    errors="raise"
)

df = df.sort_values(
    by=["user_uuid", "event_time"],
    kind="mergesort"
).reset_index(drop=True)

df["prev_event_name"] = df.groupby("user_uuid")["event_name"].shift(1)

df["is_canonical"] = (
    df["prev_event_name"].isna() | (df["event_name"] != df["prev_event_name"])
)

df = df.drop(columns=["prev_event_name"])

cleaned_timeline = df[df["is_canonical"]].drop(
    columns=["is_canonical"]
)

df["is_consecutive_dup"] = ~df["is_canonical"]

consecutive_dups = df[df["is_consecutive_dup"]].copy()

if len(consecutive_dups) > 0:
    repetition_summary = (
        consecutive_dups.groupby(["user_uuid", "event_name", "category", "event_date"], as_index=False)
          .agg(
              start_time=("event_time", "min"),
              end_time=("event_time", "max"),
              frequency=("event_time", "size")
          )
    )
    repetition_summary["repetitions_removed"] = repetition_summary["frequency"]
else:
    repetition_summary = pd.DataFrame(columns=[
        "user_uuid", "event_name", "category", "event_date", "start_time", "end_time",
        "frequency", "repetitions_removed"
    ])

if len(repetition_summary) > 0:
    repetition_summary["start_time"] = (
        repetition_summary["start_time"].dt.strftime("%H:%M:%S.%f")
    )
    repetition_summary["end_time"] = (
        repetition_summary["end_time"].dt.strftime("%H:%M:%S.%f")
    )
    repetition_summary["event_day"] = (
        pd.to_datetime(repetition_summary["event_date"])
          .dt.day_name()
    )

unique_users = cleaned_timeline[["user_uuid"]].drop_duplicates()

unique_users_report = pd.DataFrame({
    "metric": ["total_unique_users"],
    "value": [len(unique_users)]
})

cleaned_timeline.to_csv(
    os.path.join(BASE_DIR, "cleaned_events_chronological.csv"),
    index=False
)

repetition_summary.to_csv(
    os.path.join(BASE_DIR, "repetition_summary.csv"),
    index=False
)

unique_users.to_csv(
    os.path.join(BASE_DIR, "unique_users_list.csv"),
    index=False
)

unique_users_report.to_csv(
    os.path.join(BASE_DIR, "unique_users_count.csv"),
    index=False
)

for uid, udf in cleaned_timeline.groupby("user_uuid", sort=False):
    safe_uid = str(uid).replace("/", "_").replace("\\", "_")
    udf.to_csv(
        os.path.join(PER_USER_DIR, f"user_{safe_uid}_timeline.csv"),
        index=False
    )
