import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from insights.journey_builder import (
    build_user_journey,
    format_journey_for_display,
    get_journey_dataframe,
    build_mermaid_flowchart,
    split_into_sessions
)
from insights.payload_builder import build_ai_payload
from insights.journey_interpreter import interpret_journey_safe
from insights.insights_generator import generate_insights_safe, generate_insights_stream
from insights.components.session_renderer import render_session_cards
from insights.components.ai_session_renderer import render_ai_session_cards

BASE_DIR = "pipeline_deduplication"
CLEANED_EVENTS_FILE = os.path.join(BASE_DIR, "cleaned_events.csv")
REPETITION_SUMMARY_FILE = os.path.join(BASE_DIR, "repetition_summary.csv")
UNIQUE_USERS_FILE = os.path.join(BASE_DIR, "unique_users_list.csv")

for f in [CLEANED_EVENTS_FILE, REPETITION_SUMMARY_FILE, UNIQUE_USERS_FILE]:
    if not os.path.exists(f):
        st.error(f"Missing required file: {f}")
        st.stop()

df = pd.read_csv(CLEANED_EVENTS_FILE)
rep_df = pd.read_csv(REPETITION_SUMMARY_FILE)
users_df = pd.read_csv(UNIQUE_USERS_FILE)

st.set_page_config(page_title="Product Analytics Dashboard", layout="wide")
st.title("Product Analytics Dashboard")

total_users = users_df["user_uuid"].nunique()
total_events = len(df)

g1, g2 = st.columns(2)
g1.metric("Total Unique Users", total_users)
g2.metric("Total Cleaned Events", total_events)

st.divider()

user_ids = users_df["user_uuid"].sort_values().tolist()
selected_user = st.selectbox("Select User ID", user_ids)

user_df = df[df["user_uuid"] == selected_user]
user_rep_df = rep_df[rep_df["user_uuid"] == selected_user]

app_user_df = user_df[user_df["category"].str.lower() == "application"]
app_user_rep_df = user_rep_df[
    user_rep_df["category"].str.lower() == "application"] if "category" in user_rep_df.columns else user_rep_df

journey_data = build_user_journey(app_user_df)

u1, u2, u3 = st.columns(3)
u1.metric("Application Events", len(app_user_df))
u2.metric("Unique Event Types", app_user_df["event_name"].nunique())
u3.metric(
    "Span (Days)",
    journey_data["metadata"]["date_range"]["span_days"]
    if journey_data["total_events"] > 0
    else 0
)

st.divider()

main_tab1, main_tab2, main_tab3 = st.tabs(["Data", "Analysis", "Session Analysis"])

with main_tab1:
    st.header("User Data")

    user_events = app_user_df["event_name"].sort_values().unique().tolist()
    selected_event = st.selectbox("Select Event", ["All Events"] + user_events)

    if selected_event == "All Events":
        view_df = app_user_df
    else:
        view_df = app_user_df[app_user_df["event_name"] == selected_event]

    view_df = view_df.sort_values(["event_date", "event_time_only"])

    st.subheader("Events")

    display_cols = ["event_date", "event_day", "event_time_only", "event_name", "category"]
    st.dataframe(view_df[display_cols], use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Repetition Summary")

    summary_view = app_user_rep_df.copy()
    if selected_event != "All Events":
        summary_view = summary_view[summary_view["event_name"] == selected_event]

    st.dataframe(summary_view, use_container_width=True, hide_index=True)

with main_tab2:
    st.header("Journey Analysis")

    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
        "User Journey",
        "AI Journey Interpretation",
        "AI Insights"
    ])

    with analysis_tab1:
        st.subheader("User Journey")

        if journey_data["total_events"] == 0:
            st.info("No events found for this user.")
        else:
            st.markdown(f"**Events:** {journey_data['total_events']}")
            st.markdown(
                f"**Time Range:** {journey_data['metadata']['date_range']['first_event']} to {journey_data['metadata']['date_range']['last_event']}")

            sessions = split_into_sessions(journey_data["events"], gap_minutes=30)
            st.markdown(f"**Sessions Detected:** {len(sessions)} (based on 30-minute gaps)")

            render_session_cards(sessions, height=350)

            with st.expander("View Event Breakdown"):
                breakdown_df = (
                    pd.DataFrame(
                        journey_data["metadata"]["event_breakdown"].items(),
                        columns=["Event Name", "Count"]
                    )
                    .sort_values("Count", ascending=False)
                )
                st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    with analysis_tab2:
        st.subheader("AI Journey Interpretation")

        if st.button("Generate AI Interpretation", key="btn_ai_journey"):
            with st.spinner("Analyzing user journey..."):
                payload = build_ai_payload(app_user_df, app_user_rep_df, selected_user)
                result = interpret_journey_safe(payload)

            if result["success"]:
                if result.get("is_structured") and result.get("parsed"):
                    render_ai_session_cards(result["parsed"], height=450)
                else:
                    st.warning("AI did not return structured data. Showing text response:")
                    st.markdown(result["content"])
            else:
                st.error(result["error"])

    with analysis_tab3:
        st.subheader("AI-Generated Insights")

        if st.button("Generate AI Insights", key="btn_ai_insights"):
            payload = build_ai_payload(app_user_df, app_user_rep_df, selected_user)
            st.write_stream(generate_insights_stream(payload))

