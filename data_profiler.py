"""
DataProfiler: Foundation layer for analyzing event data

This module provides comprehensive profiling of user event data including:
- Basic statistics and metrics
- Session detection and analysis
- Time pattern analysis
- Transition matrix construction (Markov chains)
- Event classification and categorization

Author: Adaptive Retention Engine Team
Date: 2024
"""

import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json


class DataProfiler:
    """
    Analyzes event data to extract patterns and statistics.

    Supports dual-mode analysis:
    - Application events (user behavior)
    - System events (infrastructure)
    """

    def __init__(self, session_gap_minutes=30):
        """
        Initialize DataProfiler.

        Args:
            session_gap_minutes (int): Time gap to consider as new session
        """
        self.session_gap_minutes = session_gap_minutes

    def profile(self, events_df, analyze_system_events=False):
        """
        Main profiling method.

        Args:
            events_df (pd.DataFrame): Event data with columns:
                - user_id (or user_uuid)
                - event_name
                - timestamp (or event_time)
                - category (application/system)
            analyze_system_events (bool): Whether to analyze system events

        Returns:
            dict: Comprehensive profile of the data
        """
        print("=" * 60)
        print("DATA PROFILER - Foundation Layer")
        print("=" * 60)

        # Standardize column names
        events_df = self._standardize_columns(events_df)

        # Separate categories
        app_df = events_df[events_df['category'] == 'application'].copy()
        sys_df = events_df[events_df['category'] == 'system'].copy()

        print(f"\n📊 Total Events: {len(events_df):,}")
        print(f"   └─ Application: {len(app_df):,} ({len(app_df)/len(events_df)*100:.1f}%)")
        print(f"   └─ System: {len(sys_df):,} ({len(sys_df)/len(events_df)*100:.1f}%)")

        # Always analyze application events (user behavior)
        # BUT use full dataset for session detection (includes system markers)
        print("\n🔍 Analyzing application events (user behavior)...")
        app_profile = self._profile_application_events(app_df, full_df=events_df)

        if analyze_system_events:
            print("\n🔧 Analyzing system events (infrastructure)...")
            sys_profile = self._profile_system_events(sys_df)

            print("\n🔗 Analyzing cross-category interactions...")
            interactions = self._analyze_interactions(app_df, sys_df)

            return {
                'application': app_profile,
                'system': sys_profile,
                'interactions': interactions
            }

        return app_profile

    def _standardize_columns(self, df):
        """Standardize column names across different data formats."""
        # Map common variations to standard names
        column_map = {
            'user_uuid': 'user_id',
            'event_time': 'timestamp'
        }

        df = df.rename(columns=column_map)

        # Ensure timestamp is datetime
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def _profile_application_events(self, app_df, full_df=None):
        """Analyze application events (user behavior)."""

        # Use full_df for session detection if provided (includes system markers)
        # But analyze only app_df for other metrics
        session_df = full_df if full_df is not None else app_df

        # Basic statistics
        print("\n  📈 Computing basic statistics...")
        basic_stats = self._compute_basic_stats(app_df)

        # Session analysis (use full dataset for detection)
        print("\n  🔄 Detecting and analyzing sessions...")
        sessions = self._analyze_sessions(app_df, session_df=session_df)

        # Time patterns
        print("\n  ⏰ Analyzing temporal patterns...")
        time_patterns = self._analyze_time_patterns(app_df)

        # Transition matrix
        print("\n  🔀 Building transition matrix...")
        transitions = self._build_transition_matrix(app_df)

        # Event classification
        print("\n  🏷️  Classifying events...")
        event_classes = self._classify_events(app_df)

        return {
            'basic_stats': basic_stats,
            'sessions': sessions,
            'time_patterns': time_patterns,
            'transitions': transitions,
            'event_classification': event_classes
        }

    def _profile_system_events(self, sys_df):
        """Analyze system events (infrastructure)."""

        if len(sys_df) == 0:
            return {}

        # Push notification analysis
        push_analysis = self._analyze_push_notifications(sys_df)

        # App lifecycle
        lifecycle = self._analyze_app_lifecycle(sys_df)

        return {
            'push_notifications': push_analysis,
            'app_lifecycle': lifecycle
        }

    def _analyze_interactions(self, app_df, sys_df):
        """Analyze how system events affect application behavior."""

        # This would analyze relationships between system and app events
        # For now, return placeholder
        return {
            'note': 'Cross-category analysis implemented in full version'
        }

    # ============================================================
    # BASIC STATISTICS
    # ============================================================

    def _compute_basic_stats(self, df):
        """Compute basic statistics about the data."""

        total_events = len(df)
        unique_events = df['event_name'].nunique()
        unique_users = df['user_id'].nunique()

        date_range = {
            'start': df['timestamp'].min(),
            'end': df['timestamp'].max(),
            'span_days': (df['timestamp'].max() - df['timestamp'].min()).days
        }

        events_per_user = df.groupby('user_id').size()

        return {
            'total_events': total_events,
            'unique_events': unique_events,
            'unique_users': unique_users,
            'date_range': date_range,
            'avg_events_per_user': events_per_user.mean(),
            'median_events_per_user': events_per_user.median(),
            'events_per_user_distribution': {
                'p25': events_per_user.quantile(0.25),
                'p50': events_per_user.quantile(0.50),
                'p75': events_per_user.quantile(0.75),
                'p90': events_per_user.quantile(0.90),
                'p95': events_per_user.quantile(0.95)
            }
        }

    # ============================================================
    # SESSION ANALYSIS
    # ============================================================

    def _analyze_sessions(self, df, session_df=None):
        """Detect and analyze user sessions using ONLY system event markers (TRUTH).

        Args:
            df: DataFrame with application events to analyze
            session_df: DataFrame with all events (app + system) for session detection
        """

        # Use session_df for detection if provided (includes system markers)
        # But analyze df for statistics (application events only)
        detection_df = session_df if session_df is not None else df

        # Sort by user and timestamp
        detection_df = detection_df.sort_values(['user_id', 'timestamp']).reset_index(drop=True)

        # TRUTH-BASED SESSION DETECTION - Use ONLY system event markers
        # These are explicit session/journey boundaries from the application itself
        session_markers = [
            'Session Started',   # Explicit session start
            'Journey Started',   # User starts a journey (search/book flow)
            'App Installed',     # First-time user session
            'User Login',        # Authentication creates session
            'Push Click'         # User re-enters app via notification
        ]

        detection_df['is_session_marker'] = detection_df['event_name'].isin(session_markers)

        # First event of each user is always a new session
        first_events = detection_df.groupby('user_id').head(1).index
        detection_df['new_session'] = False
        detection_df.loc[first_events, 'new_session'] = True
        detection_df.loc[detection_df['is_session_marker'], 'new_session'] = True

        # Assign session IDs
        detection_df['session_id'] = detection_df.groupby('user_id')['new_session'].cumsum()

        # Now map session IDs back to the application events DataFrame
        # Merge on user_id and timestamp to transfer session_id
        df_with_sessions = df.merge(
            detection_df[['user_id', 'timestamp', 'session_id']],
            on=['user_id', 'timestamp'],
            how='left'
        )

        # Fill any missing session_ids by forward-filling within each user
        df_with_sessions['session_id'] = df_with_sessions.groupby('user_id')['session_id'].ffill()
        df_with_sessions['session_id'] = df_with_sessions.groupby('user_id')['session_id'].bfill()

        # Session statistics (computed on application events)
        session_stats = self._compute_session_stats(df_with_sessions)

        # Add method info (from detection_df)
        session_stats['session_detection_method'] = 'system_events_only'
        session_stats['session_markers_used'] = detection_df['is_session_marker'].sum()
        session_stats['total_session_boundaries'] = detection_df['new_session'].sum()

        return session_stats

    def _compute_session_stats(self, df):
        """Compute statistics about sessions."""

        # Group by user and session
        sessions = df.groupby(['user_id', 'session_id'])

        # Session lengths (number of events)
        session_lengths = sessions.size()

        # Session durations (time span)
        session_durations = sessions['timestamp'].apply(
            lambda x: (x.max() - x.min()).total_seconds() / 60
        )

        # Bounce rate (single event sessions)
        bounce_sessions = (session_lengths == 1).sum()
        total_sessions = len(session_lengths)
        bounce_rate = bounce_sessions / total_sessions if total_sessions > 0 else 0

        # Common start and end events
        first_events = sessions.first()['event_name'].value_counts().head(10)
        last_events = sessions.last()['event_name'].value_counts().head(10)

        return {
            'total_sessions': total_sessions,
            'avg_session_length': session_lengths.mean(),
            'median_session_length': session_lengths.median(),
            'avg_session_duration_minutes': session_durations.mean(),
            'median_session_duration_minutes': session_durations.median(),
            'bounce_rate': bounce_rate,
            'session_length_distribution': {
                'p25': session_lengths.quantile(0.25),
                'p50': session_lengths.quantile(0.50),
                'p75': session_lengths.quantile(0.75),
                'p90': session_lengths.quantile(0.90),
                'p95': session_lengths.quantile(0.95)
            },
            'common_start_events': first_events.to_dict(),
            'common_end_events': last_events.to_dict()
        }

    # ============================================================
    # TIME PATTERN ANALYSIS
    # ============================================================

    def _analyze_time_patterns(self, df):
        """Analyze temporal patterns in event data."""

        # Extract time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_name'] = df['timestamp'].dt.day_name()
        df['date'] = df['timestamp'].dt.date

        # Hourly activity
        hourly_activity = df.groupby('hour').size().to_dict()
        peak_hours = df['hour'].value_counts().head(3).index.tolist()

        # Daily activity
        daily_activity = df.groupby('day_name').size().to_dict()

        # Events per day
        events_per_day = df.groupby('date').size()

        # User activity days
        active_days_per_user = df.groupby('user_id')['date'].nunique().mean()

        return {
            'hourly_activity': hourly_activity,
            'peak_hours': peak_hours,
            'daily_activity': daily_activity,
            'avg_events_per_day': events_per_day.mean(),
            'median_events_per_day': events_per_day.median(),
            'avg_active_days_per_user': active_days_per_user
        }

    # ============================================================
    # TRANSITION MATRIX
    # ============================================================

    def _build_transition_matrix(self, df):
        """Build Markov chain transition matrix."""

        # Sort by user and timestamp
        df = df.sort_values(['user_id', 'timestamp']).reset_index(drop=True)

        # Create event pairs (current -> next)
        transitions = []
        for user_id, user_df in df.groupby('user_id'):
            events = user_df['event_name'].tolist()
            for i in range(len(events) - 1):
                transitions.append((events[i], events[i+1]))

        # Count transitions
        transition_counts = Counter(transitions)
        event_counts = Counter([t[0] for t in transitions])

        # Calculate probabilities
        transition_probs = {}
        for (from_event, to_event), count in transition_counts.items():
            if from_event not in transition_probs:
                transition_probs[from_event] = {}
            prob = count / event_counts[from_event]
            transition_probs[from_event][to_event] = prob

        # Find high exit probability events
        high_exit_events = self._find_high_exit_events(df)

        # Most common transitions
        most_common = transition_counts.most_common(20)

        return {
            'transition_probabilities': transition_probs,
            'most_common_transitions': most_common,
            'high_exit_events': high_exit_events
        }

    def _find_high_exit_events(self, df):
        """Find events that often lead to session end."""

        # Sort by user and timestamp
        df = df.sort_values(['user_id', 'timestamp'])

        # Mark last event in each user's sequence
        last_events = df.groupby('user_id').last()['event_name'].value_counts()
        all_event_counts = df['event_name'].value_counts()

        # Calculate exit probability for each event
        exit_probs = {}
        for event in all_event_counts.index:
            if event in last_events:
                exit_prob = last_events[event] / all_event_counts[event]
                if exit_prob > 0.3:  # Only events with >30% exit rate
                    exit_probs[event] = exit_prob

        # Sort by exit probability
        sorted_exit = sorted(exit_probs.items(), key=lambda x: x[1], reverse=True)

        return sorted_exit[:10]  # Top 10 high-exit events

    # ============================================================
    # EVENT CLASSIFICATION
    # ============================================================

    def _classify_events(self, df):
        """Classify events by their intent/purpose."""

        event_names = df['event_name'].unique()

        classifications = {
            'authentication': [],
            'search': [],
            'selection': [],
            'transaction': [],
            'navigation': [],
            'onboarding': [],
            'api_calls': [],
            'other': []
        }

        for event in event_names:
            event_lower = event.lower()

            if '_auth_' in event_lower or 'login' in event_lower or 'otp' in event_lower:
                classifications['authentication'].append(event)
            elif 'search' in event_lower or 'filter' in event_lower:
                classifications['search'].append(event)
            elif 'select' in event_lower or 'choose' in event_lower or 'pick' in event_lower:
                classifications['selection'].append(event)
            elif 'payment' in event_lower or 'book' in event_lower or 'ticket' in event_lower:
                classifications['transaction'].append(event)
            elif 'pageview' in event_lower or 'click' in event_lower or 'back' in event_lower:
                classifications['navigation'].append(event)
            elif 'onboarding' in event_lower:
                classifications['onboarding'].append(event)
            elif event.startswith('_'):
                classifications['api_calls'].append(event)
            else:
                classifications['other'].append(event)

        # Count events in each category
        classification_counts = {}
        for category, events in classifications.items():
            if events:
                count = df[df['event_name'].isin(events)].shape[0]
                classification_counts[category] = {
                    'event_count': count,
                    'unique_events': len(events),
                    'examples': events[:5]  # Show first 5 examples
                }

        return classification_counts

    # ============================================================
    # SYSTEM EVENT ANALYSIS
    # ============================================================

    def _analyze_push_notifications(self, sys_df):
        """Analyze push notification effectiveness."""

        push_events = sys_df[sys_df['event_name'].str.contains('Push', na=False)]

        if len(push_events) == 0:
            return {}

        push_counts = push_events['event_name'].value_counts().to_dict()

        # Calculate rates (if we have the data)
        total_sent = push_counts.get('Push Sent', 0)

        if total_sent > 0:
            delivered = push_counts.get('Push Delivered', 0)
            clicked = push_counts.get('Push Click', 0)
            failed = push_counts.get('Push Failure', 0)

            return {
                'total_sent': total_sent,
                'delivery_rate': delivered / total_sent if total_sent > 0 else 0,
                'click_rate': clicked / delivered if delivered > 0 else 0,
                'failure_rate': failed / total_sent if total_sent > 0 else 0,
                'event_breakdown': push_counts
            }

        return {'event_breakdown': push_counts}

    def _analyze_app_lifecycle(self, sys_df):
        """Analyze app installation and usage lifecycle."""

        installs = (sys_df['event_name'] == 'App Installed').sum()
        uninstalls = (sys_df['event_name'] == 'App Uninstalled').sum()

        return {
            'total_installs': installs,
            'total_uninstalls': uninstalls,
            'churn_rate': uninstalls / installs if installs > 0 else 0
        }

    # ============================================================
    # REPORTING
    # ============================================================

    def print_summary(self, profile):
        """Print a human-readable summary of the profile."""

        print("\n" + "=" * 60)
        print("PROFILE SUMMARY")
        print("=" * 60)

        stats = profile['basic_stats']
        print(f"\n📊 Basic Statistics:")
        print(f"   Total Events: {stats['total_events']:,}")
        print(f"   Unique Events: {stats['unique_events']}")
        print(f"   Unique Users: {stats['unique_users']:,}")
        print(f"   Date Range: {stats['date_range']['span_days']} days")
        print(f"   Avg Events/User: {stats['avg_events_per_user']:.1f}")

        sessions = profile['sessions']
        print(f"\n🔄 Sessions:")
        print(f"   Detection Method: {sessions.get('session_detection_method', 'N/A').upper()}")
        print(f"   Total Sessions: {sessions['total_sessions']:,}")
        if 'session_markers_used' in sessions:
            markers = sessions['session_markers_used']
            total = sessions['total_session_boundaries']
            print(f"   System Markers Used: {markers:,}")
            print(f"   Total Boundaries: {total:,}")
        print(f"   Avg Length: {sessions['avg_session_length']:.1f} events")
        print(f"   Avg Duration: {sessions['avg_session_duration_minutes']:.1f} minutes")
        print(f"   Bounce Rate: {sessions['bounce_rate']:.1%}")

        time = profile['time_patterns']
        print(f"\n⏰ Time Patterns:")
        print(f"   Peak Hours: {time['peak_hours']}")
        print(f"   Avg Events/Day: {time['avg_events_per_day']:.0f}")

        trans = profile['transitions']
        print(f"\n🔀 High Exit Events (Top 5):")
        for event, prob in trans['high_exit_events'][:5]:
            print(f"   {event}: {prob:.1%} exit rate")

        classes = profile['event_classification']
        print(f"\n🏷️  Event Classification:")
        for category, data in classes.items():
            print(f"   {category.title()}: {data['event_count']:,} events ({data['unique_events']} types)")

        print("\n" + "=" * 60)

    def save_report(self, profile, filename='data_profile_report.json'):
        """Save profile to JSON file."""

        # Convert non-serializable objects
        def convert(obj):
            if isinstance(obj, (pd.Timestamp, datetime)):
                return obj.isoformat()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Recursively convert all values
        def deep_convert(item):
            if isinstance(item, dict):
                return {k: deep_convert(v) for k, v in item.items()}
            elif isinstance(item, list):
                return [deep_convert(v) for v in item]
            elif isinstance(item, tuple):
                return tuple(deep_convert(v) for v in item)
            else:
                return convert(item)

        profile_clean = deep_convert(profile)

        with open(filename, 'w') as f:
            json.dump(profile_clean, f, indent=2)

        print(f"\n💾 Profile saved to: {filename}")


if __name__ == "__main__":
    print("DataProfiler module loaded successfully!")
    print("Use: profiler = DataProfiler() to create an instance")
