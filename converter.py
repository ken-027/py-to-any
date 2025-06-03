import os
import io
import sys
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from IPython.display import Markdown, display, update_display
import gradio as gr
import subprocess
import requests
from exceptions import RateLimitError

from environment import openai_key, anthropic_key, CLAUDE_MODEL, OPENAI_MODEL, ratelimit_api, request_token

class Converter:
    languages = []

    def __init__(self):
        self.openai = OpenAI(api_key=openai_key)
        self.claude = anthropic.Anthropic(api_key=anthropic_key)
        self.claude_model = CLAUDE_MODEL
        self.openai_model = OPENAI_MODEL
        self.languages = [
            {"name": "C++", "extension": "cpp", "fn": self.execute_cpp},
            {"name": "Javascript", "extension": "js", "fn": self.execute_js},
            {"name": "Php", "extension": "php", "fn": self.execute_php}
        ]


    def __get_name_by_extension(self, extension):
        for lang in self.languages:
            if lang["extension"] == extension:
                return lang["name"]
        return None

    def __get_fn_by_extension(self, extension):
        for lang in self.languages:
            if lang["extension"] == extension:
                return lang["fn"]
        return None

    def get_system_message(self, prog_lang):
        name = self.__get_name_by_extension(prog_lang)
        return (
            f"Respond only with code. Use comments only when absolutely necessary; avoid any form of explanation.\n"
            f"The converted {name} code must produce the exact same output as the original, with the fastest execution possible in that language.\n"
            f"If a function or construct used in the original code does not exist in {name}, replace it with the most efficient and idiomatic equivalent.\n"
            f"If no compatible alternative exists in {name}, return an error explicitly stating the incompatibility."
        )

    def user_prompt_for(self, python, prog_lang):
        name = self.__get_name_by_extension(prog_lang)
        return (
            f"Convert the following Python code to {name}, optimizing for maximum performance and identical output.\n"
            f"Respond only with {name} code. Use minimal comments only when necessary; do not include any explanations.\n"
            f"Ensure correct handling of data types (e.g., integers, floats) to prevent issues such as overflow or loss of precision.\n"
            f"If the Python functionality does not exist in {name}, substitute it with the most efficient equivalent. If no equivalent exists, return an error.\n\n"
            f"{python}"
        )

    def messages_for(self, python, prog_lang):
        return [
            {"role": "system", "content": self.get_system_message(prog_lang)},
            {"role": "user", "content": self.user_prompt_for(python, prog_lang)}
        ]

    def write_output(self, content, prog_lang):
        cleaned_code = (
            content.replace("```cpp", "")
                   .replace("```javascript", "")
                   .replace("```", "")
                   .strip()
        )
        output_path = f"optimized/result.{prog_lang}"
        with open(output_path, "w") as f:
            f.write(cleaned_code)

    def __stream_gpt(self, python, prog_lang):
        stream = self.openai.chat.completions.create(
            model=self.openai_model,
            messages=self.messages_for(python, prog_lang),
            stream=True
        )
        reply = ""
        for chunk in stream:
            fragment = chunk.choices[0].delta.content or ""
            reply += fragment
            yield reply.replace("```cpp\n", "").replace("```javascript\n", "").replace("```", "")

    def __stream_claude(self, python, prog_lang):
        result = self.claude.messages.stream(
            model=self.claude_model,
            max_tokens=2000,
            system=self.get_system_message(prog_lang),
            messages=[{"role": "user", "content": self.user_prompt_for(python, prog_lang)}],
        )
        reply = ""
        with result as stream:
            for text in stream.text_stream:
                reply += text
                yield reply.replace("```cpp\n", "").replace("```javascript\n", "").replace("```", "")

    def optimize(self, python, model, prog_lang):
        try:
            # implementation of ratelimiter here
            response = requests.post(
                ratelimit_api,
                json={"token": request_token}
            )
            status_code = response.status_code

            if (status_code == 429):
                raise RateLimitError()

            elif (status_code != 201):
                raise Exception(f"Unexpected status code from rate limiter: {status_code}")


            if model == "GPT":
                stream = self.__stream_gpt(python, prog_lang)
            elif model == "Claude":
                stream = self.__stream_claude(python, prog_lang)
            else:
                raise ValueError("Unknown model")

            for output in stream:
                yield output

        except RateLimitError as rle:
            yield rle.message

        except Exception as e:
            yield f"Something went wrong! {e}"

    def execute_python(self, code):
        try:
            output = io.StringIO()
            sys.stdout = output
            exec(code, {})
        finally:
            sys.stdout = sys.__stdout__
        return output.getvalue()

    def execute_cpp(self, code):
        try:
            compile_cmd = ["clang++", "-std=c++17", "-O3", "-ffast-math", "-o", "optimized/output.exe", "optimized/result.cpp"]
            # compile_cmd = ["clang++", "-ffast-math", "-std=c++17", "-o", "optimized", "optimized/result.cpp"]
            subprocess.run(compile_cmd, check=True, text=True, capture_output=True)
            run_result = subprocess.run(["./optimized/output.exe"], check=True, text=True, capture_output=True)
            return run_result.stdout
        except Exception as e:
            return f"An error occurred:\n{e.stderr}"

    def execute_js(self, code):
        try:
            result = subprocess.run(["node", "optimized/result.js"], check=True, text=True, capture_output=True)
            return result.stdout
        except Exception as e:
            return f"An error occurred:\n{e.stderr}"

    def execute_php(self, code):
        try:
            result = subprocess.run(["php", "optimized/result.php"], check=True, text=True, capture_output=True)
            return result.stdout
        except Exception as e:
            return f"An error occurred:\n{e.stderr}"

    def handle_execution(self, code, prog_lang):
        self.write_output(code, prog_lang)
        execute_fn = self.__get_fn_by_extension(prog_lang)
        if not execute_fn:
            return "Execution function not found for this language."
        return execute_fn(code)