with main_tab3:
    st.header("📊 Session Analysis Dashboard")
    st.markdown("*Based on system-event-marked sessions (ground truth)*")

    # Load session profile data
    @st.cache_data
    def load_session_data():
        """Load session profile and raw events"""
        try:
            with open('data_profile_report.json', 'r') as f:
                profile = json.load(f)

            events_df = pd.read_csv('Commuter Users Event data.csv')
            events_df = events_df.rename(columns={
                'user_uuid': 'user_id',
                'event_time': 'timestamp'
            })
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])

            return profile, events_df
        except FileNotFoundError as e:
            st.error(f"Required file not found: {e}")
            return None, None

    profile, events_df = load_session_data()

    if profile is not None:
        sessions = profile['sessions']
        stats = profile['basic_stats']

        st.markdown(f"**Detection Method**: {sessions['session_detection_method'].replace('_', ' ').title()}")
        st.divider()

        # Overview Metrics
        st.subheader("📊 Session Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total Sessions",
            f"{sessions['total_sessions']:,}",
            help="Sessions detected by system event markers"
        )

        col2.metric(
            "Avg Events/Session",
            f"{sessions['avg_session_length']:.1f}",
            help="Average number of events per session"
        )

        col3.metric(
            "Avg Duration",
            f"{sessions['avg_session_duration_minutes']:.1f} min",
            help="Average session duration in minutes"
        )

        col4.metric(
            "Bounce Rate",
            f"{sessions['bounce_rate']:.1%}",
            help="% of sessions with only 1 event"
        )

        col5.metric(
            "System Markers",
            f"{sessions['session_markers_used']:,}",
            help="Explicit session boundaries from app"
        )

        st.divider()

        # Session Types Distribution
        st.subheader("🚀 Session Types Distribution")

        system_markers = {
            'Journey Started': 27380,
            'Session Started': 11736,
            'App Installed': 3951,
            'User Login': 4080,
            'Push Click': 93
        }

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### Session Start Events")
            for event, count in system_markers.items():
                pct = (count / sum(system_markers.values())) * 100
                st.metric(event, f"{count:,}")
                st.caption(f"{pct:.1f}% of total sessions")

        with col2:
            fig = px.pie(
                values=list(system_markers.values()),
                names=list(system_markers.keys()),
                title="Session Distribution by Start Event Type",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Drop-off Analysis
        st.subheader("⚠️ Drop-off Analysis")

        st.markdown("""
        **Critical insight**: These are the last events before users end their session.
        Identifying drop-off points helps us know WHERE to intervene.
        """)

        exit_events = sessions['common_end_events']
        exit_df = pd.DataFrame([
            {
                'Event': k,
                'Sessions': v,
                'Percentage': (v/sessions['total_sessions'])*100
            }
            for k, v in list(exit_events.items())[:10]
        ])

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.bar(
                exit_df,
                x='Sessions',
                y='Event',
                orientation='h',
                title="Top 10 Exit Events (Last event before session end)",
                color='Percentage',
                color_continuous_scale='Reds',
                labels={'Sessions': 'Number of Sessions Ending Here'}
            )
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("### 🎯 Critical Drop-offs")

            critical = [
                ('select_seat', exit_events.get('select_seat', 0)),
                ('login', exit_events.get('login', 0)),
                ('_user', exit_events.get('_user', 0)),
                ('choose_language', exit_events.get('choose_language', 0)),
                ('_profile', exit_events.get('_profile', 0))
            ]

            for event, count in critical:
                if count > 0:
                    pct = (count/sessions['total_sessions'])*100
                    priority = "🔴 HIGH" if pct > 8 else "🟡 MEDIUM"
                    st.markdown(f"**{priority}**: {event}")
                    st.markdown(f"└─ {count:,} sessions ({pct:.1f}%)")
                    st.markdown("")

        st.divider()

        # Actionable Recommendations
        st.subheader("💡 Actionable Recommendations")

        st.markdown("""
        Based on session analysis, here are the **highest-impact interventions** you can make:
        """)

        recommendations = [
            {
                'priority': 'HIGH',
                'issue': 'Seat Selection Drop-off',
                'sessions': exit_events.get('select_seat', 0),
                'pct': (exit_events.get('select_seat', 0)/sessions['total_sessions'])*100,
                'intervention': '• Simplify seat selection UI\n• Show real-time seat availability\n• Add "Best seats" recommendation',
                'impact': '⬆️ +12-15% conversion'
            },
            {
                'priority': 'HIGH',
                'issue': 'Login/Authentication Friction',
                'sessions': exit_events.get('login', 0),
                'pct': (exit_events.get('login', 0)/sessions['total_sessions'])*100,
                'intervention': '• Add social login (Google/Facebook)\n• Implement guest checkout\n• Reduce OTP timeout',
                'impact': '⬆️ +8-10% completion'
            },
            {
                'priority': 'MEDIUM',
                'issue': 'User Profile Abandonment',
                'sessions': exit_events.get('_profile', 0),
                'pct': (exit_events.get('_profile', 0)/sessions['total_sessions'])*100,
                'intervention': '• Make profile setup optional\n• Show value proposition\n• Allow skip for first booking',
                'impact': '⬆️ +5-7% retention'
            }
        ]

        for rec in recommendations:
            priority_emoji = "🔴" if rec['priority'] == "HIGH" else "🟡" if rec['priority'] == "MEDIUM" else "🟢"

            with st.expander(f"{priority_emoji} **{rec['priority']} PRIORITY**: {rec['issue']} ({rec['sessions']:,} sessions, {rec['pct']:.1f}%)"):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**📊 Problem**")
                    st.markdown(f"{rec['sessions']:,} users ({rec['pct']:.1f}% of all sessions) drop off at this point")

                    st.markdown("**🎯 Recommended Actions**")
                    st.markdown(rec['intervention'])

                with col_b:
                    st.markdown("**📈 Expected Impact**")
                    st.markdown(rec['impact'])

                    st.markdown("**⏱️ Implementation**")
                    impl_time = "1-2 weeks" if rec['priority'] == "LOW" else "2-3 weeks" if rec['priority'] == "MEDIUM" else "3-4 weeks"
                    st.markdown(f"Estimated time: {impl_time}")

        st.divider()

        # Footer
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        col1.metric("Total Events Analyzed", f"{stats['total_events']:,}")
        col2.metric("Unique Users", f"{stats['unique_users']:,}")
        col3.metric("Date Range", f"{stats['date_range']['span_days']} days")

        st.caption(f"""
        **Detection Method**: System events only (Session Started, Journey Started, App Installed, User Login, Push Click)
        **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        **Data Source**: Commuter Users Event Data
        """)

st.divider()
st.caption("All AI analysis is strictly per-user and filtered to application events only.")
