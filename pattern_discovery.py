"""
Pattern Discovery Engine: Layer 2 of Adaptive Retention Engine

This module discovers meaningful patterns in user behavior by analyzing
the output from DataProfiler (Layer 1). It identifies:
- Sequential patterns (friction points)
- User segments (behavioral clusters)
- Drop-off risk (survival analysis)
- Hidden states (what users are thinking)
- Predictive rules (intervention triggers)

Author: Adaptive Retention Engine Team
"""

import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import json
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from lifelines import KaplanMeierFitter
import warnings
warnings.filterwarnings('ignore')


class PatternDiscovery:
    """
    Discovers actionable patterns from profiled event data.

    Takes DataProfiler output and applies machine learning algorithms
    to find:
    - Why users drop off
    - Which user segments exist
    - What patterns predict success/failure
    - Where to intervene for maximum impact
    """

    def __init__(self, min_pattern_support=0.05, min_confidence=0.6):
        """
        Initialize Pattern Discovery Engine.

        Args:
            min_pattern_support (float): Minimum frequency for pattern (5% = 1 in 20 sessions)
            min_confidence (float): Minimum confidence for rules (60%)
        """
        self.min_support = min_pattern_support
        self.min_confidence = min_confidence

    def discover(self, events_df: pd.DataFrame, profile_data: Dict = None) -> Dict[str, Any]:
        """
        Main discovery method - finds all patterns.

        Args:
            events_df: Raw event data with columns [user_id, event_name, timestamp, session_id]
            profile_data: Optional DataProfiler output for context

        Returns:
            Dictionary with discovered patterns:
            - sequential_patterns: Frequent event sequences
            - user_segments: Behavioral clusters
            - survival_analysis: Drop-off risk curves
            - hidden_states: User mental states
            - intervention_rules: Trigger conditions
        """
        print("🔍 Pattern Discovery Engine Starting...")
        print("=" * 60)

        # Ensure data is sorted
        events_df = events_df.sort_values(['user_id', 'timestamp'])

        patterns = {
            'metadata': {
                'total_events': len(events_df),
                'unique_users': events_df['user_id'].nunique(),
                'total_sessions': events_df['session_id'].nunique() if 'session_id' in events_df.columns else None,
                'discovery_config': {
                    'min_support': self.min_support,
                    'min_confidence': self.min_confidence
                }
            }
        }

        # 1. Sequential Pattern Mining
        print("\n1️⃣  Mining Sequential Patterns...")
        patterns['sequential_patterns'] = self._discover_sequential_patterns(events_df)

        # 2. User Clustering
        print("\n2️⃣  Clustering Users into Segments...")
        patterns['user_segments'] = self._discover_user_segments(events_df)

        # 3. Survival Analysis
        print("\n3️⃣  Analyzing Session Survival...")
        patterns['survival_analysis'] = self._analyze_survival(events_df)

        # 4. Friction Point Detection
        print("\n4️⃣  Detecting Friction Points...")
        patterns['friction_points'] = self._detect_friction_points(events_df)

        # 5. Association Rules
        print("\n5️⃣  Mining Association Rules...")
        patterns['intervention_rules'] = self._mine_association_rules(events_df)

        print("\n" + "=" * 60)
        print("✅ Pattern Discovery Complete!")

        return patterns

    def _discover_sequential_patterns(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find frequent sequential patterns in user journeys.

        Uses a simplified PrefixSpan-like algorithm to find:
        - Common event sequences
        - Repetition patterns (user hesitation)
        - Paths leading to drop-offs

        Returns:
            Dictionary with:
            - frequent_sequences: Top sequences and their frequency
            - repetition_patterns: Events users repeat (friction signals)
            - dropout_sequences: Common paths before abandonment
        """
        # Build sequences per session
        if 'session_id' not in events_df.columns:
            # Create pseudo-sessions if not available
            events_df = events_df.copy()
            events_df['session_id'] = events_df.groupby('user_id').cumcount() // 20

        sequences = []
        for session_id, session_df in events_df.groupby('session_id'):
            seq = session_df['event_name'].tolist()
            sequences.append(seq)

        # Find frequent patterns (length 2-5)
        pattern_counts = defaultdict(int)

        for seq in sequences:
            # Extract all subsequences
            for length in range(2, min(6, len(seq) + 1)):
                for i in range(len(seq) - length + 1):
                    subseq = tuple(seq[i:i+length])
                    pattern_counts[subseq] += 1

        # Filter by minimum support
        min_count = int(len(sequences) * self.min_support)
        frequent_patterns = {
            ' → '.join(pattern): count
            for pattern, count in pattern_counts.items()
            if count >= min_count
        }

        # Sort by frequency
        frequent_patterns = dict(sorted(
            frequent_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:50])  # Top 50

        # Find repetition patterns
        repetition_patterns = self._find_repetitions(sequences)

        # Find dropout sequences (last N events before session end)
        dropout_sequences = self._find_dropout_sequences(sequences)

        return {
            'total_sequences': len(sequences),
            'frequent_patterns': frequent_patterns,
            'repetition_patterns': repetition_patterns,
            'dropout_sequences': dropout_sequences,
            'pattern_insights': self._interpret_patterns(frequent_patterns, repetition_patterns)
        }

    def _find_repetitions(self, sequences: List[List[str]]) -> Dict[str, Any]:
        """Find events that users repeat (hesitation signals)."""
        repetition_counts = Counter()
        max_repetitions = defaultdict(list)

        for seq in sequences:
            # Count consecutive repeats
            i = 0
            while i < len(seq):
                event = seq[i]
                count = 1
                while i + count < len(seq) and seq[i + count] == event:
                    count += 1

                if count > 1:
                    repetition_counts[event] += 1
                    max_repetitions[event].append(count)

                i += count

        # Summarize
        repetition_summary = {}
        for event, counts in max_repetitions.items():
            repetition_summary[event] = {
                'sessions_with_repetition': repetition_counts[event],
                'avg_repetitions': np.mean(counts),
                'max_repetitions': max(counts),
                'total_repeated_events': sum(counts) - len(counts)  # Extra events beyond first
            }

        # Sort by frequency
        repetition_summary = dict(sorted(
            repetition_summary.items(),
            key=lambda x: x[1]['sessions_with_repetition'],
            reverse=True
        )[:20])

        return repetition_summary

    def _find_dropout_sequences(self, sequences: List[List[str]]) -> Dict[str, int]:
        """Find common sequences before session end (dropout patterns)."""
        dropout_patterns = Counter()

        for seq in sequences:
            if len(seq) >= 2:
                # Last 2-3 events
                for length in [2, 3]:
                    if len(seq) >= length:
                        pattern = ' → '.join(seq[-length:])
                        dropout_patterns[pattern] += 1

        return dict(dropout_patterns.most_common(30))

    def _interpret_patterns(self, frequent_patterns: Dict, repetition_patterns: Dict) -> Dict[str, str]:
        """Generate human-readable insights from patterns."""
        insights = {}

        # Check for common friction patterns
        for pattern, count in list(frequent_patterns.items())[:10]:
            if 'search' in pattern.lower() and count > 100:
                insights[pattern] = "Users frequently search multiple times - possible discovery issues"
            elif 'select_seat' in pattern.lower():
                insights[pattern] = "Seat selection appears in common journeys - critical conversion point"
            elif 'login' in pattern.lower():
                insights[pattern] = "Authentication is common step - reduce friction here"

        # Check repetition issues
        for event, data in list(repetition_patterns.items())[:5]:
            if data['avg_repetitions'] > 3:
                insights[f"FRICTION: {event}"] = f"Users repeat this {data['avg_repetitions']:.1f}x on average - major friction point"

        return insights

    def _discover_user_segments(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Cluster users into behavioral segments.

        Creates feature vectors for each user and uses clustering
        to identify distinct behavior patterns.

        Features:
        - Session count
        - Average session length
        - Event diversity
        - Repetition ratio
        - Time span
        """
        # Build user feature matrix
        user_features = []
        user_ids = []

        for user_id, user_df in events_df.groupby('user_id'):
            user_ids.append(user_id)

            # Calculate features
            features = {
                'total_events': len(user_df),
                'unique_events': user_df['event_name'].nunique(),
                'event_diversity': user_df['event_name'].nunique() / len(user_df),
                'time_span_hours': (user_df['timestamp'].max() - user_df['timestamp'].min()).total_seconds() / 3600,
            }

            # Repetition ratio (consecutive duplicates)
            user_df = user_df.sort_values('timestamp')
            consecutive_same = (user_df['event_name'] == user_df['event_name'].shift(1)).sum()
            features['repetition_ratio'] = consecutive_same / len(user_df) if len(user_df) > 0 else 0

            # Session count (if available)
            if 'session_id' in user_df.columns:
                features['session_count'] = user_df['session_id'].nunique()
                features['avg_session_length'] = len(user_df) / features['session_count']

            user_features.append(features)

        features_df = pd.DataFrame(user_features, index=user_ids)

        # Simple rule-based clustering (can be replaced with DBSCAN)
        segments = self._rule_based_clustering(features_df)

        return {
            'total_users': len(user_ids),
            'segments': segments,
            'feature_summary': features_df.describe().to_dict()
        }

    def _rule_based_clustering(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """DBSCAN clustering for user segmentation."""
        segments = {}

        # Prepare features for clustering
        feature_cols = ['total_events', 'event_diversity', 'repetition_ratio', 'time_span_hours']
        X = features_df[feature_cols].fillna(0)

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Apply DBSCAN clustering
        # eps: Maximum distance between samples (tune based on data scale)
        # min_samples: Minimum cluster size
        dbscan = DBSCAN(eps=0.5, min_samples=50)
        features_df['cluster'] = dbscan.fit_predict(X_scaled)

        # Analyze each cluster
        unique_clusters = features_df['cluster'].unique()

        # Label clusters based on characteristics
        for cluster_id in unique_clusters:
            cluster_data = features_df[features_df['cluster'] == cluster_id]

            avg_events = cluster_data['total_events'].mean()
            avg_diversity = cluster_data['event_diversity'].mean()
            avg_repetition = cluster_data['repetition_ratio'].mean()

            # Determine cluster label based on characteristics
            if cluster_id == -1:
                label = 'others'
                description = 'Outliers with unique behavior patterns'
            elif avg_repetition > features_df['repetition_ratio'].quantile(0.75):
                label = 'strugglers'
                description = 'Users facing friction - high repetition and stuck patterns'
            elif avg_events < features_df['total_events'].quantile(0.33) and avg_diversity > features_df['event_diversity'].median():
                label = 'quick_bookers'
                description = 'Users who know what they want and book quickly'
            elif avg_events > features_df['total_events'].quantile(0.67) and avg_diversity > features_df['event_diversity'].median():
                label = 'explorers'
                description = 'Users who browse extensively before deciding'
            else:
                label = f'cluster_{cluster_id}'
                description = 'Users with distinct behavior patterns'

            segments[label] = {
                'count': len(cluster_data),
                'percentage': len(cluster_data) / len(features_df) * 100,
                'characteristics': {
                    'avg_events': avg_events,
                    'avg_diversity': avg_diversity,
                    'avg_repetition': avg_repetition
                },
                'description': description
            }

        # If no strugglers/quick_bookers/explorers found, use rule-based fallback
        if 'strugglers' not in segments:
            strugglers = features_df[features_df['repetition_ratio'] > features_df['repetition_ratio'].quantile(0.75)]
            if len(strugglers) > 0:
                segments['strugglers'] = {
                    'count': len(strugglers),
                    'percentage': len(strugglers) / len(features_df) * 100,
                    'characteristics': {
                        'avg_events': strugglers['total_events'].mean(),
                        'avg_diversity': strugglers['event_diversity'].mean(),
                        'avg_repetition': strugglers['repetition_ratio'].mean()
                    },
                    'description': 'Users facing friction - high repetition and stuck patterns'
                }

        if 'quick_bookers' not in segments:
            quick_bookers = features_df[
                (features_df['total_events'] < features_df['total_events'].quantile(0.33)) &
                (features_df['event_diversity'] > features_df['event_diversity'].median())
            ]
            if len(quick_bookers) > 0:
                segments['quick_bookers'] = {
                    'count': len(quick_bookers),
                    'percentage': len(quick_bookers) / len(features_df) * 100,
                    'characteristics': {
                        'avg_events': quick_bookers['total_events'].mean(),
                        'avg_diversity': quick_bookers['event_diversity'].mean(),
                        'avg_repetition': quick_bookers['repetition_ratio'].mean()
                    },
                    'description': 'Users who know what they want and book quickly'
                }

        return segments

    def _analyze_survival(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Survival analysis: probability of continuing at each step.

        Calculates session "survival" rate at each event position.
        """
        if 'session_id' not in events_df.columns:
            return {'error': 'session_id required for survival analysis'}

        # Get session lengths
        session_lengths = events_df.groupby('session_id').size()

        # Calculate survival at each step
        max_steps = min(100, session_lengths.max())
        survival_curve = []

        for step in range(1, max_steps + 1):
            surviving = (session_lengths >= step).sum()
            survival_rate = surviving / len(session_lengths)
            survival_curve.append({
                'step': step,
                'surviving_sessions': surviving,
                'survival_rate': survival_rate,
                'dropout_rate': 1 - survival_rate
            })

        # Find critical drop-off points (largest decreases)
        dropoffs = []
        for i in range(1, len(survival_curve)):
            prev_rate = survival_curve[i-1]['survival_rate']
            curr_rate = survival_curve[i]['survival_rate']
            drop = prev_rate - curr_rate

            if drop > 0.05:  # 5% drop
                dropoffs.append({
                    'step': i + 1,
                    'drop_percentage': drop * 100,
                    'survival_before': prev_rate,
                    'survival_after': curr_rate
                })

        return {
            'survival_curve': survival_curve[:30],  # First 30 steps
            'critical_dropoffs': sorted(dropoffs, key=lambda x: x['drop_percentage'], reverse=True)[:10],
            'median_session_length': int(session_lengths.median()),
            'sessions_reaching_step_10': (session_lengths >= 10).sum(),
            'sessions_reaching_step_20': (session_lengths >= 20).sum()
        }

    def _detect_friction_points(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Identify specific events where users get stuck.

        Friction indicators:
        - High repetition rate
        - Long time gaps
        - Common exit points
        """
        friction_scores = {}

        for event_name, event_df in events_df.groupby('event_name'):
            # Calculate metrics
            event_df = event_df.sort_values(['user_id', 'timestamp'])

            # Repetition rate
            event_df['is_repeat'] = event_df.groupby('user_id')['event_name'].shift(1) == event_name
            repetition_rate = event_df['is_repeat'].mean()

            # Average time gap (within sessions)
            if 'session_id' in event_df.columns:
                event_df['time_gap'] = event_df.groupby('session_id')['timestamp'].diff().dt.total_seconds()
                avg_time_gap = event_df['time_gap'].median()
            else:
                avg_time_gap = None

            # Friction score (simple heuristic)
            friction_score = repetition_rate * 100

            if friction_score > 10:  # More than 10% repetition
                friction_scores[event_name] = {
                    'repetition_rate': repetition_rate,
                    'avg_time_gap_seconds': avg_time_gap,
                    'friction_score': friction_score,
                    'total_occurrences': len(event_df),
                    'users_affected': event_df['user_id'].nunique()
                }

        # Sort by friction score
        friction_scores = dict(sorted(
            friction_scores.items(),
            key=lambda x: x[1]['friction_score'],
            reverse=True
        )[:20])

        return {
            'high_friction_events': friction_scores,
            'friction_summary': self._summarize_friction(friction_scores)
        }

    def _summarize_friction(self, friction_scores: Dict) -> str:
        """Generate summary of friction findings."""
        if not friction_scores:
            return "No significant friction points detected"

        top_friction = list(friction_scores.items())[0]
        event_name, metrics = top_friction

        summary = f"Highest friction: '{event_name}' with {metrics['repetition_rate']:.1%} repetition rate. "
        summary += f"{metrics['users_affected']:,} users affected. "

        if metrics['repetition_rate'] > 0.5:
            summary += "CRITICAL: More than half of occurrences are repeats - major UX issue."
        elif metrics['repetition_rate'] > 0.3:
            summary += "HIGH: Significant user hesitation detected."
        else:
            summary += "MEDIUM: Some friction present but manageable."

        return summary

    def _mine_association_rules(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find associations between events and outcomes using Apriori algorithm.

        Example rule: IF (search > 10x AND seat_selection > 5x) THEN abandon (95% confidence)
        """
        if 'session_id' not in events_df.columns:
            return {'error': 'session_id required for association mining'}

        # Build transactions (one per session)
        transactions = []
        session_outcomes = {}

        for session_id, session_df in events_df.groupby('session_id'):
            event_counts = session_df['event_name'].value_counts().to_dict()
            session_length = len(session_df)

            # Define outcome (successful = long session with diverse events)
            is_successful = (
                session_length > 20 and
                session_df['event_name'].nunique() > 10
            )
            session_outcomes[session_id] = is_successful

            # Create transaction with repeated events marked
            transaction = []
            for event, count in event_counts.items():
                if count > 3:
                    transaction.append(f"{event}_repeated")
                else:
                    transaction.append(event)

            # Add outcome to transaction
            transaction.append('dropout' if not is_successful else 'success')
            transactions.append(transaction)

        # Convert to one-hot encoded dataframe for Apriori
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        # Apply Apriori algorithm
        try:
            frequent_itemsets = apriori(
                df_encoded,
                min_support=self.min_support,
                use_colnames=True,
                max_len=3
            )

            if len(frequent_itemsets) == 0:
                # Fallback to manual rule mining
                return self._manual_rule_mining(events_df)

            # Generate association rules
            rules_df = association_rules(
                frequent_itemsets,
                metric="confidence",
                min_threshold=self.min_confidence
            )

            # Filter rules that predict dropout
            dropout_rules = rules_df[
                rules_df['consequents'].apply(lambda x: 'dropout' in str(x))
            ].copy()

            # Format rules
            formatted_rules = []
            for _, row in dropout_rules.iterrows():
                antecedents = list(row['antecedents'])
                condition = ' AND '.join([str(item).replace('_repeated', ' > 3x') for item in antecedents])

                formatted_rules.append({
                    'condition': condition,
                    'outcome': 'dropout_likely',
                    'confidence': row['confidence'],
                    'support': int(row['support'] * len(transactions)),
                    'lift': row['lift'],
                    'recommendation': f"Intervene when user triggers: {condition}"
                })

            # Sort by confidence
            formatted_rules = sorted(formatted_rules, key=lambda x: x['confidence'], reverse=True)[:15]

            return {
                'total_rules': len(formatted_rules),
                'intervention_triggers': formatted_rules,
                'algorithm': 'Apriori'
            }

        except Exception as e:
            print(f"   ⚠️  Apriori failed ({str(e)}), using manual rule mining")
            return self._manual_rule_mining(events_df)

    def _manual_rule_mining(self, events_df: pd.DataFrame) -> Dict[str, Any]:
        """Fallback manual rule mining when Apriori fails."""
        rules = []

        for session_id, session_df in events_df.groupby('session_id'):
            event_counts = session_df['event_name'].value_counts().to_dict()
            session_length = len(session_df)

            is_successful = (
                session_length > 20 and
                session_df['event_name'].nunique() > 10
            )

            for event, count in event_counts.items():
                if count > 3:
                    rules.append({
                        'condition': f"{event} > 3x",
                        'outcome': 'success' if is_successful else 'dropout',
                        'session_length': session_length
                    })

        rule_stats = defaultdict(lambda: {'success': 0, 'dropout': 0})

        for rule in rules:
            condition = rule['condition']
            outcome = rule['outcome']
            rule_stats[condition][outcome] += 1

        formatted_rules = []
        for condition, outcomes in rule_stats.items():
            total = outcomes['success'] + outcomes['dropout']
            if total >= 10:
                confidence = outcomes['dropout'] / total
                if confidence > self.min_confidence:
                    formatted_rules.append({
                        'condition': condition,
                        'outcome': 'dropout_likely',
                        'confidence': confidence,
                        'support': total,
                        'recommendation': f"Intervene when user triggers: {condition}"
                    })

        formatted_rules = sorted(formatted_rules, key=lambda x: x['confidence'], reverse=True)[:15]

        return {
            'total_rules': len(formatted_rules),
            'intervention_triggers': formatted_rules,
            'algorithm': 'Manual'
        }

    def save_patterns(self, patterns: Dict, filename: str = 'pattern_discovery_report.json'):
        """Save discovered patterns to JSON file."""
        with open(filename, 'w') as f:
            json.dump(patterns, f, indent=2, default=str)
        print(f"\n💾 Patterns saved to: {filename}")

    def print_summary(self, patterns: Dict):
        """Print human-readable summary of discoveries."""
        print("\n" + "=" * 60)
        print("📊 PATTERN DISCOVERY SUMMARY")
        print("=" * 60)

        # Sequential Patterns
        seq = patterns.get('sequential_patterns', {})
        print(f"\n🔄 Sequential Patterns:")
        print(f"   Found {len(seq.get('frequent_patterns', {}))} frequent sequences")
        print(f"   Detected {len(seq.get('repetition_patterns', {}))} repetition patterns")

        if seq.get('repetition_patterns'):
            top_rep = list(seq['repetition_patterns'].items())[0]
            print(f"   Top friction: {top_rep[0]} (repeated in {top_rep[1]['sessions_with_repetition']} sessions)")

        # User Segments
        segments = patterns.get('user_segments', {}).get('segments', {})
        print(f"\n👥 User Segments:")
        for seg_name, seg_data in segments.items():
            print(f"   {seg_name.replace('_', ' ').title()}: {seg_data.get('count', 0)} users ({seg_data.get('percentage', 0):.1f}%)")

        # Survival Analysis
        survival = patterns.get('survival_analysis', {})
        if 'critical_dropoffs' in survival:
            print(f"\n⚠️  Critical Drop-off Points:")
            for dropoff in survival['critical_dropoffs'][:3]:
                print(f"   Step {dropoff['step']}: {dropoff['drop_percentage']:.1f}% drop")

        # Intervention Rules
        rules = patterns.get('intervention_rules', {}).get('intervention_triggers', [])
        print(f"\n🎯 Intervention Triggers:")
        print(f"   Discovered {len(rules)} high-confidence rules")
        if rules:
            for rule in rules[:3]:
                print(f"   • {rule['condition']} → {rule['confidence']:.0%} dropout risk")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    print("PatternDiscovery module loaded successfully!")
    print("Use: discovery = PatternDiscovery() to create an instance")
