"""
Autonomous Revenue Analysis Agent using OpenAI with function calling.
"""
import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path to import tools and prompts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import execute_python, save_successful_script, list_saved_scripts
from prompts import REVENUE_AGENT_SYSTEM_PROMPT, get_initial_prompt

load_dotenv()


class RevenueAnalysisAgent:
    """Autonomous agent for revenue and retention analysis using OpenAI."""

    def __init__(self, api_key: str = None):
        """Initialize the agent with OpenAI client."""
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be provided or set in environment")

        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o"  # Using GPT-4o for best function calling
        self.conversation_history = []
        self.analysis_results = []

        # Define tools for OpenAI
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": "Execute Python code and return the output. Use this to analyze data, create visualizations, and perform calculations.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. The code will have access to pandas, numpy, plotly, and other data science libraries."
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_successful_script",
                    "description": "Save a successful analysis script for future reuse. Use this after creating valuable analysis code.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name for the script (without .py extension)"
                            },
                            "code": {
                                "type": "string",
                                "description": "The Python code to save"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of what the script does"
                            }
                        },
                        "required": ["name", "code", "description"]
                    }
                }
            }
        ]

    def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        function_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"\n🔧 Tool Call: {function_name}")
        print(f"📝 Args preview: {str(args)[:200]}...")

        if function_name == "execute_python":
            result = execute_python(args["code"])
            if result["success"]:
                print(f"✅ Execution successful")
                if result["output"]:
                    print(f"📊 Output preview: {result['output'][:500]}...")
            else:
                print(f"❌ Execution failed: {result['error']}")
            return result

        elif function_name == "save_successful_script":
            result = save_successful_script(
                args["name"],
                args["code"],
                args.get("description", "")
            )
            if result["success"]:
                print(f"💾 Script saved: {result['file_path']}")
            return result

        else:
            return {"success": False, "error": f"Unknown function: {function_name}"}

    def analyze(self, csv_path: str, max_iterations: int = 20) -> Dict[str, Any]:
        """
        Run autonomous analysis on the provided CSV file.

        Args:
            csv_path: Path to the CSV file to analyze
            max_iterations: Maximum number of agent iterations

        Returns:
            Dictionary with analysis results and insights
        """
        print(f"\n🚀 Starting autonomous revenue analysis...")
        print(f"📁 Data file: {csv_path}")
        print(f"🤖 Model: {self.model_name}")
        print(f"🔄 Max iterations: {max_iterations}\n")

        # Initialize conversation with system prompt and task
        initial_prompt = get_initial_prompt(csv_path)

        self.conversation_history = [
            {"role": "system", "content": REVENUE_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": initial_prompt}
        ]

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"Iteration {iteration}/{max_iterations}")
            print(f"{'='*80}")

            try:
                # Generate response from the model
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.conversation_history,
                    tools=self.tools,
                    tool_choice="auto",  # Let model decide when to use tools
                    temperature=0.1,  # Low temperature for consistent analysis
                )

                assistant_message = response.choices[0].message

                # Add assistant response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })

                # Check for text response
                if assistant_message.content:
                    print(f"\n💬 Agent: {assistant_message.content[:500]}...")
                    self.analysis_results.append({
                        "type": "text",
                        "content": assistant_message.content,
                        "iteration": iteration
                    })

                # Check for tool calls
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        # Execute the tool
                        result = self._execute_tool_call(tool_call)

                        # Add tool result to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps(result)
                        })

                        self.analysis_results.append({
                            "type": "tool_call",
                            "function": tool_call.function.name,
                            "result": result,
                            "iteration": iteration
                        })
                else:
                    # No tool calls - agent is done
                    if response.choices[0].finish_reason == "stop":
                        print("\n✅ Analysis complete - agent has finished")
                        break

            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {str(e)}")
                import traceback
                traceback.print_exc()
                break

        # Compile final results
        final_results = {
            "success": True,
            "iterations": iteration,
            "analysis_results": self.analysis_results,
            "conversation_history": self.conversation_history
        }

        print(f"\n{'='*80}")
        print(f"🎉 Analysis completed in {iteration} iterations")
        print(f"{'='*80}\n")

        return final_results

    def get_summary(self) -> str:
        """Get a summary of the analysis."""
        text_parts = [r["content"] for r in self.analysis_results if r["type"] == "text"]
        return "\n\n".join(text_parts)
