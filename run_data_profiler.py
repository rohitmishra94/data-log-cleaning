"""
Run DataProfiler on Commuter Users Event Data

This script loads the actual event data and runs comprehensive profiling.
"""

import pandas as pd
from data_profiler import DataProfiler

def main():
    print("Loading Commuter Users Event Data...")
    print("-" * 60)

    # Load the data
    df = pd.read_csv('Commuter Users Event data.csv')

    print(f"✓ Loaded {len(df):,} events")
    print(f"✓ Columns: {list(df.columns)}")
    print(f"✓ Date range: {df['event_time'].min()} to {df['event_time'].max()}")

    # Create profiler
    profiler = DataProfiler(session_gap_minutes=30)

    # Run profiling (application events only)
    print("\n" + "=" * 60)
    print("PROFILING APPLICATION EVENTS ONLY")
    print("=" * 60)
    profile = profiler.profile(df, analyze_system_events=False)

    # Print summary
    profiler.print_summary(profile)

    # Save report
    profiler.save_report(profile, 'data_profile_report.json')

    print("\n" + "=" * 60)
    print("PROFILING WITH SYSTEM EVENTS")
    print("=" * 60)

    # Run full profiling (with system events)
    full_profile = profiler.profile(df, analyze_system_events=True)

    # Print system event analysis
    if 'system' in full_profile and full_profile['system']:
        print("\n📱 System Events Analysis:")

        if 'push_notifications' in full_profile['system']:
            push = full_profile['system']['push_notifications']
            if 'total_sent' in push:
                print(f"\n  Push Notifications:")
                print(f"    Sent: {push['total_sent']:,}")
                print(f"    Delivery Rate: {push['delivery_rate']:.1%}")
                print(f"    Click Rate: {push['click_rate']:.1%}")
                print(f"    Failure Rate: {push['failure_rate']:.1%}")

        if 'app_lifecycle' in full_profile['system']:
            lifecycle = full_profile['system']['app_lifecycle']
            print(f"\n  App Lifecycle:")
            print(f"    Installs: {lifecycle['total_installs']:,}")
            print(f"    Uninstalls: {lifecycle['total_uninstalls']:,}")
            print(f"    Churn Rate: {lifecycle['churn_rate']:.1%}")

    # Save full report
    profiler.save_report(full_profile, 'data_profile_full_report.json')

    print("\n✅ Profiling Complete!")
    print("\nGenerated Files:")
    print("  1. data_profile_report.json (application events only)")
    print("  2. data_profile_full_report.json (all events)")

    # Show some interesting insights
    print("\n" + "=" * 60)
    print("KEY INSIGHTS")
    print("=" * 60)

    app_stats = profile['basic_stats']
    sessions = profile['sessions']
    trans = profile['transitions']

    print(f"\n💡 User Engagement:")
    print(f"   Average user generates {app_stats['avg_events_per_user']:.0f} application events")
    print(f"   Median user generates {app_stats['median_events_per_user']:.0f} events")

    print(f"\n💡 Session Quality:")
    print(f"   {sessions['bounce_rate']:.0%} of sessions are single-event (bounces)")
    print(f"   Average session has {sessions['avg_session_length']:.0f} events")
    print(f"   Average session lasts {sessions['avg_session_duration_minutes']:.1f} minutes")

    print(f"\n💡 Drop-off Points:")
    print("   Top events where users exit:")
    for i, (event, prob) in enumerate(trans['high_exit_events'][:3], 1):
        print(f"   {i}. {event}: {prob:.0%} of users exit here")

    print(f"\n💡 Popular Starting Points:")
    start_events = sessions['common_start_events']
    for event, count in list(start_events.items())[:3]:
        print(f"   {event}: {count:,} sessions")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
