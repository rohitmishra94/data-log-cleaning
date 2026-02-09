"""
Tools for autonomous agent to execute Python code and save successful scripts.
"""
import subprocess
import json
import os
from datetime import datetime
from typing import Dict, Any
from agents import function_tool


@function_tool
def execute_python(code: str) -> Dict[str, Any]:
    """
    Execute Python code safely and return the output.

    Args:
        code: Python code to execute

    Returns:
        Dict with success status, output/error, and execution metadata
    """
    try:
        # Create a temporary file to execute
        temp_file = f"/tmp/agent_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

        with open(temp_file, 'w') as f:
            f.write(code)

        # Execute the code with timeout
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd='/Users/rm/Downloads/projects/data-log-cleaning'  # Set working directory
        )

        # Clean up temp file
        os.remove(temp_file)

        if result.returncode == 0:
            # Print to console AND save to file
            if result.stdout:
                print(f"\n{'='*60}")
                print("ANALYSIS OUTPUT:")
                print('='*60)
                print(result.stdout)
                print('='*60)

                # Also append to results file
                try:
                    with open("/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/analysis_results.txt", 'a') as f:
                        f.write("\n" + "="*60 + "\n")
                        f.write("ANALYSIS RESULT:\n")
                        f.write("="*60 + "\n")
                        f.write(result.stdout)
                        f.write("\n")
                except:
                    pass

            return {
                "success": True,
                "output": result.stdout,
                "error": None,
                "return_code": result.returncode
            }
        else:
            # Print errors to console
            if result.stderr:
                print(f"\n{'='*60}")
                print("ERROR:")
                print('='*60)
                print(result.stderr)
                print('='*60)

            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": "Code execution timed out after 120 seconds",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "output": None,
            "error": str(e),
            "return_code": -1
        }


@function_tool
def save_successful_script(name: str, code: str, description: str = "") -> Dict[str, Any]:
    """
    Save a successful analysis script for future reuse.

    Args:
        name: Name for the script (without .py extension)
        code: Python code to save
        description: Optional description of what the script does

    Returns:
        Dict with success status and file path
    """
    try:
        # Ensure name is filesystem safe
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-'))

        script_dir = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/saved_scripts"
        script_path = os.path.join(script_dir, f"{safe_name}.py")

        # Save the script
        with open(script_path, 'w') as f:
            if description:
                f.write(f'"""\n{description}\n"""\n\n')
            f.write(code)

        # Save metadata
        metadata_path = os.path.join(script_dir, f"{safe_name}_metadata.json")
        metadata = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "file_path": script_path
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            "success": True,
            "file_path": script_path,
            "metadata_path": metadata_path,
            "message": f"Script saved successfully as {safe_name}.py"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save script: {str(e)}"
        }


def list_saved_scripts() -> Dict[str, Any]:
    """
    List all saved scripts with their metadata.

    Returns:
        Dict with list of scripts and their information
    """
    try:
        script_dir = "/Users/rm/Downloads/projects/data-log-cleaning/autonomous_agent/saved_scripts"

        scripts = []
        for file in os.listdir(script_dir):
            if file.endswith('_metadata.json'):
                metadata_path = os.path.join(script_dir, file)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    scripts.append(metadata)

        return {
            "success": True,
            "scripts": scripts,
            "count": len(scripts)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "scripts": [],
            "count": 0
        }
