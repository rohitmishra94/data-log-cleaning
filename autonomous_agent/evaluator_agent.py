"""
Evaluator Agent that critiques and scores revenue analysis output.
Uses session memory to track evaluation history and improvements.
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from agents import Agent, Runner, ModelSettings
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions.memory import AdvancedSQLiteSession

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Bedrock configuration
bedrock_extra_args = {
    "anthropic_beta": ["context-1m-2025-08-07"]
}

EVALUATOR_SYSTEM_PROMPT = """You are an Expert Data Analysis Evaluator.

Your role is to critically evaluate revenue analysis reports and provide:
1. **Quality Score** (0-100) across multiple dimensions
2. **Critical Assessment** of strengths and weaknesses
3. **Actionable Improvements** to make the analysis better
4. **Reality Check** on claims and projections

## Evaluation Criteria:

### 1. Data Quality (20 points)
- Are all data sources properly validated?
- Are missing values and outliers addressed?
- Is the sample size adequate for conclusions?

### 2. Methodology (25 points)
- Are statistical methods appropriate?
- Are assumptions clearly stated and reasonable?
- Is the analysis reproducible?
- Are edge cases considered?

### 3. Insights Quality (25 points)
- Are insights actionable and specific?
- Do recommendations have clear ROI estimates?
- Are projections realistic vs overly optimistic?
- Is business context properly considered?

### 4. Clarity & Communication (15 points)
- Is the analysis easy to understand?
- Are visualizations effective?
- Is jargon minimized?
- Are key findings highlighted?

### 5. Completeness (15 points)
- Are all key questions answered?
- Is the funnel analysis comprehensive?
- Are alternative explanations considered?
- Are limitations acknowledged?

## Output Format:

Return a JSON object with:
```json
{
  "overall_score": 85,
  "dimension_scores": {
    "data_quality": 18,
    "methodology": 22,
    "insights_quality": 20,
    "clarity": 13,
    "completeness": 12
  },
  "strengths": [
    "Strength 1",
    "Strength 2"
  ],
  "weaknesses": [
    "Weakness 1",
    "Weakness 2"
  ],
  "critical_issues": [
    "Issue 1: Revenue projections unrealistic - assumes 100% conversion possible"
  ],
  "improvements": [
    {
      "category": "Methodology",
      "issue": "Revenue projections assume all users intend to purchase",
      "suggestion": "Segment users by intent (browsers vs buyers) and apply realistic recovery rates (5-15%)",
      "impact": "High - makes projections credible"
    }
  ],
  "realistic_assessment": {
    "claimed_opportunity": "₹1,845,000",
    "realistic_opportunity": "₹100,000-180,000",
    "rationale": "Not all users intend to buy. Industry benchmarks show 10-20% conversion is excellent."
  }
}
```

