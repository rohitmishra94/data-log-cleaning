"""
Advanced user journey pattern discovery tool that analyzes event sequences to identify success/failure patterns, friction indicators, terminal events, and common user paths. Includes sequence mining algorithms to find frequent patterns and behavioral insights for conversion optimization.
"""

import pandas as pd
from collections import Counter, defaultdict
import numpy as np

def discover_user_journey_patterns(csv_path):
    """
    Advanced pattern discovery for user journey analysis
    
    Identifies:
    - Common user sequences
    - Success vs failure patterns  
    - Friction indicators
    - Terminal event analysis
    
    Args:
        csv_path: Path to event data CSV
        
    Returns:
        dict: Comprehensive pattern analysis results
    """
    
    # Load data
    df = pd.read_csv(csv_path)
    df['event_time'] = pd.to_datetime(df['event_time'])
    df_sorted = df.sort_values(['user_uuid', 'event_time'])
    
    # Create user journey sequences
    user_sequences = {}
    for user, group in df_sorted.groupby('user_uuid'):
        sequence = group['event_name'].tolist()
        user_sequences[user] = sequence
    
    # Segment users by outcome
    successful_users = set(df[df['event_name'] == 'payment_success']['user_uuid'].unique())
    failed_payment_users = set(df[df['event_name'] == 'payment_failed']['user_uuid'].unique())
    drop_off_users = set(df['user_uuid'].unique()) - successful_users - failed_payment_users
    
    def analyze_sequences(user_set, label):
        """Analyze patterns for a specific user segment"""
        sequences = {u: user_sequences[u] for u in user_set if u in user_sequences}
        
        if not sequences:
            return {}
            
        # Starting patterns (first 3 events)
        start_sequences = []
        end_sequences = []
        sequence_lengths = []
        
        for user, sequence in sequences.items():
            if len(sequence) >= 3:
                start_sequences.append(' → '.join(sequence[:3]))
                end_sequences.append(' → '.join(sequence[-3:]))
            sequence_lengths.append(len(sequence))
        
        start_patterns = Counter(start_sequences).most_common(5)
        end_patterns = Counter(end_sequences).most_common(5)
        
        return {
            'count': len(sequences),
            'avg_sequence_length': np.mean(sequence_lengths),
            'median_sequence_length': np.median(sequence_lengths),
            'common_starts': start_patterns,
            'common_ends': end_patterns
        }
    
    # Analyze each segment
    successful_analysis = analyze_sequences(successful_users, 'Successful')
    failed_analysis = analyze_sequences(failed_payment_users, 'Failed')  
    dropoff_analysis = analyze_sequences(drop_off_users, 'Dropoff')
    
    # Find friction indicators
    friction_events = [
        'SeatSelection_Click On Back',
        'PaymentPage_Click On Back',
        'booking_page_dropoff', 
        'checkout_backpress',
        'payment_failed',
        'error',
        'Onboarding_backpressed'
    ]
    
    friction_impact = {}
    for event in friction_events:
        if event in df['event_name'].values:
            users_with_friction = set(df[df['event_name'] == event]['user_uuid'].unique())
            success_rate = len(users_with_friction & successful_users) / len(users_with_friction) if users_with_friction else 0
            
            friction_impact[event] = {
                'users_affected': len(users_with_friction),
                'total_occurrences': len(df[df['event_name'] == event]),
                'success_rate': success_rate,
                'avg_per_user': len(df[df['event_name'] == event]) / len(users_with_friction) if users_with_friction else 0
            }
    
    # Terminal event analysis
    user_last_events = df_sorted.groupby('user_uuid')['event_name'].last()
    terminal_events = user_last_events.value_counts().head(10)
    
    # Sequence mining: Find common subsequences
    def find_common_subsequences(sequences, min_length=2, max_length=4):
        """Find common subsequences in user journeys"""
        subsequence_counts = defaultdict(int)
        
        for sequence in sequences:
            for length in range(min_length, min(max_length + 1, len(sequence) + 1)):
                for i in range(len(sequence) - length + 1):
                    subseq = tuple(sequence[i:i+length])
                    subsequence_counts[subseq] += 1
        
        # Filter by minimum support
        min_support = max(2, len(sequences) * 0.05)  # At least 5% support
        common_subsequences = {k: v for k, v in subsequence_counts.items() if v >= min_support}
        
        return sorted(common_subsequences.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # Find patterns separately for successful and failed users
    successful_sequences = [user_sequences[u] for u in successful_users if u in user_sequences]
    dropoff_sequences = [user_sequences[u] for u in drop_off_users if u in user_sequences]
    
    success_patterns = find_common_subsequences(successful_sequences)
    failure_patterns = find_common_subsequences(dropoff_sequences)
    
    results = {
        'user_segments': {
            'successful': successful_analysis,
            'failed_payment': failed_analysis,
            'dropoff': dropoff_analysis
        },
        'friction_analysis': friction_impact,
        'terminal_events': dict(terminal_events),
        'success_patterns': success_patterns,
        'failure_patterns': failure_patterns,
        'total_users': len(user_sequences)
    }
    
    return results

def print_pattern_insights(results):
    """Print formatted insights from pattern analysis"""
    
    print("USER JOURNEY PATTERN ANALYSIS")
    print("="*50)
    
    segments = results['user_segments']
    
    for segment_name, data in segments.items():
        if not data:
            continue
            
        print(f"\n{segment_name.upper()} USERS:")
        print(f"Count: {data['count']:,}")
        print(f"Avg sequence length: {data['avg_sequence_length']:.1f}")
        print(f"Common start patterns:")
        for pattern, count in data['common_starts']:
            print(f"  {pattern} ({count})")
    
    print(f"\nFRICTION EVENTS IMPACT:")
    for event, data in results['friction_analysis'].items():
        print(f"{event}:")
        print(f"  Users affected: {data['users_affected']:,}")
        print(f"  Success rate after friction: {data['success_rate']*100:.1f}%")

# Example usage:
# results = discover_user_journey_patterns('/path/to/data.csv')  
# print_pattern_insights(results)