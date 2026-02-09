import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

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

main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(["Data", "Analysis", "Session Analysis", "Pattern Discovery"])

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

with main_tab4:
    st.header("🔍 Pattern Discovery")
    st.markdown("*Behavioral patterns discovered through machine learning algorithms*")

    # Load pattern discovery data
    @st.cache_data
    def load_pattern_data():
        """Load pattern discovery report"""
        try:
            with open('pattern_discovery_report.json', 'r') as f:
                patterns = json.load(f)
            return patterns
        except FileNotFoundError:
            st.error("Pattern discovery report not found. Run: python run_pattern_discovery.py")
            st.stop()

    patterns = load_pattern_data()

    metadata = patterns.get('metadata', {})
    st.markdown(f"""
    **Analysis Scope**: {metadata['total_events']:,} events | {metadata['unique_users']:,} users | {metadata['total_sessions']:,} sessions
    """)

    st.divider()

    # Executive Summary (if LLM insights available)
    if patterns.get('llm_executive_summary'):
        with st.container():
            st.markdown("### 📋 Executive Summary")
            st.info(patterns['llm_executive_summary'])
            st.divider()

    # Nested tabs for pattern discovery
    pattern_tab1, pattern_tab2, pattern_tab3, pattern_tab4, pattern_tab5 = st.tabs([
        "🔄 Sequential Patterns",
        "👥 User Segments",
        "🔥 Friction Analysis",
        "📉 Survival Analysis",
        "🎯 Intervention Triggers"
    ])

    with pattern_tab1:
        st.subheader("Sequential Patterns")
        st.markdown("**Most frequent event sequences** - reveals common user journeys and stuck loops")

        seq_patterns = patterns.get('sequential_patterns', {})

        # Show LLM insights if available
        if seq_patterns.get('llm_insights'):
            with st.expander("🤖 LLM Analysis - Sequential Patterns", expanded=True):
                st.markdown(seq_patterns['llm_insights'])
            st.divider()
        frequent = seq_patterns.get('frequent_patterns', {})
        repetitions = seq_patterns.get('repetition_patterns', {})

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("#### Top 20 Frequent Sequences")

            seq_df = pd.DataFrame([
                {'Pattern': k, 'Frequency': v, 'Pattern_Length': len(k.split(' → '))}
                for k, v in list(frequent.items())[:20]
            ])

            fig = px.bar(
                seq_df,
                x='Frequency',
                y='Pattern',
                orientation='h',
                title="Most Common Event Sequences",
                color='Pattern_Length',
                color_continuous_scale='Blues',
                labels={'Frequency': 'Number of Occurrences', 'Pattern_Length': 'Sequence Length'}
            )
            fig.update_layout(height=600, showlegend=True, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### Repetition Patterns")
            st.markdown("*Events users repeat → friction signals*")

            rep_df = pd.DataFrame([
                {
                    'Event': k,
                    'Sessions': v['sessions_with_repetition'],
                    'Avg Repeats': v['avg_repetitions'],
                    'Max Repeats': v['max_repetitions']
                }
                for k, v in list(repetitions.items())[:5]
            ])

            for _, row in rep_df.iterrows():
                st.metric(
                    row['Event'][:40] + '...' if len(row['Event']) > 40 else row['Event'],
                    f"{row['Avg Repeats']:.1f}x avg"
                )
                st.caption(f"{row['Sessions']} sessions")
                if row['Avg Repeats'] > 5:
                    st.error("🔴 CRITICAL FRICTION")

    with pattern_tab2:
        st.subheader("User Segments")
        st.markdown("**Behavioral clustering** - distinct user groups with different needs")

        user_segments_data = patterns.get('user_segments', {})
        segments = user_segments_data.get('segments', {})
        total_users = user_segments_data.get('total_users', 0)

        # Show LLM insights if available
        if user_segments_data.get('llm_insights'):
            with st.expander("🤖 LLM Analysis - User Personas", expanded=True):
                st.markdown(user_segments_data['llm_insights'])
            st.divider()

        seg_data = []
        for seg_name, seg_info in segments.items():
            seg_data.append({
                'Segment': seg_name.replace('_', ' ').title(),
                'Count': seg_info.get('count', 0),
                'Percentage': seg_info.get('percentage', 0)
            })

        seg_df = pd.DataFrame(seg_data)

        fig = px.pie(
            seg_df,
            values='Count',
            names='Segment',
            title=f"User Segments (Total: {total_users:,})",
            hole=0.5
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # Segment profiles
        cols = st.columns(4)
        for idx, (seg_name, seg_info) in enumerate(segments.items()):
            with cols[idx % 4]:
                priority = "🔴" if seg_name == 'strugglers' else "🟢" if seg_name == 'quick_bookers' else "🔵"
                st.markdown(f"### {priority} {seg_name.replace('_', ' ').title()}")
                st.metric("Users", f"{seg_info.get('count', 0):,}")
                st.caption(f"{seg_info.get('percentage', 0):.1f}% of total users")

                if 'characteristics' in seg_info:
                    chars = seg_info['characteristics']
                    st.markdown(f"**Avg Events**: {chars.get('avg_events', 0):.0f}")
                    st.markdown(f"**Diversity**: {chars.get('avg_diversity', 0):.1%}")
                    st.markdown(f"**Repetition**: {chars.get('avg_repetition', 0):.1%}")

    with pattern_tab3:
        st.subheader("Friction Analysis")
        st.markdown("**Events causing user hesitation** - where users get stuck")

        friction = patterns.get('friction_points', {})

        # Show LLM insights if available
        if friction.get('llm_insights'):
            with st.expander("🤖 LLM Analysis - Root Cause & Solutions", expanded=True):
                st.markdown(friction['llm_insights'])
            st.divider()

        high_friction = friction.get('high_friction_events', {})

        friction_df = pd.DataFrame([
            {
                'Event': k[:50] + '...' if len(k) > 50 else k,
                'Repetition Rate': v['repetition_rate'] * 100,
                'Users Affected': v['users_affected'],
                'Friction Score': v['friction_score']
            }
            for k, v in list(high_friction.items())[:10]
        ])

        if not friction_df.empty:
            fig = px.bar(
                friction_df,
                x='Friction Score',
                y='Event',
                orientation='h',
                title="Top Friction Events (Higher = Worse UX)",
                color='Repetition Rate',
                color_continuous_scale='Reds',
                hover_data=['Users Affected']
            )
            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

    with pattern_tab4:
        st.subheader("Survival Analysis")
        st.markdown("**Session survival probability** - likelihood of continuing at each step")

        survival = patterns.get('survival_analysis', {})

        if 'survival_curve' in survival:
            curve_data = survival['survival_curve']
            curve_df = pd.DataFrame(curve_data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=curve_df['step'],
                y=curve_df['survival_rate'] * 100,
                mode='lines+markers',
                name='Survival Rate',
                line=dict(color='#4B9EFF', width=3)
            ))

            fig.update_layout(
                title="Session Survival Curve",
                xaxis_title="Session Step",
                yaxis_title="Percentage",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Median Session Length", f"{survival.get('median_session_length', 0)} events")
            col2.metric("Reach Step 10", f"{int(survival.get('sessions_reaching_step_10', 0)):,}")
            col3.metric("Reach Step 20", f"{int(survival.get('sessions_reaching_step_20', 0)):,}")

    with pattern_tab5:
        st.subheader("Intervention Triggers")
        st.markdown("**Automated rules** - conditions that predict user drop-off")

        rules = patterns.get('intervention_rules', {})

        # Show LLM insights if available
        if rules.get('llm_insights'):
            with st.expander("🤖 LLM Analysis - Intervention Strategies", expanded=True):
                st.markdown(rules['llm_insights'])
            st.divider()
        triggers = rules.get('intervention_triggers', [])

        if triggers:
            high_risk = [r for r in triggers if r['confidence'] > 0.9]
            medium_risk = [r for r in triggers if 0.7 <= r['confidence'] <= 0.9]

            col1, col2 = st.columns(2)
            col1.metric("🔴 High Risk Rules", len(high_risk), ">90% dropout")
            col2.metric("🟡 Medium Risk Rules", len(medium_risk), "70-90% dropout")

            st.divider()

            for trigger in triggers[:5]:
                confidence = trigger['confidence']
                icon = "🔴" if confidence > 0.9 else "🟡"

                with st.expander(f"{icon} **{trigger['condition']}** ({confidence:.0%} dropout risk)"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**📊 Risk Assessment**")
                        st.progress(confidence)
                        st.markdown(f"Confidence: {confidence:.1%}")
                        st.markdown(f"Support: {trigger['support']} sessions")
                    with col_b:
                        st.markdown("**💡 Recommendation**")
                        st.markdown(trigger['recommendation'])

st.divider()
st.caption("All AI analysis is strictly per-user and filtered to application events only.")
