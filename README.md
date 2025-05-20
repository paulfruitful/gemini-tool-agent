# Gemini Tool Agent

A lightweight, tool-aware Gemini agent to handle structured prompts and tool usage in conversations.

## Overview

Gemini Tool Agent is a Python library that provides a simple interface for creating tool-aware agents powered by Google's Gemini AI models. It enables developers to define custom tools with structured input schemas and seamlessly integrate them into conversational flows.

## Features

- Tool-aware conversation handling
- Structured prompt processing
- Automatic context management
- JSON response parsing
- Conversation history tracking

## Installation

```bash
pip install gemini-tool-agent
```

## Requirements

- Python 3.8 or higher
- Google Generative AI Python SDK (google-genai >= 0.3.2)

## Usage

```python
from gemini_tool_agent.agent import Agent

# Initialize the agent with your API key
agent = Agent(key="your-api-key")

# Define your tools
agent.tools = [
    {
        "name": "save_note",
        "description": "Save a note to the database",
        "input_schema": {
            "title": "string",
            "content": "string"
        }
    }
]

# Process a query that might use tools
response = agent.process_query("Save a note about AI agents")
print(response)
```

## Response Format

The agent returns a structured response in JSON format:

```json
{
  "needs_tool": true,
  "tool_name": "save_note",
  "needs_direct_response": true,
  "direct_response_first": false,
  "reasoning": "The query explicitly asks to save a note, which requires the save_note tool",
  "direct_response": "AI agents are software entities that can perform tasks autonomously..."
}
```

## Advanced Usage

You can access the conversation history:

```python
# Get the conversation history
history = agent.history
```

1### Tool Parameter Extraction

After identifying that a tool needs to be used, you can extract parameters from the conversation:

```python
# First process the query to determine if a tool is needed
response = agent.process_query("Save a note titled 'AI Agents' with content about machine learning")

# If a tool is needed, extract the parameters
if response.get("needs_tool", False):
    tool_name = response.get("tool_name")
    tool_params = agent.process_use_tool(tool_name)
    
    # Now you can use the extracted parameters to execute the tool
    print(tool_params)
    # Output: {'tool_name': 'save_note', 'input': {'title': 'AI Agents', 'content': '...'}}  
```

### Optimized Response Generation

The agent automatically handles large prompts for memory efficiency:

```python
# For direct usage (normally used internally by the agent)
response_text = agent.generate_response(large_prompt)

# The method automatically optimizes prompts over 10,000 characters by:
# - Trimming conversation history to the most recent 15 lines when needed
# - Truncating large direct responses while preserving start and end content
```

## License

MIT

## Author

Paul Fruitful (fruitful2007@outlook.com)