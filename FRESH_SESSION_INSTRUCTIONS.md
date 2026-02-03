# Fresh Session Instructions

## Project Overview

This is a **Product Analytics Dashboard** for a bus ticket booking mobile app. The system analyzes user behavior to identify friction points, drop-off patterns, and opportunities for conversion optimization.

## What We've Built

### 1. Core Architecture (4 Layers)

```
Layer 1: Data Profiler → Layer 2: Pattern Discovery → Layer 3: LLM Synthesis → Layer 4: Dashboard
```

**Files:**
- `data_profiler.py` - Automated event data profiling with system event detection
- `pattern_discovery.py` - ML algorithms (DBSCAN, Apriori, Sequential Mining, Survival Analysis)
- `pattern_synthesis.py` - LLM intelligence layer (replaces hardcoded rules)
- `app1.py` - Main unified dashboard

### 2. Key Innovation: LLM-Driven Pattern Interpretation

**Problem Solved:** Originally, pattern interpretation used hardcoded if/else rules like:
```python
if data['avg_repetitions'] > 3:
    insights[f"FRICTION: {event}"] = "Major friction point"
```

**Solution:** Now uses LLM synthesis for contextual, adaptive insights:
```python
synthesized = synthesizer.synthesize_patterns(raw_patterns, business_context)
# Result: "The 0.4s gap indicates keystroke-level tracking. Implement debouncing..."
```

### 3. Dashboard Structure (app1.py)

**4 Main Tabs:**

1. **Data** - Raw event data and repetition summaries
2. **Analysis** - User journey visualization and AI interpretation
3. **Session Analysis** - Drop-off points using system event detection
4. **Pattern Discovery** - ML-discovered patterns with LLM insights
   - Sequential Patterns (journey flows)
   - User Segments (behavioral clusters)
   - Friction Analysis (stuck points)
   - Survival Analysis (drop-off probability)
   - Intervention Triggers (dropout predictors)

## Critical Technical Decisions

### Session Detection Method

**What We Use:** System events as ground truth
- Events like `Session Started`, `Journey Started`, `App Installed`, `User Login`
- Result: 37,058 sessions detected

**What We Don't Use:** Time-gap based detection
- Original approach using 30-minute gaps
- Result: Only 6,748 sessions (missed 82%)

**Why:** System events are explicit boundaries set by the app, representing true user intent.

### Success/Dropout Definition

**Correct Approach (Current):**
```python
success_events = {
    'payment_success', 'booking_confirmed', 'payment_initiate',
    'ticket_confirmed', 'booking_complete', 'payment_completed'
}
is_successful = bool(session_events & success_events)
```

**Wrong Approach (Fixed):**
- Originally used arbitrary thresholds (>20 events AND >10 unique types)
- Led to false positives: "app_start → 99% dropout"

**Fix Applied:**
- Excluded onboarding events from dropout analysis
- Defined success based on actual booking outcomes

### Cluster Labels

**Current (LLM-Driven):**
```python
# Neutral labels - LLM creates personas
label = 'outliers' if cluster_id == -1 else f'segment_{cluster_id}'
```

**Previous (Hardcoded):**
```python
# Domain-specific assumptions
label = 'strugglers' if avg_events > 200 else 'quick_bookers'
```

## Key Files and Their Purpose

### Core Engine Files

| File | Purpose | Lines | Key Methods |
|------|---------|-------|-------------|
| `data_profiler.py` | Event data profiling, Markov chains, session detection | 500+ | `profile()`, `_detect_sessions()`, `_build_markov_chain()` |
| `pattern_discovery.py` | ML pattern mining (DBSCAN, Apriori, Sequential) | 700+ | `discover()`, `_discover_sequential_patterns()`, `_mine_association_rules()` |
| `pattern_synthesis.py` | LLM intelligence layer | 334 | `synthesize_all_patterns()`, `_synthesize_sequential_patterns()` |
| `run_data_profiler.py` | Generate data_profile_report.json | 50 | - |
| `run_pattern_discovery.py` | Generate pattern_discovery_report.json with LLM synthesis | 50 | - |

