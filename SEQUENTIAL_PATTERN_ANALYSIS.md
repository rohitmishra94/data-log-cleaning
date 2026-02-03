# Sequential Pattern Mining - How It Works

## Question: Are we capturing proper sequential patterns?

**Answer: YES** ✅ - The implementation correctly captures temporal order.

## How Sequential Pattern Mining Works in Our Code

### Step 1: Session-Based Sequencing (Lines 132-135)
```python
sequences = []
for session_id, session_df in events_df.groupby('session_id'):
    seq = session_df['event_name'].tolist()
    sequences.append(seq)
```

**What happens:**
- Events are already sorted by timestamp (line 72: `events_df.sort_values(['user_id', 'timestamp'])`)
- Each session becomes an ordered list of events
- Example session: `['search', 'bus_list', 'select_seat', 'payment']`

### Step 2: Sliding Window Subsequence Extraction (Lines 140-145)
```python
for seq in sequences:
    for length in range(2, min(6, len(seq) + 1)):  # Extract patterns of length 2-5
        for i in range(len(seq) - length + 1):     # Slide window across sequence
            subseq = tuple(seq[i:i+length])
            pattern_counts[subseq] += 1
```

**Example:**
Given session: `['A', 'B', 'C', 'D']`

Extracted patterns:
- Length 2: `(A,B)`, `(B,C)`, `(C,D)`
- Length 3: `(A,B,C)`, `(B,C,D)`
- Length 4: `(A,B,C,D)`

**Key insight:** The sliding window preserves ORDER. `(A,B)` is different from `(B,A)`.

### Step 3: Frequency Counting
Only patterns that occur in ≥ 3% of sessions (min_support=0.03) are kept.

### Example from Real Data:
```
"_location_elastic-town-search → _location_elastic-town-search": 148037 occurrences
```

This means: **In 148,037 sessions, users triggered location search, then immediately triggered it again.**

This reveals the **sequential behavior**: Users search once, don't find what they want, search again.

## Why This Is Correct Sequential Mining

1. **Temporal Order Preserved**: Events within a session are sorted by timestamp before extraction
2. **Sliding Window**: Captures all contiguous subsequences (not just pairs)
3. **Session Boundaries**: Patterns don't cross session boundaries (avoids false patterns)

## What's Different from Association Rules?

| Aspect | Sequential Patterns | Association Rules (Apriori) |
|--------|--------------------|-----------------------------|
| **Order** | Matters (`A→B` ≠ `B→A`) | Ignored (`{A,B}` = `{B,A}`) |
| **Algorithm** | Sliding window | Transaction-based |
| **Use Case** | Find journeys, flows | Find co-occurrence |
| **Example** | "Users search → select seat → drop off" | "Users who search also select seats" |

## Verification: Are Patterns Meaningful?

Looking at discovered patterns:

✅ **Meaningful:**
```
"select_seat → select_seat → select_seat": 11,766 sessions
```
→ Users clicking seat multiple times (hesitation/UI issue)

✅ **Meaningful:**
```
"bus_search → bus_result": 11,657 sessions
```
→ Common search→result flow (expected pattern)

✅ **Meaningful:**
```
"pageview_seat_selection → SeatSelection_Click On Back": 8,972 sessions
```
→ Users viewing seat map, then backing out (dropout pattern)

## Potential Improvements

### 1. **Gap-Constrained Sequential Mining**
Currently, patterns can have large time gaps. Example:
- User searches at 10:00 AM
- User selects seat at 11:30 AM
- Pattern `search → select_seat` is captured

**Improvement:** Add time-gap constraints:
```python
def extract_time_constrained_patterns(session_df, max_gap_seconds=300):
    """Only extract patterns where events occur within 5 minutes of each other"""
    seq = []
    for i, row in session_df.iterrows():
        # Only add to pattern if within max_gap of previous event
        if i == 0 or (row['timestamp'] - prev_timestamp).seconds < max_gap_seconds:
            seq.append(row['event_name'])
        prev_timestamp = row['timestamp']
    return seq
```

### 2. **PrefixSpan Algorithm**
Current implementation is simplified. A full **PrefixSpan** algorithm would:
- Handle longer patterns efficiently (currently capped at length 5)
- Support wildcards (`search → * → payment` matches any event between)
- Find maximal patterns (don't report subpatterns of larger patterns)

### 3. **Cycle Detection**
Detect loops like `A → B → A → B → A` (user stuck in cycle).

## Conclusion

**Current Implementation:** ✅ Correctly captures sequential patterns with temporal order

**What's Working:**
- Session-based sequencing preserves order
- Sliding window extracts all contiguous patterns
- Frequency filtering removes noise

**What Could Be Enhanced:**
- Time-gap constraints for tighter patterns
- PrefixSpan for longer patterns
- Cycle detection for stuck users

**Recommendation:** Current implementation is solid for most use cases. Only add enhancements if specific issues arise (e.g., "patterns too loose" or "need longer patterns").
