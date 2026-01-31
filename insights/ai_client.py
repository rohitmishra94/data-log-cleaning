import streamlit as st
import os
from google import genai
from openai import OpenAI
from typing import Dict, Any, Generator
from dotenv import load_dotenv

load_dotenv()


def get_ai_response(prompt: str) -> Dict[str, Any]:
    try:
        gemini_key_1 = st.secrets.get("GEMINI_API_KEY", None)
    except:
        gemini_key_1 = None

    try:
        gemini_key_2 = st.secrets.get("GEMINI_API_KEY_2", None)
    except:
        gemini_key_2 = None

    try:
        openai_key = st.secrets.get("OPENAI_API_KEY", None)
    except:
        openai_key = None

    gemini_keys = [
        gemini_key_1 or os.environ.get("GEMINI_API_KEY"),
        gemini_key_2 or os.environ.get("GEMINI_API_KEY_2"),
    ]
    gemini_keys = [k for k in gemini_keys if k]
    openai_key = openai_key or os.environ.get("OPENAI_API_KEY")

    for i, gemini_key in enumerate(gemini_keys):
        try:
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt
            )
            return {"success": True, "content": response.text, "provider": f"gemini_{i + 1}"}
        except Exception as e:
            if i == len(gemini_keys) - 1 and not openai_key:
                return {"success": False, "error": f"All Gemini keys failed: {str(e)}"}

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            return {"success": True, "content": response.choices[0].message.content, "provider": "openai"}
        except Exception as e:
            return {"success": False, "error": f"OpenAI failed: {str(e)}"}

    return {"success": False, "error": "No API keys configured in st.secrets"}


def get_ai_response_stream(prompt: str) -> Generator[Dict[str, Any], None, None]:
    try:
        gemini_key_1 = st.secrets.get("GEMINI_API_KEY", None)
    except:
        gemini_key_1 = None

    try:
        gemini_key_2 = st.secrets.get("GEMINI_API_KEY_2", None)
    except:
        gemini_key_2 = None

    try:
        openai_key = st.secrets.get("OPENAI_API_KEY", None)
    except:
        openai_key = None

    gemini_keys = [
        gemini_key_1 or os.environ.get("GEMINI_API_KEY"),
        gemini_key_2 or os.environ.get("GEMINI_API_KEY_2"),
    ]
    gemini_keys = [k for k in gemini_keys if k]
    openai_key = openai_key or os.environ.get("OPENAI_API_KEY")

    for i, gemini_key in enumerate(gemini_keys):
        try:
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt
            )
            for chunk in response:
                if chunk.text:
                    yield {"success": True, "chunk": chunk.text, "provider": f"gemini_{i + 1}"}
            return
        except Exception as e:
            if i == len(gemini_keys) - 1 and not openai_key:
                yield {"success": False, "error": f"All Gemini keys failed: {str(e)}"}
                return

    if openai_key:
        try:
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"success": True, "chunk": chunk.choices[0].delta.content, "provider": "openai"}
            return
        except Exception as e:
            yield {"success": False, "error": f"OpenAI streaming failed: {str(e)}"}
            return

    yield {"success": False, "error": "No API keys configured in st.secrets"}
