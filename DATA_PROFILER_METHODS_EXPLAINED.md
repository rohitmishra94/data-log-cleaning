# DataProfiler Methods: Detailed Technical Explanation

## Overview
The `DataProfiler` class automatically analyzes event data to understand user behavior patterns without requiring any domain knowledge or templates. This document explains each method, the algorithms used, and the calculations performed.

---

## Core Methods

## 1. `_analyze_sessions(events_df)`

### Purpose
Identify and analyze how users group their activities into sessions (continuous periods of activity).

### What It Does

```python
def _analyze_sessions(self, events_df):
    """Identify and analyze user sessions"""

    # Step 1: Session Detection (Time-based)
    # If gap between events > threshold (e.g., 30 min), new session starts
    events_df = events_df.sort_values(['user_id', 'timestamp'])
    events_df['time_diff'] = events_df.groupby('user_id')['timestamp'].diff()
    events_df['new_session'] = events_df['time_diff'] > pd.Timedelta(minutes=30)
    events_df['session_id'] = events_df.groupby('user_id')['new_session'].cumsum()

    # Step 2: Session Statistics
    session_stats = {
        'total_sessions': events_df.groupby(['user_id', 'session_id']).ngroups,
        'avg_session_length': events_df.groupby(['user_id', 'session_id']).size().mean(),
        'median_session_length': events_df.groupby(['user_id', 'session_id']).size().median(),
        'avg_session_duration': events_df.groupby(['user_id', 'session_id'])
            .agg({'timestamp': lambda x: (x.max() - x.min()).total_seconds() / 60})
            .mean().values[0],  # in minutes
        'session_distribution': self._get_session_length_distribution(events_df),
        'incomplete_sessions': self._identify_incomplete_sessions(events_df)
    }

    # Step 3: Session Patterns
    session_patterns = {
        'common_start_events': events_df.groupby(['user_id', 'session_id'])
            .first()['event_name'].value_counts().head(10),
        'common_end_events': events_df.groupby(['user_id', 'session_id'])
            .last()['event_name'].value_counts().head(10),
        'bounce_rate': self._calculate_bounce_rate(events_df),  # Single event sessions
        'conversion_sessions': self._identify_conversion_sessions(events_df)
    }

    return {**session_stats, **session_patterns}
```

### Key Algorithms

#### Session Detection Algorithm
- **Method**: Gap-based segmentation
- **Formula**: `new_session = (time_diff > threshold)`
- **Session ID Assignment**: Cumulative sum of new_session flags

#### Statistical Calculations
- **Average Session Length**: `mean(events_per_session)`
- **Session Duration**: `max(timestamp) - min(timestamp)` per session
- **Bounce Rate**: `count(single_event_sessions) / total_sessions`

### Helper Methods

```python
def _calculate_bounce_rate(self, events_df):
    """Calculate percentage of single-event sessions"""
    session_lengths = events_df.groupby(['user_id', 'session_id']).size()
    bounce_sessions = (session_lengths == 1).sum()
    total_sessions = len(session_lengths)
    return bounce_sessions / total_sessions if total_sessions > 0 else 0

def _get_session_length_distribution(self, events_df):
    """Get percentile distribution of session lengths"""
    lengths = events_df.groupby(['user_id', 'session_id']).size()
    return {
        'p10': np.percentile(lengths, 10),
        'p25': np.percentile(lengths, 25),
        'p50': np.percentile(lengths, 50),  # median
        'p75': np.percentile(lengths, 75),
        'p90': np.percentile(lengths, 90),
        'p95': np.percentile(lengths, 95),
        'p99': np.percentile(lengths, 99)
    }
```

---

## 2. `_analyze_time_patterns(events_df)`

### Purpose
Discover temporal patterns in user behavior - when users are active, periodicity, and time-based trends.

### What It Does

