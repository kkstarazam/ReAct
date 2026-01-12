# ReAct Agent

A Python-based ReAct (Reasoning and Acting) agent that follows the thought → action → observation → thought pattern using OpenRouter for LLM capabilities.

## Features

- **4 Built-in Tools:**
  - 🧮 **Calculate** - Perform mathematical calculations
  - ⏰ **Time** - Get current date and time
  - 🌤️ **Weather** - Get weather information for any city
  - 📚 **Wikipedia Search** - Search Wikipedia articles

- **ReAct Loop Architecture:**
  - Structured thought → action → observation cycle
  - Error handling with automatic retry (max 2 attempts)
  - JSON-based LLM output parsing
  - Loop breaks when action is null (final answer ready)

- **Web Interface:**
  - Clean chat UI using Pico CSS
  - Real-time message display
  - Loading indicators
  - User/agent message differentiation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set OpenRouter API Key

Get your API key from [OpenRouter](https://openrouter.ai/) and set it as an environment variable:

**Windows (PowerShell):**
```powershell
$env:OPENROUTER_API_KEY="your-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENROUTER_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

### 3. Run the Application

```bash
python react_agent.py
```

The server will start at `http://localhost:5000`

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Type your question in the input field
3. The agent will process your request using the ReAct loop
4. View the final answer in the chat interface

### Example Queries

- "What is 25 * 4 + 100?"
- "What time is it?"
- "What's the weather in Paris?"
- "Tell me about Python programming language"

## Architecture

### Backend (`react_agent.py`)

- **ReAct Loop:** Main processing loop that handles thought-action-observation cycles
- **Tool Functions:** 4 tools (calculate, time, weather, wikipedia_search)
- **LLM Integration:** OpenRouter API with structured JSON responses
- **Error Handling:** Catches malformed outputs and retries up to 2 times
- **Flask API:** Exposes `/chat` endpoint for frontend communication

### Frontend (`index.html`)

- **Pico CSS Framework:** Modern, lightweight styling
- **Chat Interface:** Message container with user/agent differentiation
- **API Integration:** Fetches responses from `/chat` endpoint
- **Loading States:** Visual feedback during processing

## LLM Output Format

The LLM responds in strict JSON format:

**During processing:**
```json
{
  "thought": "reasoning about what to do",
  "action": "tool_name",
  "action_input": "input for the tool"
}
```

**Final answer:**
```json
{
  "thought": "reasoning about being done",
  "action": null,
  "action_input": null,
  "final_answer": "the answer to show the user"
}
```

## Configuration

- **Model:** `meta-llama/llama-3.1-8b-instruct:free` (configurable in code)
- **Max Iterations:** 10 (prevents infinite loops)
- **Max Errors:** 2 (malformed JSON attempts)
- **Port:** 5000 (configurable in code)

## File Structure

```
ReAct/
├── react_agent.py      # Main backend with ReAct loop and tools
├── index.html          # Frontend chat interface
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Troubleshooting

**API Key Issues:**
- Ensure `OPENROUTER_API_KEY` is set before running the application
- Check that your API key is valid and has credits

**Port Already in Use:**
- Change the port in `react_agent.py`: `app.run(debug=True, port=5001)`

**Tool Errors:**
- Weather API requires internet connection
- Wikipedia API requires internet connection
- Calculate tool uses safe eval (limited to mathematical operations)

## License

MIT
