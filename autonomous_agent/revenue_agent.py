"""
Autonomous Revenue Analysis Agent using Gemini 2.0 Pro and function calling.
"""
import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Add parent directory to path to import tools and prompts
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from tools import execute_python, save_successful_script, list_saved_scripts
from prompts import REVENUE_AGENT_SYSTEM_PROMPT, get_initial_prompt

load_dotenv()


class RevenueAnalysisAgent:
    """Autonomous agent for revenue and retention analysis."""

    def __init__(self, gemini_api_key: str = None):
        """Initialize the agent with Gemini client."""
        api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be provided or set in environment")

        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-exp-1206"  # Using experimental model with better function calling
        self.conversation_history = []
        self.analysis_results = []

        # Define tools for the agent
        self.tools = [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="execute_python",
                        description="Execute Python code and return the output. Use this to analyze data, create visualizations, and perform calculations.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "code": types.Schema(
                                    type=types.Type.STRING,
                                    description="Python code to execute. The code will have access to pandas, numpy, plotly, and other data science libraries."
                                )
                            },
                            required=["code"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="save_successful_script",
                        description="Save a successful analysis script for future reuse. Use this after creating valuable analysis code.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "name": types.Schema(
                                    type=types.Type.STRING,
                                    description="Name for the script (without .py extension)"
                                ),
                                "code": types.Schema(
                                    type=types.Type.STRING,
                                    description="The Python code to save"
                                ),
                                "description": types.Schema(
                                    type=types.Type.STRING,
                                    description="Description of what the script does"
                                )
                            },
                            required=["name", "code", "description"]
                        )
                    )
                ]
            )
        ]

    def _execute_tool_call(self, function_call: types.FunctionCall) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        function_name = function_call.name
        args = function_call.args

        print(f"\n🔧 Tool Call: {function_name}")
        print(f"📝 Args: {json.dumps(dict(args), indent=2)[:200]}...")

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
            types.Content(
                role="user",
                parts=[types.Part(text=REVENUE_AGENT_SYSTEM_PROMPT + "\n\n" + initial_prompt)]
            )
        ]

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"Iteration {iteration}/{max_iterations}")
            print(f"{'='*80}")

            try:
                # Generate response from the model
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=self.conversation_history,
                    config=types.GenerateContentConfig(
                        tools=self.tools,
                        temperature=0.1,  # Low temperature for consistent analysis
                        tool_config=types.ToolConfig(
                            function_calling_config=types.FunctionCallingConfig(
                                mode="AUTO"  # Let model decide when to use tools
                            )
                        )
                    )
                )

                # Add model response to history
                self.conversation_history.append(
                    types.Content(
                        role="model",
                        parts=response.candidates[0].content.parts
                    )
                )

                # Check if there are function calls
                if response.candidates[0].content.parts:
                    has_function_calls = False

                    for part in response.candidates[0].content.parts:
                        # Check for text response
                        if hasattr(part, 'text') and part.text:
                            print(f"\n💬 Agent: {part.text[:500]}...")
                            self.analysis_results.append({
                                "type": "text",
                                "content": part.text,
                                "iteration": iteration
                            })

                        # Check for function call
                        if hasattr(part, 'function_call') and part.function_call:
                            has_function_calls = True
                            function_call = part.function_call

                            # Execute the tool
                            result = self._execute_tool_call(function_call)

                            # Add tool result to conversation
                            self.conversation_history.append(
                                types.Content(
                                    role="user",
                                    parts=[
                                        types.Part(
                                            function_response=types.FunctionResponse(
                                                name=function_call.name,
                                                response={"result": result}
                                            )
                                        )
                                    ]
                                )
                            )

                            self.analysis_results.append({
                                "type": "tool_call",
                                "function": function_call.name,
                                "result": result,
                                "iteration": iteration
                            })

                    # If no function calls, agent is done
                    if not has_function_calls:
                        print("\n✅ Analysis complete - agent has finished")
                        break

                else:
                    print("\n⚠️  No response parts from model")
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
