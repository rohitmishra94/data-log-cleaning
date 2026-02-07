"""
Autonomous Revenue Analysis Agent using OpenAI Agents SDK.
"""
import os
import sys
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel

# Add parent directory to path to import tools and prompts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import execute_python, save_successful_script
from prompts import REVENUE_AGENT_SYSTEM_PROMPT, ANALYSIS_CONTEXT

load_dotenv()

# Bedrock configuration
bedrock_extra_args = {
    "anthropic_beta": ["context-1m-2025-08-07"]
}


def run_revenue_analysis(csv_path: str, max_turns: int = 50):
    """
    Run autonomous revenue analysis using OpenAI Agents SDK.

    Args:
        csv_path: Path to the CSV file to analyze
        max_turns: Maximum number of agent turns (default: 50)
    """

    # Create the revenue analysis agent
    revenue_agent = Agent(
        name="Revenue Analyst",
        instructions=REVENUE_AGENT_SYSTEM_PROMPT + "\n\n" + ANALYSIS_CONTEXT,
        tools=[execute_python, save_successful_script],
        model=LitellmModel(model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"),
        model_settings=ModelSettings(
            include_usage=True,
            extra_args=bedrock_extra_args,
            reasoning={'effort': 'medium'},
            extra_headers={"anthropic-beta": "interleaved-thinking-2025-05-14"}
        )
    )

    # Create the task prompt
    task = f"""
    Analyze the event data at: {csv_path}

    Execute this complete analysis:

    1. **Data Understanding Phase**
       - Read the CSV and examine structure
       - Count users, events, date range
       - Identify data quality issues

    2. **Event Classification Phase**
       - Find terminal events (payment, booking, success events)
       - Classify as behavioral, system, or onboarding
       - Calculate event frequencies

    3. **Revenue Analysis Phase**
       - Build conversion funnels automatically
       - Calculate conversion rates
       - Identify drop-off points
       - Estimate revenue impact

    4. **Pattern Discovery Phase**
       - Find common user journeys
       - Identify sequences that predict drop-off
       - Calculate time-to-conversion metrics

    5. **Visualization Phase**
       - Create plotly visualizations (save as HTML)
       - Generate funnel charts
       - Create drop-off analysis charts

    6. **Insights & Recommendations Phase**
       - Provide specific, actionable recommendations
       - Estimate revenue impact of each fix
       - Prioritize by impact

    7. **Save Successful Scripts**
       - Save any valuable analysis scripts you create

    Work through each phase systematically using the execute_python tool.
    Generate complete analysis with visualizations and insights.
    """

    print(f"\n🚀 Starting Autonomous Revenue Analysis")
    print(f"📁 CSV: {csv_path}")
    print(f"🔄 Max Turns: {max_turns}")
    print(f"🤖 Agent: Revenue Analyst (Claude Sonnet 4)")
    print(f"\n{'='*80}\n")

    # Save outputs to file as we go
    output_file = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/analysis_results.txt"

    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("AUTONOMOUS REVENUE ANALYSIS RESULTS\n")
        f.write("="*80 + "\n\n")

    # Run the agent
    result = Runner.run_sync(
        starting_agent=revenue_agent,
        input=task,
        max_turns=max_turns
    )

    print(f"\n{'='*80}")
    print(f"✅ Analysis Complete!")
    print(f"{'='*80}\n")
    print(f"📄 Results saved to: {output_file}")
    print(f"\nTo view results: cat {output_file}")

    # Check for HTML files
    import glob
    html_files = glob.glob("/tmp/*.html") + glob.glob("*.html")
    if html_files:
        print(f"\n📊 Visualizations created:")
        for f in html_files:
            if any(x in f for x in ['conversion', 'revenue', 'funnel', 'pattern', 'user']):
                print(f"   • {f}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run autonomous revenue analysis")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="../Commuter Users Event data.csv",
        help="Path to CSV file"
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=50,
        help="Maximum agent turns (default: 50)"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run evaluator agent after analysis"
    )

    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # Run the analysis
    run_revenue_analysis(csv_path, max_turns=args.max_turns)

    # Run evaluator if requested
    if args.evaluate:
        print(f"\n{'='*80}")
        print("🔍 Running Evaluator Agent...")
        print(f"{'='*80}\n")

        from evaluator_agent import run_evaluation_sync
        output_file = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/analysis_results.txt"
        run_evaluation_sync(output_file)
