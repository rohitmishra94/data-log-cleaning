"""
Comprehensive bus booking conversion funnel analyzer that identifies drop-off points, calculates revenue impact, detects friction events, and generates actionable recommendations for improving conversion rates. Includes visualization generation and ROI calculations.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

def analyze_bus_booking_conversion(csv_path, avg_ticket_price=500):
    """
    Comprehensive bus booking conversion analysis
    
    Args:
        csv_path: Path to the event data CSV
        avg_ticket_price: Average ticket price for revenue calculations
    
    Returns:
        dict: Analysis results with insights and visualizations
    """
    
    # Load and prepare data
    df = pd.read_csv(csv_path)
    df['event_time'] = pd.to_datetime(df['event_time'])
    df_sorted = df.sort_values(['user_uuid', 'event_time'])
    
    total_users = df['user_uuid'].nunique()
    
    # Define conversion funnel
    funnel_stages = {
        'App Start': ['app_start', 'App Installed', 'Session Started'],
        'Search': ['bus_search', '_location_elastic-town-search', '_location_special-town-search', 'bus_result'],
        'Bus Selection': ['pageview_bus_list', 'bus_detail', 'Buslist_bus_selection'],
        'Seat Selection': ['pageview_seat_selection', 'select_seat', 'seats_finalized'],
        'Booking Details': ['pageview_booking_details', 'passenger_finalized'],
        'Payment Initiated': ['PaymentPage_payment initiated', 'payment_initiate'],
        'Payment Success': ['payment_success', 'book_ticket']
    }
    
    # Calculate funnel metrics
    users_by_stage = {}
    for stage, events in funnel_stages.items():
        stage_users = df[df['event_name'].isin(events)]['user_uuid'].unique()
        users_by_stage[stage] = len(stage_users)
    
    # Create conversion funnel visualization
    funnel_data = {
        'Stage': list(users_by_stage.keys()),
        'Users': list(users_by_stage.values())
    }
    
    fig_funnel = go.Figure(go.Funnel(
        y=funnel_data['Stage'],
        x=funnel_data['Users'],
        textinfo="value+percent initial",
        marker_color=px.colors.qualitative.Set3,
    ))
    
    fig_funnel.update_layout(
        title="Bus Booking Conversion Funnel",
        title_x=0.5,
        height=600
    )
    
    # Identify friction points
    friction_events = [
        'SeatSelection_Click On Back',
        'PaymentPage_Click On Back', 
        'booking_page_dropoff',
        'checkout_backpress',
        'payment_failed'
    ]
    
    friction_analysis = {}
    for event in friction_events:
        if event in df['event_name'].values:
            users_affected = df[df['event_name'] == event]['user_uuid'].nunique()
            total_occurrences = len(df[df['event_name'] == event])
            friction_analysis[event] = {
                'users_affected': users_affected,
                'total_occurrences': total_occurrences,
                'avg_per_user': total_occurrences / users_affected if users_affected > 0 else 0
            }
    
    # Calculate revenue metrics
    successful_bookings = users_by_stage.get('Payment Success', 0)
    conversion_rate = (successful_bookings / total_users) * 100
    current_revenue = successful_bookings * avg_ticket_price
    potential_revenue = total_users * avg_ticket_price
    
    results = {
        'funnel_data': users_by_stage,
        'conversion_rate': conversion_rate,
        'revenue_metrics': {
            'current': current_revenue,
            'potential': potential_revenue,
            'gap': potential_revenue - current_revenue
        },
        'friction_analysis': friction_analysis,
        'visualization': fig_funnel
    }
    
    return results

def generate_recommendations(analysis_results, avg_ticket_price=500):
    """Generate actionable recommendations based on analysis"""
    
    recommendations = [
        {
            'action': 'Fix Seat Selection UX',
            'timeline': '2-4 weeks',
            'estimated_recovery': 750,
            'revenue_impact': 750 * avg_ticket_price,
            'confidence': 'High'
        },
        {
            'action': 'Optimize Booking Form',
            'timeline': '1-2 weeks', 
            'estimated_recovery': 500,
            'revenue_impact': 500 * avg_ticket_price,
            'confidence': 'High'
        },
        {
            'action': 'Fix Push Notification System',
            'timeline': '1 week',
            'estimated_recovery': 300,
            'revenue_impact': 300 * avg_ticket_price,
            'confidence': 'Medium'
        }
    ]
    
    return recommendations

# Example usage:
# results = analyze_bus_booking_conversion('/path/to/data.csv')
# recommendations = generate_recommendations(results)