```python
def _analyze_time_patterns(self, events_df):
    """Analyze temporal patterns in event data"""

    events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])

    # Step 1: Extract Time Features
    events_df['hour'] = events_df['timestamp'].dt.hour
    events_df['day_of_week'] = events_df['timestamp'].dt.dayofweek
    events_df['day_name'] = events_df['timestamp'].dt.day_name()
    events_df['is_weekend'] = events_df['day_of_week'].isin([5, 6])
    events_df['month'] = events_df['timestamp'].dt.month
    events_df['date'] = events_df['timestamp'].dt.date

    # Step 2: Activity Patterns
    time_patterns = {
        # Hourly distribution
        'hourly_activity': events_df.groupby('hour').size().to_dict(),
        'peak_hours': events_df['hour'].value_counts().head(3).index.tolist(),

        # Daily patterns
        'daily_activity': events_df.groupby('day_name').size().to_dict(),
        'weekday_vs_weekend': {
            'weekday_events': events_df[~events_df['is_weekend']].shape[0],
            'weekend_events': events_df[events_df['is_weekend']].shape[0]
        },

        # User activity patterns
        'avg_events_per_day': events_df.groupby('date').size().mean(),
        'active_days_per_user': events_df.groupby('user_id')['date'].nunique().mean(),

        # Time between events
        'avg_time_between_events': self._calculate_inter_event_times(events_df),

        # Velocity patterns (events per time unit)
        'event_velocity': self._calculate_event_velocity(events_df),

        # Periodicity detection
        'periodic_patterns': self._detect_periodicity(events_df)
    }

    return time_patterns
```

### Key Algorithms

#### Periodicity Detection Using Fourier Transform

```python
def _detect_periodicity(self, events_df):
    """Detect periodic patterns using signal processing"""

    # Create time series of event counts
    hourly_counts = events_df.set_index('timestamp').resample('H').size()

    # Fast Fourier Transform to find dominant frequencies
    from scipy.fft import fft, fftfreq

    fft_values = fft(hourly_counts.values)
    frequencies = fftfreq(len(hourly_counts), d=1/24)  # d=1/24 for hourly data

    # Find dominant periods
    power_spectrum = np.abs(fft_values) ** 2
    dominant_frequencies = frequencies[np.argsort(power_spectrum)[-5:]]
    dominant_periods = 1 / dominant_frequencies[dominant_frequencies > 0]

    # Autocorrelation for validation
    from statsmodels.tsa.stattools import acf
    autocorr = acf(hourly_counts, nlags=168)  # Check up to 1 week

    return {
        'dominant_periods_hours': dominant_periods.tolist(),
        'daily_pattern_strength': autocorr[24],  # 24-hour correlation
        'weekly_pattern_strength': autocorr[168] if len(autocorr) > 168 else None
    }
```

#### Mathematical Concepts
- **Fourier Transform**: Decomposes time series into frequency components
  - Formula: `F(ω) = ∫ f(t) * e^(-iωt) dt`
  - Identifies repeating patterns at different frequencies

- **Autocorrelation**: Measures correlation of signal with delayed version
  - Formula: `R(τ) = E[(X_t - μ)(X_{t+τ} - μ)] / σ²`
  - High autocorrelation at lag 24 = daily pattern
  - High autocorrelation at lag 168 = weekly pattern

#### Event Velocity Calculation

```python
def _calculate_event_velocity(self, events_df):
    """Calculate rate of events over time (events per minute)"""

    velocities = []

    for user_id, user_df in events_df.groupby('user_id'):
        user_df = user_df.sort_values('timestamp')

        # Use sliding window (e.g., 5-minute windows)
        window_size = pd.Timedelta(minutes=5)

        for i in range(len(user_df)):
            window_start = user_df.iloc[i]['timestamp']
            window_end = window_start + window_size

            # Count events in window
            events_in_window = user_df[
                (user_df['timestamp'] >= window_start) &
                (user_df['timestamp'] < window_end)
            ].shape[0]

            # Velocity = events per minute
            velocity = events_in_window / 5
            velocities.append(velocity)

    return {
        'avg_velocity': np.mean(velocities),
        'max_velocity': np.max(velocities),
        'velocity_percentiles': np.percentile(velocities, [25, 50, 75, 90, 95])
    }
```

