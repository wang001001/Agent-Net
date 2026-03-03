import json
import uuid
import asyncio

# Import the module under test
from SmartVoyage import main as sv_main

# ---- Dummy classes to mock LLM and prompts ----
class DummyResponseObj:
    def __init__(self, content):
        self.content = content

class DummyChain:
    def __init__(self, response_content):
        self.response_content = response_content
    def invoke(self, _):
        # Return an object with .content attribute
        return DummyResponseObj(self.response_content)

class DummyPrompt:
    def __or__(self, llm):
        # Return a DummyChain that simply echoes a predefined JSON string
        # The JSON will be tailored per test via a global variable
        return DummyChain(sv_main.TEST_CHAIN_RESPONSE)
    def __call__(self, *args, **kwargs):
        return self

# Mock the SmartVoyagePrompts used in the main module
class MockPrompts:
    @staticmethod
    def intent_prompt():
        return DummyPrompt()
    @staticmethod
    def attraction_prompt():
        return DummyPrompt()
    @staticmethod
    def summarize_weather_prompt():
        return DummyPrompt()
    @staticmethod
    def summarize_ticket_prompt():
        return DummyPrompt()

# Replace the real prompts with our mock
sv_main.SmartVoyagePrompts = MockPrompts

# ---- Mock LLM ----
class DummyLLM:
    pass  # No behavior needed; the DummyPrompt ignores it

sv_main.llm = DummyLLM()

# ---- Mock Agent and Network ----
class DummyAgent:
    async def send_task_async(self, task):
        # Simulate a successful response structure
        class DummyStatus:
            state = 'completed'
        class DummyArtifact:
            def __init__(self, text):
                self.text = text
            @property
            def parts(self):
                return [{'text': self.text}]
        class DummyRawResponse:
            status = DummyStatus()
            artifacts = [{'parts': [{'text': 'raw agent result'}]}]
        return DummyRawResponse()

class DummyNetwork:
    def __init__(self):
        self.agents = {
            'WeatherQueryAssistant': DummyAgent(),
            'TicketQueryAssistant': DummyAgent(),
            'TicketOrderAssistant': DummyAgent()
        }
    def get_agent(self, name):
        return self.agents.get(name)

sv_main.agent_network = DummyNetwork()

# ---- Test intent_agent ----

def test_intent_agent_weather():
    # Prepare the JSON string that the dummy chain will return
    sv_main.TEST_CHAIN_RESPONSE = json.dumps({
        "intents": ["weather"],
        "user_queries": {"weather": "今天北京天气怎么样"},
        "follow_up_message": ""
    })
    intents, user_queries, follow_up = sv_main.intent_agent("今天北京天气怎么样")
    assert intents == ["weather"]
    assert user_queries["weather"] == "今天北京天气怎么样"
    assert follow_up == ""

# ---- Test process_user_input routing ----

def test_process_user_input_routes_to_weather_agent(monkeypatch, capsys):
    # Set up dummy response for intent_agent as above
    sv_main.TEST_CHAIN_RESPONSE = json.dumps({
        "intents": ["weather"],
        "user_queries": {"weather": "明天上海的天气怎样"},
        "follow_up_message": ""
    })
    # Reset global state
    sv_main.messages.clear()
    sv_main.conversation_history = ""
    # Run the function
    sv_main.process_user_input("明天上海的天气怎样")
    # Capture printed output
    captured = capsys.readouterr()
    # The final assistant response should contain the dummy summarization result
    assert "raw agent result" in captured.out
    # Verify that messages were recorded
    assert any(m["role"] == "assistant" for m in sv_main.messages)