### Dashboard Files

| File | Purpose | Port |
|------|---------|------|
| `app1.py` | **Main unified dashboard** (4 tabs) | 8501 |
| `app3_session_analysis.py` | Standalone session analysis | 8503 |
| `app4_pattern_discovery.py` | Standalone pattern discovery | 8504 |

### Documentation Files

| File | Contents |
|------|----------|
| `SEQUENTIAL_PATTERN_ANALYSIS.md` | Explains how temporal order is preserved in sequential mining |
| `DATA_PROFILER_METHODS_EXPLAINED.md` | Technical deep-dive into profiling algorithms |
| `SESSION_ANALYSIS_VISUALIZATION.md` | Dashboard design patterns |
| `TRUE_SESSION_DETECTION.md` | Why system events > time gaps |
| `ADAPTIVE_RETENTION_ENGINE_PROPOSAL.md` | Scalable 4-layer architecture proposal |

## How to Run the System

### Step 1: Generate Profile Data
```bash
python run_data_profiler.py
```
**Output:** `data_profile_report.json` (session analysis data)

### Step 2: Generate Pattern Discovery Data
```bash
python run_pattern_discovery.py
```
**Output:** `pattern_discovery_report.json` (ML patterns + LLM insights)

### Step 3: Run Dashboard
```bash
source venv/bin/activate
streamlit run app1.py
```
**URL:** http://localhost:8501

## Data Files Required

```
data-log-cleaning/
├── Commuter Users Event data.csv          # Raw event data
├── pipeline_deduplication/
│   ├── cleaned_events.csv                 # Deduplicated events
│   ├── repetition_summary.csv             # Event repetition analysis
│   └── unique_users_list.csv              # User list
├── data_profile_report.json               # Generated by run_data_profiler.py
└── pattern_discovery_report.json          # Generated by run_pattern_discovery.py
```

## Key Insights Discovered

### 1. Search Friction (CRITICAL)
- Event: `_location_elastic-town-search`
- Repetition: 97.7% (10.6x avg per session)
- Issue: Each keystroke tracked as separate event
- Fix: Implement debouncing (wait 300-500ms before API call)

### 2. Seat Selection Struggle (HIGH)
- Event: `select_seat`
- Repetition: 94.4% (5.1x avg, max 100x!)
- Issue: Small touch targets, no visual feedback
- Fix: Expand touch areas to 44x44px, instant visual feedback

### 3. Authentication Wall (CRITICAL)
- Event: `_auth_verify-otp` → `enter_otp`
- Dropout: 99.9% confidence
- Issue: SMS latency, no auto-read OTP
- Fix: WhatsApp OTP fallback, implement guest checkout

### 4. User Segments (DBSCAN Clustering)
- **Segment 0** (85%): Standard Explorers - avg 96 events, 0.39 diversity
- **Outliers** (15%): Deep-Search Stumblers - avg 379 events, 0.19 diversity (stuck in search loops)

## Git Branch Structure

**Current Branch:** `feature/session-analysis-dashboard`

**Pull Request:** #1 - https://github.com/rohitmishra94/data-log-cleaning/pull/1

**Commits:**
1. Initial session analysis dashboard
2. Pattern discovery integration
3. **Latest:** "Transform Pattern Discovery to LLM-driven intelligence layer"

## Common Issues and Fixes

### Issue 1: Intervention Triggers Show Onboarding as Dropout
**Symptom:** Rules like "app_start → 99.8% dropout", "choose_language → 98.9% dropout"

**Cause:** Onboarding events included in dropout analysis

**Fix Applied:**
```python
# Exclude onboarding events from transactions
onboarding_events = {
    'app_start', 'choose_language', 'Onboarding_Language',
    'generate_otp', 'Onboarding_get_otp', ...
}
if session_events.issubset(onboarding_events):
    continue  # Skip pure onboarding sessions
```