---

## 3. `_build_transition_matrix(events_df)`

### Purpose
Build a Markov chain transition matrix to understand how users move between different events.

### What It Does

```python
def _build_transition_matrix(self, events_df):
    """Build transition probability matrix between events"""

    # Step 1: Create Event Pairs (current -> next)
    events_df = events_df.sort_values(['user_id', 'session_id', 'timestamp'])

    transitions = []
    for (user, session), group in events_df.groupby(['user_id', 'session_id']):
        events = group['event_name'].tolist()
        # Create pairs: (event_i, event_i+1)
        for i in range(len(events) - 1):
            transitions.append((events[i], events[i+1]))

    # Step 2: Count Transitions
    from collections import Counter, defaultdict

    transition_counts = Counter(transitions)
    event_counts = Counter([t[0] for t in transitions])

    # Step 3: Calculate Probabilities
    transition_matrix = defaultdict(dict)

    for (from_event, to_event), count in transition_counts.items():
        # P(to_event | from_event) = count(from->to) / count(from)
        probability = count / event_counts[from_event]
        transition_matrix[from_event][to_event] = probability

    # Step 4: Convert to DataFrame for better visualization
    import pandas as pd

    all_events = sorted(set(events_df['event_name']))
    matrix_df = pd.DataFrame(0.0, index=all_events, columns=all_events)

    for from_event, to_events in transition_matrix.items():
        for to_event, prob in to_events.items():
            matrix_df.loc[from_event, to_event] = prob

    # Step 5: Additional Analysis
    analysis = {
        'transition_matrix': matrix_df,
        'most_common_transitions': sorted(
            transition_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20],
        'dead_ends': self._find_dead_end_events(matrix_df),
        'high_exit_events': self._find_high_exit_probability_events(events_df),
        'strongly_connected': self._find_strongly_connected_events(matrix_df)
    }

    return analysis
```

### Key Algorithms

#### Markov Chain Construction
- **Assumption**: First-order Markov property (next state depends only on current state)
- **Transition Probability Formula**:
  ```
  P(B|A) = Count(A→B) / Count(A)
  ```
  Where:
  - `P(B|A)` = Probability of transitioning to event B given current event A
  - `Count(A→B)` = Number of times A is followed by B
  - `Count(A)` = Total occurrences of event A

#### Graph Analysis Methods

```python
def _find_dead_end_events(self, matrix_df):
    """Find events with no outgoing transitions"""
    dead_ends = []
    for event in matrix_df.index:
        if matrix_df.loc[event].sum() == 0:  # No outgoing transitions
            dead_ends.append(event)
    return dead_ends

def _find_high_exit_probability_events(self, events_df):
    """Find events that often lead to session end"""

    # Mark last event in each session
    last_events = events_df.groupby(['user_id', 'session_id']).last()
    last_event_counts = last_events['event_name'].value_counts()

    # Calculate exit probability for each event
    all_event_counts = events_df['event_name'].value_counts()

    exit_probabilities = {}
    for event in all_event_counts.index:
        if event in last_event_counts:
            # P(exit | event) = times_as_last_event / total_occurrences
            exit_prob = last_event_counts[event] / all_event_counts[event]
            exit_probabilities[event] = exit_prob

    # Return high-risk events (>50% exit probability)
    high_exit = {k: v for k, v in exit_probabilities.items() if v > 0.5}
    return sorted(high_exit.items(), key=lambda x: x[1], reverse=True)
```

#### Strongly Connected Components

