# Autonomous Revenue Analysis Agent

AI-powered autonomous agent that analyzes event data to identify revenue opportunities, conversion bottlenecks, and provides actionable recommendations.

## Features

- 🤖 **Autonomous Analysis**: Uses Claude Sonnet 4 to autonomously explore and analyze data
- 📊 **Multi-Phase Analysis**:
  - Data profiling and quality checks
  - Event classification and funnel building
  - Revenue impact analysis
  - Pattern discovery and user journey analysis
  - Visualization generation
  - Executive insights and recommendations
- 🔍 **Evaluator Agent**: Critiques analysis output with realistic assessments
- 💾 **Session Memory**: Tracks evaluation history for continuous improvement

## Setup

### Requirements

```bash
pip install openai-agents[litellm] python-dotenv pandas plotly
```

### AWS Bedrock Configuration

Create `.env` file with your AWS credentials:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION_NAME=us-east-1
```

## Usage

### Iterative Analysis (Recommended) 🔄

**Automatically improves analysis based on evaluator feedback**

```bash
# Run with automatic improvement loop (stops at score > 80% or 3 iterations)
python iterative_agent.py path/to/data.csv

# Custom target score and max iterations
python iterative_agent.py path/to/data.csv --target-score 85 --max-iterations 5

# Example
python iterative_agent.py ../Commuter\ Users\ Event\ data.csv
```

**How it works:**
1. Runs revenue analysis
2. Evaluates results (scores 0-100)
3. If score < 80%, feeds feedback back to agent
4. Repeats up to 3 times until score > 80%

### Run Revenue Analysis (Single Pass)

```bash
# Basic usage (auto-generates session ID)
python agent_sdk.py path/to/data.csv

# With session ID for tracking
python agent_sdk.py path/to/data.csv --session-id iteration_1

# With max turns
python agent_sdk.py path/to/data.csv --max-turns 50

# With automatic evaluation
python agent_sdk.py path/to/data.csv --evaluate

# Full example with all options
python agent_sdk.py ../Commuter\ Users\ Event\ data.csv \
  --max-turns 30 \
  --session-id v2_improvements \
  --evaluate
```

### Run Evaluator Separately

```bash
# Evaluate existing analysis
python evaluator_agent.py analysis_results.txt

# With session ID for memory tracking
python evaluator_agent.py analysis_results.txt --session-id eval_v2
```

## Architecture

### Revenue Agent (`agent_sdk.py`)
- Reads CSV event data
- Discovers events, users, and patterns autonomously
- Builds dynamic conversion funnels
- Generates visualizations
- Provides recommendations with revenue impact

### Evaluator Agent (`evaluator_agent.py`)
- Scores analysis on 5 dimensions (0-100)
- Identifies strengths and weaknesses
- Provides reality check on projections
- Suggests specific improvements
- Uses session memory to track changes

### Evaluation Criteria

| Dimension | Weight | Focus |
|-----------|--------|-------|
| Data Quality | 20% | Validation, missing values, sample size |
| Methodology | 25% | Statistical rigor, assumptions, reproducibility |
| Insights Quality | 25% | Actionability, realism, ROI estimates |
| Clarity | 15% | Communication, visualizations, jargon |
| Completeness | 15% | Coverage, alternatives, limitations |

## Output Files

```
autonomous_agent/
├── analysis_results.txt              # Main analysis report (latest)
├── analysis_results_evaluation.json  # Evaluation scores & feedback
├── iteration_history.json            # Iterative improvement history
├── iteration_feedback.txt            # Feedback sent to agent each iteration
├── revenue_sessions.db               # Revenue agent session memory
├── evaluations.db                    # Evaluator session memory
├── artifacts/
│   ├── conversion_funnel.html
│   ├── dropoff_analysis.html
│   ├── user_segments.html
│   └── friction_analysis.html
└── saved_scripts/
    └── [generated analysis scripts]
```

## Example Workflows

### Simple Workflow (Single Pass)

```bash
cd autonomous_agent

# Run analysis with evaluation
python agent_sdk.py ../Commuter\ Users\ Event\ data.csv --evaluate

# View results
cat analysis_results.txt
cat analysis_results_evaluation.json

# Open visualizations
open artifacts/conversion_funnel.html
```

### Iterative Workflow (Recommended)

```bash
cd autonomous_agent

# Run iterative improvement loop
python iterative_agent.py ../Commuter\ Users\ Event\ data.csv

# The agent will:
# - Iteration 1: Run analysis → Score: 55/100
# - Iteration 2: Apply feedback → Score: 72/100
# - Iteration 3: Apply feedback → Score: 83/100 ✓ (>80%, stops)

# View iteration history
cat iteration_history.json

# View final results
cat analysis_results.txt
cat analysis_results_evaluation.json
```

## Key Insights Format

The evaluator provides:
- **Overall Score**: Composite quality score (0-100)
- **Dimension Scores**: Breakdown by evaluation criteria
- **Critical Issues**: High-priority problems to fix
- **Improvements**: Specific, actionable suggestions
- **Reality Check**: Realistic vs optimistic projections

Example evaluation output:
```json
{
  "overall_score": 72,
  "critical_issues": [
    "Revenue projections unrealistic - assumes 100% conversion possible"
  ],
  "realistic_assessment": {
    "claimed_opportunity": "₹1,845,000",
    "realistic_opportunity": "₹100,000-180,000",
    "rationale": "Not all users intend to buy. 10-20% conversion is excellent."
  }
}
```

## Session Memory

Both agents use SQLite-based session memory to:
- **Track conversation history** - Previous analyses and evaluations
- **Learn from feedback** - Remember what worked and what didn't
- **Compare improvements** - Track changes across iterations
- **Maintain context** - Continuous conversation across runs
- **Enable iterative refinement** - Build on previous work

### Session Databases:
- **`revenue_sessions.db`** - Revenue agent conversation history
- **`evaluations.db`** - Evaluator agent assessment history

### Using Sessions:
```bash
# First iteration
python agent_sdk.py data.csv --session-id v1 --evaluate

# Continue conversation in same session
python agent_sdk.py data.csv --session-id v1 --evaluate

# Start fresh iteration
python agent_sdk.py data.csv --session-id v2 --evaluate

# View session history
sqlite3 revenue_sessions.db "SELECT * FROM sessions;"
```

Session memory allows the agent to:
- Reference previous findings
- Build on earlier analysis
- Remember user feedback
- Improve over multiple runs

## Tools & Prompts

- **`tools.py`**: Python execution and script saving tools
- **`prompts.py`**: System prompts for revenue agent
- **`evaluator_agent.py`**: Evaluator prompts and scoring logic

## Model Configuration

Both agents use:
- **Model**: Claude Sonnet 4 (via AWS Bedrock)
- **Context**: 1M tokens
- **Thinking**: Interleaved reasoning mode
- **Effort**: Medium (revenue) / High (evaluator)

## License

Part of the data-log-cleaning project.
