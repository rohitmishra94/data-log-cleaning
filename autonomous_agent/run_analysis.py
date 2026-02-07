#!/usr/bin/env python3
"""
Entry point script to run autonomous revenue analysis.

Usage:
    python run_analysis.py [csv_path]

If csv_path is not provided, uses the default Commuter Users Event data.
"""
import os
import sys
import argparse
from datetime import datetime

# Try to import OpenAI version first, fallback to Gemini
try:
    from revenue_agent_openai import RevenueAnalysisAgent
    USING_OPENAI = True
except ImportError:
    from revenue_agent import RevenueAnalysisAgent
    USING_OPENAI = False


def main():
    parser = argparse.ArgumentParser(description="Run autonomous revenue analysis on event data")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="../Commuter Users Event data.csv",
        help="Path to CSV file to analyze (default: Commuter Users Event data.csv)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=20,
        help="Maximum number of agent iterations (default: 20)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API key (default: uses GEMINI_API_KEY environment variable)"
    )

    args = parser.parse_args()

    # Resolve the CSV path
    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"🤖 AUTONOMOUS REVENUE ANALYSIS AGENT")
    print(f"{'='*80}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 CSV File: {csv_path}")
    print(f"🔄 Max Iterations: {args.max_iterations}")
    print(f"🔧 Using: {'OpenAI GPT-4o' if USING_OPENAI else 'Gemini'}")
    print(f"{'='*80}\n")

    try:
        # Initialize the agent
        agent = RevenueAnalysisAgent(api_key=args.api_key)

        # Run the analysis
        results = agent.analyze(csv_path, max_iterations=args.max_iterations)

        # Print summary
        print(f"\n{'='*80}")
        print(f"📊 ANALYSIS SUMMARY")
        print(f"{'='*80}\n")

        summary = agent.get_summary()
        print(summary)

        # Save results to file
        output_dir = "analysis_results"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"analysis_{timestamp}.txt")

        with open(output_file, 'w') as f:
            f.write(f"Autonomous Revenue Analysis Report\n")
            f.write(f"{'='*80}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"CSV File: {csv_path}\n")
            f.write(f"Iterations: {results['iterations']}\n")
            f.write(f"{'='*80}\n\n")
            f.write(summary)

        print(f"\n💾 Full analysis saved to: {output_file}")

        # List saved scripts
        from tools import list_saved_scripts
        saved_scripts = list_saved_scripts()
        if saved_scripts['success'] and saved_scripts['count'] > 0:
            print(f"\n📜 Saved {saved_scripts['count']} analysis script(s):")
            for script in saved_scripts['scripts']:
                print(f"   • {script['name']}: {script['description']}")

        print(f"\n{'='*80}")
        print(f"✅ Analysis completed successfully!")
        print(f"{'='*80}\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