```python
def _find_strongly_connected_events(self, matrix_df):
    """Find groups of events that users cycle through"""

    import networkx as nx

    # Create directed graph from transition matrix
    G = nx.DiGraph()

    for from_event in matrix_df.index:
        for to_event in matrix_df.columns:
            if matrix_df.loc[from_event, to_event] > 0.01:  # Threshold
                G.add_edge(from_event, to_event,
                          weight=matrix_df.loc[from_event, to_event])

    # Find strongly connected components using Tarjan's algorithm
    components = list(nx.strongly_connected_components(G))

    # Filter to meaningful components (>2 events)
    meaningful_components = [
        list(comp) for comp in components if len(comp) > 2
    ]

    return meaningful_components
```

**Algorithm**: Tarjan's Strongly Connected Components
- **Time Complexity**: O(V + E) where V = vertices (events), E = edges (transitions)
- **Purpose**: Find cycles in user behavior (e.g., search → view → back → search)

---

## 4. Additional Analysis Methods

### Incomplete Session Detection

```python
def _identify_incomplete_sessions(self, events_df):
    """Find sessions that didn't reach a terminal state"""

    # Define terminal events (success states)
    terminal_events = self._identify_terminal_events(events_df)

    incomplete = []

    for (user, session), group in events_df.groupby(['user_id', 'session_id']):
        events = set(group['event_name'])

        # Check if session contains any terminal event
        if not events.intersection(terminal_events):
            incomplete.append({
                'user_id': user,
                'session_id': session,
                'last_event': group.iloc[-1]['event_name'],
                'session_length': len(group),
                'duration_minutes': (group.iloc[-1]['timestamp'] -
                                   group.iloc[0]['timestamp']).total_seconds() / 60
            })

    return {
        'incomplete_count': len(incomplete),
        'incomplete_rate': len(incomplete) / events_df['session_id'].nunique(),
        'common_drop_points': Counter([s['last_event'] for s in incomplete]).most_common(10),
        'avg_incomplete_length': np.mean([s['session_length'] for s in incomplete])
    }
```

### Terminal Event Identification

```python
def _identify_terminal_events(self, events_df, threshold=0.02):
    """Identify events that represent successful completion"""

    # Method 1: Low frequency + high value events
    event_frequencies = events_df['event_name'].value_counts(normalize=True)
    rare_events = event_frequencies[event_frequencies < threshold].index

    # Method 2: Events that always end sessions
    last_events = events_df.groupby(['user_id', 'session_id']).last()
    always_last = []

    for event in events_df['event_name'].unique():
        event_occurrences = (events_df['event_name'] == event).sum()
        as_last_event = (last_events['event_name'] == event).sum()

        if event_occurrences > 0:
            last_ratio = as_last_event / event_occurrences
            if last_ratio > 0.9:  # 90% of time it's the last event
                always_last.append(event)

    # Method 3: Semantic analysis (if event names contain keywords)
    success_keywords = ['success', 'complete', 'confirm', 'done', 'finish',
                       'thank', 'receipt', 'final']

    semantic_terminals = []
    for event in events_df['event_name'].unique():
        if any(keyword in event.lower() for keyword in success_keywords):
            semantic_terminals.append(event)

    # Combine all methods
    terminal_events = set(rare_events) | set(always_last) | set(semantic_terminals)

    return list(terminal_events)
```

### Inter-Event Time Analysis

```python
def _calculate_inter_event_times(self, events_df):
    """Calculate time gaps between consecutive events"""

    inter_event_times = []

    for user_id, user_df in events_df.groupby('user_id'):
        user_df = user_df.sort_values('timestamp')
        time_diffs = user_df['timestamp'].diff().dt.total_seconds()
        inter_event_times.extend(time_diffs.dropna().tolist())

    return {
        'mean_seconds': np.mean(inter_event_times),
        'median_seconds': np.median(inter_event_times),
        'std_seconds': np.std(inter_event_times),
        'percentiles': {
            'p10': np.percentile(inter_event_times, 10),
            'p25': np.percentile(inter_event_times, 25),
            'p50': np.percentile(inter_event_times, 50),
            'p75': np.percentile(inter_event_times, 75),
            'p90': np.percentile(inter_event_times, 90),
            'p95': np.percentile(inter_event_times, 95)
        }
    }
```

