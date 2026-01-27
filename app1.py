import streamlit as st
import pandas as pd
import os

BASE_DIR = "pipeline_deduplication"

CLEANED_EVENTS_FILE = os.path.join(BASE_DIR, "cleaned_events.csv")
REPETITION_SUMMARY_FILE = os.path.join(BASE_DIR, "repetition_summary.csv")
UNIQUE_USERS_FILE = os.path.join(BASE_DIR, "unique_users_list.csv")

for f in [CLEANED_EVENTS_FILE, REPETITION_SUMMARY_FILE, UNIQUE_USERS_FILE]:
    if not os.path.exists(f):
        st.error(f"Missing required file: {f}")
        st.stop()

df = pd.read_csv(CLEANED_EVENTS_FILE)
summary = pd.read_csv(REPETITION_SUMMARY_FILE)
users_df = pd.read_csv(UNIQUE_USERS_FILE)

st.set_page_config(page_title="Deduplicated Events", layout="wide")
st.title("Apni Bus Events Explorer")

total_users = users_df["user_uuid"].nunique()
total_events = len(df)

c1, c2 = st.columns(2)
c1.metric("Total Unique Users", total_users)

st.divider()

user_ids = users_df["user_uuid"].sort_values().tolist()
selected_user = st.selectbox("Select User ID", user_ids)

user_df = df[df["user_uuid"] == selected_user]

user_event_count = len(user_df)
user_unique_events = user_df["event_name"].nunique()

c3, c4 = st.columns(2)
c3.metric("Events for Selected User", user_event_count)
c4.metric("Unique Event Types", user_unique_events)

st.divider()

user_events = (
    user_df["event_name"]
    .sort_values()
    .unique()
    .tolist()
)

selected_event = st.selectbox(
    "Select Event",
    ["All Events"] + user_events
)

if selected_event == "All Events":
    view_df = user_df
else:
    view_df = user_df[user_df["event_name"] == selected_event]

view_df = view_df.sort_values(["event_date", "event_time_only"])

display_cols = [
    "event_date",
    "event_day",
    "event_time_only",
    "event_name",
    "category"
]

st.dataframe(
    view_df[display_cols],
    use_container_width=True,
    hide_index=True
)

st.divider()

summary_view = summary[summary["user_uuid"] == selected_user]

if selected_event != "All Events":
    summary_view = summary_view[
        summary_view["event_name"] == selected_event
    ]

st.dataframe(
    summary_view,
    use_container_width=True,
    hide_index=True
)
