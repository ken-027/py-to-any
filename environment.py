import os
from dotenv import load_dotenv

load_dotenv(override=True)

openai_key= os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
request_token = os.getenv('REQUEST_TOKEN')
ratelimit_api = os.getenv('RATELIMIT_API')


OPENAI_MODEL = "gpt-4o-mini"
CLAUDE_MODEL = "claude-3-haiku-20240307"

css = """
.python {background-color: #306998;}
.cpp {background-color: #050;}
.php {background-color: #cb7afa;}
.js {background-color: #f4ff78;}
"""

python_code = """
person = {
    "name": "John Doe",
    "age": 28
}

print(person)
"""