---

## 5. Complete DataProfiler Class

```python
class DataProfiler:
    """Comprehensive data profiling for event data"""

    def __init__(self, session_gap_minutes=30):
        self.session_gap_minutes = session_gap_minutes

    def profile(self, events_df):
        """Main profiling method that calls all analysis functions"""

        # Basic statistics
        basic_stats = {
            'total_events': len(events_df),
            'unique_events': events_df['event_name'].nunique(),
            'unique_users': events_df['user_id'].nunique(),
            'date_range': {
                'start': events_df['timestamp'].min(),
                'end': events_df['timestamp'].max(),
                'span_days': (events_df['timestamp'].max() -
                            events_df['timestamp'].min()).days
            },
            'avg_events_per_user': len(events_df) / events_df['user_id'].nunique()
        }

        # Detailed analysis
        session_analysis = self._analyze_sessions(events_df)
        time_patterns = self._analyze_time_patterns(events_df)
        transitions = self._build_transition_matrix(events_df)

        # Event-level analysis
        event_analysis = {
            'event_frequencies': events_df['event_name'].value_counts().to_dict(),
            'rare_events': self._find_rare_events(events_df),
            'common_sequences': self._find_common_sequences(events_df),
            'event_complexity': self._calculate_event_complexity(events_df)
        }

        return {
            'basic_stats': basic_stats,
            'sessions': session_analysis,
            'time_patterns': time_patterns,
            'transitions': transitions,
            'events': event_analysis
        }
```

---

## Mathematical Foundations

### 1. Markov Chain Theory
- **State Space**: Set of all unique events
- **Transition Matrix**: P where P[i,j] = P(state_j | state_i)
- **Stationary Distribution**: π where πP = π (long-term event distribution)

### 2. Time Series Analysis
- **Fourier Transform**: Frequency domain analysis for periodicity
- **Autocorrelation Function**: Measures self-similarity over time lags
- **Seasonality Detection**: Identifies repeating patterns

### 3. Graph Theory
- **Directed Graph**: Events as nodes, transitions as edges
- **Strongly Connected Components**: Cycles in user behavior
- **Path Analysis**: Most common paths through event graph

### 4. Statistical Methods
- **Maximum Likelihood Estimation**: For probability calculations
- **Percentile Analysis**: For distribution understanding
- **Hypothesis Testing**: For pattern significance

---

## Output Example

```json
{
  "basic_stats": {
    "total_events": 125000,
    "unique_events": 45,
    "unique_users": 3200,
    "avg_events_per_user": 39.06
  },
  "sessions": {
    "total_sessions": 8500,
    "avg_session_length": 14.7,
    "avg_session_duration": 12.3,
    "bounce_rate": 0.23,
    "incomplete_rate": 0.67
  },
  "time_patterns": {
    "peak_hours": [19, 20, 21],
    "daily_pattern_strength": 0.83,
    "weekly_pattern_strength": 0.71,
    "avg_velocity": 2.4
  },
  "transitions": {
    "most_common": [
      ["search", "view_results", 0.89],
      ["view_results", "select_item", 0.34]
    ],
    "high_exit_events": [
      ["payment_failed", 0.92],
      ["error_page", 0.88]
    ]
  }
}
```

---

## Usage in Adaptive Retention Engine

The DataProfiler output feeds into:
1. **Pattern Discovery**: Uses transition matrix for sequence mining
2. **Intervention Timing**: Uses velocity and time patterns
3. **Risk Assessment**: Uses incomplete sessions and exit events
4. **Personalization**: Uses session patterns and user segments

This automated profiling eliminates the need for manual analysis or domain knowledge, making the system truly adaptive to any application's data.