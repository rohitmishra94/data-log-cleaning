"""
Quick funnel visualization generator for instant conversion analysis. Creates funnel and drop-off charts with minimal setup. Perfect for rapid analysis and stakeholder presentations.
"""

#!/usr/bin/env python3
"""
Quick Funnel Visualization Generator
===================================
Creates instant conversion funnel visualizations from event data.
Useful for quick analysis and presentations.

Usage: python quick_funnel_viz.py <path_to_csv>
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

def create_quick_funnel(file_path, output_path="/tmp/quick_funnel.html"):
    """Generate quick funnel visualization"""
    
    # Load data
    df = pd.read_csv(file_path)
    df['event_time'] = pd.to_datetime(df['event_time'], errors='coerce')
    
    total_users = df['user_uuid'].nunique()
    
    # Define common funnel events (customize as needed)
    funnel_stages = {
        'Total Users': ['.*'],  # All users
        'App Opened': ['Session Started', '_user', 'app_start'],
        'Searched': ['search', 'bus_search', '_location'],
        'Viewed Results': ['result', 'list', 'bus_result'],
        'Selected Item': ['select', 'seat', 'item'],
        'Payment Started': ['payment', 'checkout', 'pay'],
        'Completed': ['success', 'complete', 'confirm']
    }
    
    # Calculate funnel metrics
    funnel_data = []
    
    for stage, keywords in funnel_stages.items():
        if stage == 'Total Users':
            users = total_users
        else:
            # Find events matching keywords
            matching_events = df[df['event_name'].str.contains('|'.join(keywords), case=False, na=False)]
            users = matching_events['user_uuid'].nunique()
        
        funnel_data.append({
            'stage': stage,
            'users': users,
            'conversion': (users / total_users * 100) if total_users > 0 else 0
        })
    
    # Create visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Conversion Funnel", "Drop-off Analysis"),
        specs=[[{"type": "funnel"}], [{"type": "bar"}]]
    )
    
    # Funnel chart
    fig.add_trace(
        go.Funnel(
            y=[d['stage'] for d in funnel_data],
            x=[d['users'] for d in funnel_data],
            textinfo="value+percent initial",
            textposition="inside",
            name="Users"
        ),
        row=1, col=1
    )
    
    # Drop-off chart
    drop_offs = []
    for i in range(1, len(funnel_data)):
        drop_off = funnel_data[i-1]['users'] - funnel_data[i]['users']
        drop_offs.append(drop_off)
    
    fig.add_trace(
        go.Bar(
            x=[d['stage'] for d in funnel_data[1:]],
            y=drop_offs,
            name="Users Dropped",
            marker_color='red'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"Quick Funnel Analysis - {total_users:,} Users",
        height=800,
        showlegend=False
    )
    
    fig.write_html(output_path)
    
    # Print summary
    print(f"📊 QUICK FUNNEL ANALYSIS")
    print(f"Total Users: {total_users:,}")
    print(f"Conversion Rate: {funnel_data[-1]['conversion']:.1f}%")
    print(f"Visualization saved: {output_path}")
    
    return fig

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_funnel_viz.py <path_to_csv>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    create_quick_funnel(file_path)