Be brutally honest. Focus on making the analysis actually useful for business decisions.
"""


async def evaluate_analysis(analysis_file_path: str, session_id: str = None):
    """
    Evaluate a revenue analysis report with session memory.

    Args:
        analysis_file_path: Path to the analysis results file
        session_id: Optional session ID for memory (generates one if not provided)

    Returns:
        Evaluation results dictionary
    """

    if session_id is None:
        session_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Read the analysis file
    if not os.path.exists(analysis_file_path):
        raise FileNotFoundError(f"Analysis file not found: {analysis_file_path}")

    with open(analysis_file_path, 'r') as f:
        analysis_content = f.read()

    # Create evaluator agent
    evaluator_agent = Agent(
        name="Analysis Evaluator",
        instructions=EVALUATOR_SYSTEM_PROMPT,
        model=LitellmModel(model="bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"),
        model_settings=ModelSettings(
            include_usage=True,
            extra_args=bedrock_extra_args,
            reasoning={'effort': 'high'},
            extra_headers={"anthropic-beta": "interleaved-thinking-2025-05-14"}
        )
    )

    # Create session with memory
    db_path = os.path.join(
        os.path.dirname(analysis_file_path),
        "evaluations.db"
    )

    session = AdvancedSQLiteSession(
        session_id=session_id,
        db_path=db_path,
        create_tables=True
    )

    # Create evaluation prompt
    task = f"""
    Evaluate this revenue analysis report:

    {'='*80}
    {analysis_content}
    {'='*80}

    Provide a comprehensive evaluation following the criteria above.
    Be specific and actionable in your feedback.

    Focus especially on:
    1. Are revenue projections realistic?
    2. Are drop-off rates properly interpreted?
    3. Are recommendations actually implementable?
    4. What critical insights are missing?

    Return your evaluation as a JSON object.
    """

    print(f"\n🔍 Starting Analysis Evaluation")
    print(f"📁 Analysis File: {analysis_file_path}")
    print(f"🆔 Session ID: {session_id}")
    print(f"💾 Memory DB: {db_path}")
    print(f"🤖 Evaluator: Claude Sonnet 4")
    print(f"\n{'='*80}\n")

    # Run evaluation
    result = await Runner.run(
        starting_agent=evaluator_agent,
        input=task,
        session=session
    )

    print(f"\n{'='*80}")
    print(f"✅ Evaluation Complete!")
    print(f"{'='*80}\n")

    # Extract and parse the evaluation JSON
    # RunResult has a `final_response` attribute
    evaluation_text = result.final_response if hasattr(result, 'final_response') else str(result)

    # Try to extract JSON from the response
    try:
        # Look for JSON in code blocks or raw text
        if "```json" in evaluation_text:
            json_start = evaluation_text.find("```json") + 7
            json_end = evaluation_text.find("```", json_start)
            json_str = evaluation_text[json_start:json_end].strip()
        elif "```" in evaluation_text:
            json_start = evaluation_text.find("```") + 3
            json_end = evaluation_text.find("```", json_start)
            json_str = evaluation_text[json_start:json_end].strip()
        else:
            json_str = evaluation_text.strip()

        evaluation = json.loads(json_str)
    except json.JSONDecodeError:
        # If JSON parsing fails, create a basic structure
        evaluation = {
            "overall_score": None,
            "raw_evaluation": evaluation_text,
            "parse_error": "Could not parse JSON from response"
        }

    # Save evaluation to file
    output_file = analysis_file_path.replace('.txt', '_evaluation.json')
    with open(output_file, 'w') as f:
        json.dump({
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "analysis_file": analysis_file_path,
            "evaluation": evaluation
        }, f, indent=2)

    print(f"📄 Evaluation saved to: {output_file}")

    # Print summary
    if "overall_score" in evaluation and evaluation["overall_score"]:
        print(f"\n📊 Overall Score: {evaluation['overall_score']}/100")

        if "dimension_scores" in evaluation:
            print(f"\n📈 Dimension Scores:")
            for dim, score in evaluation["dimension_scores"].items():
                print(f"   • {dim.replace('_', ' ').title()}: {score}")

        if "critical_issues" in evaluation and evaluation["critical_issues"]:
            print(f"\n🚨 Critical Issues:")
            for issue in evaluation["critical_issues"]:
                print(f"   • {issue}")

        if "realistic_assessment" in evaluation:
            ra = evaluation["realistic_assessment"]
            print(f"\n💰 Reality Check:")
            print(f"   Claimed: {ra.get('claimed_opportunity', 'N/A')}")
            print(f"   Realistic: {ra.get('realistic_opportunity', 'N/A')}")

    return evaluation


def run_evaluation_sync(analysis_file_path: str, session_id: str = None):
    """Synchronous wrapper for evaluate_analysis"""
    import asyncio
    return asyncio.run(evaluate_analysis(analysis_file_path, session_id))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate revenue analysis report")
    parser.add_argument(
        "analysis_file",
        nargs="?",
        default="analysis_results.txt",
        help="Path to analysis results file"
    )
    parser.add_argument(
        "--session-id",
        help="Session ID for memory tracking (optional)"
    )

    args = parser.parse_args()

    analysis_path = os.path.abspath(args.analysis_file)

    if not os.path.exists(analysis_path):
        print(f"❌ Error: Analysis file not found at {analysis_path}")
        sys.exit(1)

    # Run evaluation
    evaluation = run_evaluation_sync(analysis_path, args.session_id)

    print(f"\n✅ Evaluation complete!")
