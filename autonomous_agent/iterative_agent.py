"""
Iterative Revenue Analysis with Evaluator Feedback Loop.

Runs the revenue agent, evaluates results, and iteratively improves
based on evaluator feedback until score > 80% or max 3 iterations.
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent_sdk import run_revenue_analysis_async
from evaluator_agent import evaluate_analysis

load_dotenv()


async def iterative_analysis(csv_path: str, max_iterations: int = 3, target_score: int = 80):
    """
    Run iterative analysis with evaluator feedback loop.

    Args:
        csv_path: Path to CSV data file
        max_iterations: Maximum number of improvement cycles (default: 3)
        target_score: Target quality score to achieve (default: 80)

    Returns:
        Final evaluation results
    """

    base_session_id = f"iterative_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    analysis_file = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/analysis_results.txt"

    print(f"\n{'='*80}")
    print(f"🔄 ITERATIVE REVENUE ANALYSIS")
    print(f"{'='*80}")
    print(f"📁 CSV: {csv_path}")
    print(f"🎯 Target Score: {target_score}/100")
    print(f"🔄 Max Iterations: {max_iterations}")
    print(f"🆔 Base Session ID: {base_session_id}")
    print(f"{'='*80}\n")

    feedback_history = []
    iteration = 1
    current_score = 0

    while iteration <= max_iterations and current_score < target_score:
        print(f"\n{'='*80}")
        print(f"🔄 ITERATION {iteration}/{max_iterations}")
        print(f"{'='*80}\n")

        # Prepare feedback context for this iteration
        feedback_context = ""
        if feedback_history:
            feedback_context = f"""
## PREVIOUS ITERATION FEEDBACK:

You have attempted this analysis {iteration - 1} time(s) before.
The evaluator identified the following issues that MUST be addressed:

"""
            for i, feedback in enumerate(feedback_history, 1):
                feedback_context += f"""
### Iteration {i} (Score: {feedback['score']}/100):

**Critical Issues:**
{chr(10).join(f"- {issue}" for issue in feedback.get('critical_issues', []))}

**Key Improvements Needed:**
{chr(10).join(f"- {imp['suggestion']}" for imp in feedback.get('improvements', [])[:3])}

**Reality Check:**
{feedback.get('realistic_assessment', {}).get('rationale', 'N/A')}

"""

            feedback_context += f"""
## YOUR TASK:
Address ALL the issues from previous iterations. Pay special attention to:
1. Realistic revenue projections (use industry benchmarks)
2. Proper user segmentation (browsers vs buyers)
3. Fix any calculation errors
4. Validate data quality issues
5. Provide implementable recommendations

DO NOT repeat the same mistakes. Learn from the feedback.
"""

        # Update task file with feedback
        feedback_file = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/iteration_feedback.txt"
        with open(feedback_file, 'w') as f:
            f.write(feedback_context if feedback_context else "First iteration - no prior feedback.")

        # Run revenue analysis
        session_id = f"{base_session_id}_iter{iteration}"

        print(f"📊 Running Revenue Analysis (Session: {session_id})")
        print(f"{'─'*80}\n")

        # Inject feedback into the analysis context
        if feedback_context:
            # Temporarily update prompts with feedback
            from prompts import ANALYSIS_CONTEXT
            enhanced_context = ANALYSIS_CONTEXT + "\n\n" + feedback_context

            # Monkey patch for this iteration
            import prompts
            original_context = prompts.ANALYSIS_CONTEXT
            prompts.ANALYSIS_CONTEXT = enhanced_context

            try:
                await run_revenue_analysis_async(csv_path, max_turns=30, session_id=session_id)
            finally:
                # Restore original context
                prompts.ANALYSIS_CONTEXT = original_context
        else:
            await run_revenue_analysis_async(csv_path, max_turns=30, session_id=session_id)

        print(f"\n{'─'*80}")
        print(f"✅ Analysis Complete")
        print(f"{'─'*80}\n")

        # Run evaluation
        eval_session_id = f"{base_session_id}_eval_iter{iteration}"

        print(f"🔍 Running Evaluation (Session: {eval_session_id})")
        print(f"{'─'*80}\n")

        evaluation = await evaluate_analysis(analysis_file, eval_session_id)

        current_score = evaluation.get('overall_score', 0)

        print(f"\n{'─'*80}")
        print(f"📊 Iteration {iteration} Results:")
        print(f"{'─'*80}")
        print(f"Score: {current_score}/100")

        if current_score >= target_score:
            print(f"✅ Target score achieved! ({current_score} >= {target_score})")
            print(f"{'─'*80}\n")
            break

        if iteration < max_iterations:
            print(f"⚠️  Below target. Starting iteration {iteration + 1}...")
            print(f"{'─'*80}\n")

            # Store feedback for next iteration
            feedback_history.append({
                'iteration': iteration,
                'score': current_score,
                'critical_issues': evaluation.get('critical_issues', []),
                'improvements': evaluation.get('improvements', []),
                'realistic_assessment': evaluation.get('realistic_assessment', {})
            })
        else:
            print(f"⚠️  Max iterations reached. Final score: {current_score}/100")
            print(f"{'─'*80}\n")

        iteration += 1

    # Final summary
    print(f"\n{'='*80}")
    print(f"🎯 ITERATIVE ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Total Iterations: {iteration - 1}")
    print(f"Final Score: {current_score}/100")
    print(f"Target Score: {target_score}/100")

    if current_score >= target_score:
        print(f"✅ SUCCESS - Target achieved!")
    else:
        print(f"⚠️  Target not reached - Consider manual review")

    print(f"{'='*80}\n")

    # Save iteration history
    history_file = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/iteration_history.json"
    with open(history_file, 'w') as f:
        json.dump({
            'base_session_id': base_session_id,
            'csv_path': csv_path,
            'target_score': target_score,
            'final_score': current_score,
            'iterations': iteration - 1,
            'success': current_score >= target_score,
            'feedback_history': feedback_history
        }, f, indent=2)

    print(f"📄 Iteration history saved to: {history_file}")

    return evaluation


def run_iterative_sync(csv_path: str, max_iterations: int = 3, target_score: int = 80):
    """Synchronous wrapper for iterative analysis"""
    return asyncio.run(iterative_analysis(csv_path, max_iterations, target_score))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run iterative revenue analysis with evaluator feedback loop"
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        default="../Commuter Users Event data.csv",
        help="Path to CSV data file"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum improvement cycles (default: 3)"
    )
    parser.add_argument(
        "--target-score",
        type=int,
        default=80,
        help="Target quality score (default: 80)"
    )

    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv_path)

    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        sys.exit(1)

    # Run iterative analysis
    run_iterative_sync(csv_path, args.max_iterations, args.target_score)
