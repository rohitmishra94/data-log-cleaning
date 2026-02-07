"""
Comprehensive revenue and retention analysis for mobile app event data. Analyzes conversion funnels, identifies drop-off points, calculates revenue opportunities, and provides actionable recommendations. Creates visualizations and executive summary.
"""

#!/usr/bin/env python3
"""
Complete Event Data Revenue Analysis Script
===========================================
Analyzes mobile app event data to identify revenue optimization opportunities.
Specifically designed for transport/booking apps but adaptable to other domains.

Features:
- Event classification (terminal, behavioral, system, onboarding)
- Conversion funnel analysis with drop-off identification
- Revenue impact calculations
- User journey pattern analysis
- Actionable recommendations with ROI estimates
- Interactive visualizations (Plotly)

Usage: python revenue_analysis.py <path_to_csv>
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import warnings
warnings.filterwarnings('ignore')

class EventRevenueAnalyzer:
    def __init__(self, file_path, avg_ticket_value=500):
        """Initialize analyzer with event data"""
        self.file_path = file_path
        self.avg_ticket_value = avg_ticket_value
        self.df = None
        self.funnel_data = {}
        self.insights = {}
        
    def load_data(self):
        """Load and prepare event data"""
        print("Loading event data...")
        self.df = pd.read_csv(self.file_path)
        
        # Parse timestamps
        self.df['event_time'] = pd.to_datetime(self.df['event_time'], format='%Y-%m-%d %H:%M:%S.%f %z', errors='coerce')
        if self.df['event_time'].isna().sum() > 0:
            print("Warning: Some timestamps couldn't be parsed")
        
        print(f"✓ Loaded {len(self.df):,} events from {self.df['user_uuid'].nunique():,} users")
        return self
        
    def classify_events(self):
        """Classify events into categories for funnel analysis"""
        print("\nClassifying events...")
        
        # Define keyword patterns
        terminal_keywords = ['payment', 'book', 'success', 'complete', 'confirm', 'purchase', 'ticket']
        system_keywords = ['failure', 'error', 'crash', 'background', 'timeout', 'exception']
        
        event_freq = self.df['event_name'].value_counts()
        event_pct = (event_freq / len(self.df) * 100)
        
        # Classify events
        self.terminal_events = []
        self.behavioral_events = []
        
        for event in event_freq.index:
            event_lower = event.lower()
            is_terminal = any(keyword in event_lower for keyword in terminal_keywords)
            is_rare = event_pct[event] < 1.0  # Low frequency events might be terminal
            
            if is_terminal or (is_rare and 'pay' in event_lower):
                self.terminal_events.append(event)
            else:
                self.behavioral_events.append(event)
        
        print(f"✓ Found {len(self.terminal_events)} terminal events, {len(self.behavioral_events)} behavioral events")
        return self
        
    def analyze_conversion_funnel(self):
        """Build and analyze conversion funnel"""
        print("\nAnalyzing conversion funnel...")
        
        # Define funnel stages (customize based on your app)
        self.funnel_events = {
            'App Open': ['Session Started', '_user'],
            'Search': ['bus_search', '_bus-search_user-bus-search', '_location_elastic-town-search'],
            'Browse Results': ['bus_result', 'pageview_bus_list', 'Buslist_bus_selection'],
            'Select Item': ['select_seat', 'pageview_seat_selection'],
            'Payment Started': ['payment_initiate', 'PaymentPage_payment initiated'],
            'Payment Success': ['payment_success']
        }
        
        total_users = self.df['user_uuid'].nunique()
        
        # Calculate users at each stage
        for stage, events in self.funnel_events.items():
            users_in_stage = self.df[self.df['event_name'].isin(events)]['user_uuid'].nunique()
            conversion_rate = (users_in_stage / total_users) * 100
            
            self.funnel_data[stage] = {
                'users': users_in_stage,
                'conversion_rate': conversion_rate,
                'events': events
            }
        
        print("✓ Funnel analysis complete")
        return self
        
    def calculate_revenue_impact(self):
        """Calculate revenue opportunities"""
        print("\nCalculating revenue impact...")
        
        payment_success_users = self.funnel_data.get('Payment Success', {}).get('users', 0)
        current_revenue = payment_success_users * self.avg_ticket_value
        
        self.revenue_analysis = {
            'current_revenue': current_revenue,
            'current_conversion': payment_success_users / self.df['user_uuid'].nunique() * 100,
            'opportunities': {}
        }
        
        # Calculate opportunity at each stage
        for stage, data in self.funnel_data.items():
            if stage != 'Payment Success':
                potential_users = data['users']
                revenue_opportunity = (potential_users - payment_success_users) * self.avg_ticket_value
                if revenue_opportunity > 0:
                    self.revenue_analysis['opportunities'][stage] = {
                        'users': potential_users - payment_success_users,
                        'revenue': revenue_opportunity
                    }
        
        print("✓ Revenue analysis complete")
        return self
        
    def analyze_user_patterns(self):
        """Analyze user journey patterns"""
        print("\nAnalyzing user patterns...")
        
        # User journey analysis
        journey_analysis = self.df.groupby('user_uuid').agg({
            'event_name': 'count',
            'event_time': ['min', 'max']
        }).reset_index()
        
        journey_analysis.columns = ['user_uuid', 'total_events', 'first_time', 'last_time']
        journey_analysis['duration_minutes'] = (journey_analysis['last_time'] - journey_analysis['first_time']).dt.total_seconds() / 60
        
        # Classify outcomes
        def classify_outcome(user_id):
            user_events = self.df[self.df['user_uuid'] == user_id]['event_name'].tolist()
            if any(event in user_events for event in self.funnel_events['Payment Success']):
                return 'converted'
            elif any(event in user_events for event in self.funnel_events['Payment Started']):
                return 'payment_attempted'
            elif any(event in user_events for event in self.funnel_events['Select Item']):
                return 'item_selected'
            elif any(event in user_events for event in self.funnel_events['Search']):
                return 'searched_only'
            else:
                return 'browsed_only'
        
        journey_analysis['outcome'] = journey_analysis['user_uuid'].apply(classify_outcome)
        
        self.user_patterns = {
            'outcome_distribution': journey_analysis['outcome'].value_counts().to_dict(),
            'avg_events_per_user': journey_analysis['total_events'].mean(),
            'avg_duration_minutes': journey_analysis['duration_minutes'].mean()
        }
        
        print("✓ User pattern analysis complete")
        return self
        
    def create_visualizations(self, output_dir="/tmp"):
        """Create interactive visualizations"""
        print(f"\nCreating visualizations in {output_dir}...")
        
        # 1. Conversion Funnel
        stages = list(self.funnel_data.keys())
        users = [self.funnel_data[stage]['users'] for stage in stages]
        
        fig_funnel = go.Figure(go.Funnel(
            y=stages,
            x=users,
            textinfo="value+percent initial"
        ))
        fig_funnel.update_layout(title="Conversion Funnel Analysis")
        fig_funnel.write_html(f"{output_dir}/conversion_funnel.html")
        
        # 2. Revenue Opportunities
        opp_stages = list(self.revenue_analysis['opportunities'].keys())
        opp_revenues = [self.revenue_analysis['opportunities'][stage]['revenue'] for stage in opp_stages]
        
        fig_revenue = go.Figure(go.Bar(x=opp_stages, y=opp_revenues))
        fig_revenue.update_layout(
            title="Revenue Opportunities by Stage",
            yaxis_title="Revenue Opportunity (₹)"
        )
        fig_revenue.write_html(f"{output_dir}/revenue_opportunities.html")
        
        # 3. User Journey Outcomes
        outcomes = list(self.user_patterns['outcome_distribution'].keys())
        counts = list(self.user_patterns['outcome_distribution'].values())
        
        fig_outcomes = go.Figure(go.Pie(labels=outcomes, values=counts))
        fig_outcomes.update_layout(title="User Journey Outcomes")
        fig_outcomes.write_html(f"{output_dir}/user_outcomes.html")
        
        print("✓ Visualizations saved")
        return self
        
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print("\nGenerating recommendations...")
        
        # Calculate biggest drop-off points
        stages = list(self.funnel_data.keys())
        drop_offs = []
        
        for i in range(1, len(stages)):
            prev_users = self.funnel_data[stages[i-1]]['users']
            curr_users = self.funnel_data[stages[i]]['users']
            drop_off = prev_users - curr_users
            drop_off_rate = (drop_off / prev_users) * 100 if prev_users > 0 else 0
            
            drop_offs.append({
                'transition': f"{stages[i-1]} → {stages[i]}",
                'users_lost': drop_off,
                'drop_off_rate': drop_off_rate,
                'revenue_lost': drop_off * self.avg_ticket_value
            })
        
        # Sort by revenue impact
        drop_offs.sort(key=lambda x: x['revenue_lost'], reverse=True)
        
        self.recommendations = {
            'top_priorities': drop_offs[:3],
            'total_opportunity': sum([opp['revenue'] for opp in self.revenue_analysis['opportunities'].values()]),
            'current_conversion': self.revenue_analysis['current_conversion']
        }
        
        print("✓ Recommendations generated")
        return self
        
    def print_executive_summary(self):
        """Print comprehensive analysis summary"""
        print("\n" + "="*60)
        print("EXECUTIVE SUMMARY")
        print("="*60)
        
        total_users = self.df['user_uuid'].nunique()
        current_conv = self.revenue_analysis['current_conversion']
        total_opp = self.recommendations['total_opportunity']
        
        print(f"📊 CURRENT PERFORMANCE:")
        print(f"   • Total Users Analyzed: {total_users:,}")
        print(f"   • Current Conversion Rate: {current_conv:.1f}%")
        print(f"   • Current Revenue: ₹{self.revenue_analysis['current_revenue']:,}")
        
        print(f"\n💰 REVENUE OPPORTUNITY:")
        print(f"   • Total Opportunity: ₹{total_opp:,}")
        print(f"   • Potential Revenue Increase: {(total_opp/self.revenue_analysis['current_revenue']*100):.0f}%")
        
        print(f"\n🎯 TOP PRIORITIES:")
        for i, priority in enumerate(self.recommendations['top_priorities'][:3], 1):
            print(f"   {i}. {priority['transition']}")
            print(f"      • {priority['users_lost']:,} users lost ({priority['drop_off_rate']:.1f}% drop-off)")
            print(f"      • ₹{priority['revenue_lost']:,} revenue opportunity")
        
        print(f"\n📈 USER PATTERNS:")
        print(f"   • Avg Events per User: {self.user_patterns['avg_events_per_user']:.1f}")
        print(f"   • Avg Session Duration: {self.user_patterns['avg_duration_minutes']:.0f} minutes")
        
        outcome_dist = self.user_patterns['outcome_distribution']
        for outcome, count in outcome_dist.items():
            pct = count / total_users * 100
            print(f"   • {outcome}: {count:,} users ({pct:.1f}%)")
        
        return self
        
    def run_complete_analysis(self):
        """Run full analysis pipeline"""
        print("🚀 Starting Complete Event Revenue Analysis")
        print("="*60)
        
        (self.load_data()
         .classify_events() 
         .analyze_conversion_funnel()
         .calculate_revenue_impact()
         .analyze_user_patterns()
         .create_visualizations()
         .generate_recommendations()
         .print_executive_summary())
        
        print(f"\n✅ Analysis Complete!")
        print(f"📁 Visualizations saved to /tmp/")
        print(f"📊 Check conversion_funnel.html, revenue_opportunities.html, user_outcomes.html")
        
        return self

# Main execution
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python revenue_analysis.py <path_to_csv>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    analyzer = EventRevenueAnalyzer(file_path)
    analyzer.run_complete_analysis()