### Issue 2: Misleading Metric Arrows
**Symptom:** Dashboard showing ⬆️ arrows on neutral metrics

**Fix:** Removed all `delta` parameters from `st.metric()` calls

### Issue 3: Hardcoded Pattern Interpretation
**Symptom:** Generic insights like "Major friction point"

**Fix:** Implemented LLM synthesis layer (`pattern_synthesis.py`)

## LLM Synthesis Configuration

**Model Used:** Anthropic Claude (via `ANTHROPIC_API_KEY` env variable)

**Prompt Structure:**
```python
system_prompt = f"""You are a product analytics expert analyzing {business_context}.
Your task is to interpret {pattern_type} data and provide actionable insights."""

user_prompt = f"""Here is the raw data: {json.dumps(pattern_data)}
Provide: 1. Key Insights, 2. Root Causes, 3. Business Impact, 4. Recommendations"""
```

**Business Context:** "bus ticket booking mobile app"

## Testing Checklist

Before making changes:
- [ ] Run `python run_data_profiler.py` - should complete in ~30 seconds
- [ ] Run `python run_pattern_discovery.py` - should complete in ~2 minutes
- [ ] Start app: `streamlit run app1.py`
- [ ] Navigate to each of the 4 tabs
- [ ] Check Pattern Discovery tab shows LLM insights in expandable sections
- [ ] Verify no onboarding events in intervention triggers

## Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Required packages
streamlit
pandas
numpy
plotly
scikit-learn
mlxtend
lifelines
anthropic

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Next Steps / Future Enhancements

### Potential Improvements
1. **Time-Gap Constraints:** Only extract patterns where events occur within 5 minutes
2. **PrefixSpan Algorithm:** Handle longer patterns (currently capped at length 5)
3. **Cycle Detection:** Detect loops like `A → B → A → B → A` (user stuck)
4. **Real-Time Alerts:** Trigger interventions when dropout patterns detected
5. **A/B Testing Framework:** Test intervention effectiveness

### Known Limitations
- Sequential patterns capped at length 5 (performance trade-off)
- DBSCAN parameters (eps=0.5, min_samples=50) may need tuning for different datasets
- LLM synthesis requires API key and internet connection
- Large datasets (>1M events) may require batch processing

## Quick Reference Commands

```bash
# Kill all Streamlit processes
pkill -f streamlit

# Run main dashboard
source venv/bin/activate && streamlit run app1.py

# Run standalone session analysis
streamlit run app3_session_analysis.py --server.port=8503

# Run standalone pattern discovery
streamlit run app4_pattern_discovery.py --server.port=8504

# Generate both report files
python run_data_profiler.py && python run_pattern_discovery.py

# Check git status
git status

# View PR
gh pr view 1
```

## Important Notes for Fresh Session

1. **Always check if report files exist** before running the dashboard
   - `data_profile_report.json`
   - `pattern_discovery_report.json`

2. **LLM insights are optional** - if `pattern_synthesis.py` fails, raw patterns still display

3. **Session detection uses ONLY system events** - don't add time-gap logic

4. **Onboarding events must stay excluded** from dropout analysis

5. **Cluster labels must remain neutral** (segment_0, outliers) - LLM creates personas

6. **Sequential patterns preserve temporal order** - verified in `SEQUENTIAL_PATTERN_ANALYSIS.md`

## Contact / Questions

For questions about this codebase:
1. Read the markdown documentation files first
2. Check `pattern_discovery.py` docstrings for algorithm details
3. Look at `SEQUENTIAL_PATTERN_ANALYSIS.md` for pattern mining verification
4. Review PR #1 description for full context

---

**Last Updated:** 2026-02-03
**Branch:** feature/session-analysis-dashboard
**Status:** Ready for merge to master
