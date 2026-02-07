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

### Run Revenue Analysis

```bash
# Basic usage
python agent_sdk.py path/to/data.csv

# With max turns
python agent_sdk.py path/to/data.csv --max-turns 50

# With automatic evaluation
python agent_sdk.py path/to/data.csv --evaluate
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
├── analysis_results.txt              # Main analysis report
├── analysis_results_evaluation.json  # Evaluation scores & feedback
├── evaluations.db                    # Session memory database
├── artifacts/
│   ├── conversion_funnel.html
│   ├── dropoff_analysis.html
│   ├── user_segments.html
│   └── friction_analysis.html
└── saved_scripts/
    └── [generated analysis scripts]
```

## Example Workflow

```bash
# 1. Run analysis with evaluation
cd autonomous_agent
python agent_sdk.py ../Commuter\ Users\ Event\ data.csv --evaluate

# 2. View results
cat analysis_results.txt

# 3. View evaluation
cat analysis_results_evaluation.json

# 4. Open visualizations
open artifacts/conversion_funnel.html
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

The evaluator uses SQLite-based session memory to:
- Track evaluation history
- Compare improvements over time
- Maintain context across iterations
- Enable iterative refinement

Session IDs can be specified for tracking:
```bash
python evaluator_agent.py analysis_results.txt --session-id iteration_1
```

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
