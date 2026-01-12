import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env file from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
CORS(app)

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt for the LLM
SYSTEM_PROMPT = """You are a helpful AI assistant with access to exactly 4 tools: calculate, time, weather, and wikipedia_search.

You MUST ALWAYS respond in valid JSON format. No other text outside the JSON is allowed.

When you need to use a tool, respond with:
{"thought": "your reasoning", "action": "tool_name", "action_input": "input for tool"}

When you have the final answer, respond with:
{"thought": "I now have the final answer", "action": null, "action_input": null, "final_answer": "your answer to the user"}

Available tools:
1. calculate - Perform math calculations. Input: string expression (e.g., "2 + 2")
2. time - Get current date and time. Input: null
3. weather - Get weather for a city. Input: city name as string
4. wikipedia_search - Search Wikipedia. Input: article title as string

IMPORTANT: Your response must be ONLY valid JSON. Start with { and end with }."""


# Tool implementations
def calculate(expression):
    """Perform mathematical calculations"""
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


def time_tool():
    """Get current date and time"""
    now = datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


def weather(city):
    """Get weather for a city using wttr.in API"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current_condition", [{}])[0]
        temp_c = current.get("temp_C", "N/A")
        temp_f = current.get("temp_F", "N/A")
        weather_desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
        
        return f"Weather in {city}: {weather_desc}, Temperature: {temp_c}°C ({temp_f}°F)"
    except Exception as e:
        return f"Error fetching weather: {str(e)}"


def wikipedia_search(title):
    """Search Wikipedia for a summary"""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        article_title = data.get("title", "N/A")
        extract = data.get("extract", "No summary available")
        
        return f"Title: {article_title}\n\nSummary: {extract}"
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


# Tool registry
TOOLS = {
    "calculate": calculate,
    "time": time_tool,
    "weather": weather,
    "wikipedia_search": wikipedia_search
}


def call_llm(messages):
    """Call OpenRouter API with the message history"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"LLM API error: {str(e)}")


def react_loop(user_message):
    """Main ReAct loop that processes user queries"""
    # Initialize message history with system prompt and user message
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    error_count = 0
    max_errors = 2
    
    while iteration < max_iterations:
        iteration += 1
        
        try:
            # Call LLM
            llm_response = call_llm(messages)
            
            # Try to parse JSON response
            try:
                response_json = json.loads(llm_response)
                error_count = 0  # Reset error count on successful parse
            except json.JSONDecodeError as e:
                error_count += 1
                
                if error_count >= max_errors:
                    return "I apologize, but I'm having trouble processing your request. Please try rephrasing your question."
                
                # Add error message to help LLM correct itself
                error_msg = f"Error: Your response was not valid JSON. Please respond with ONLY valid JSON in the exact format specified. Error details: {str(e)}"
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({"role": "user", "content": error_msg})
                continue
            
            # Extract fields from response
            thought = response_json.get("thought", "")
            action = response_json.get("action")
            action_input = response_json.get("action_input")
            final_answer = response_json.get("final_answer")
            
            # Check if we have a final answer
            if action is None:
                return final_answer if final_answer else "I couldn't determine an answer."
            
            # Execute the action
            if action not in TOOLS:
                error_msg = f"Error: Unknown tool '{action}'. Available tools are: {', '.join(TOOLS.keys())}"
                messages.append({"role": "assistant", "content": llm_response})
                messages.append({"role": "user", "content": error_msg})
                continue
            
            # Call the tool
            tool_function = TOOLS[action]
            if action == "time":
                observation = tool_function()
            else:
                observation = tool_function(action_input)
            
            # Add observation to message history
            messages.append({"role": "assistant", "content": llm_response})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            
        except Exception as e:
            return f"An error occurred: {str(e)}"
    
    return "Maximum iterations reached. Please try a simpler question."


@app.route('/')
def index():
    """Serve the frontend HTML"""
    return send_from_directory('.', 'index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """API endpoint for chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        print(f"Received message: {user_message}")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Run the ReAct loop
        response = react_loop(user_message)
        
        print(f"Sending response: {response}")
        
        return jsonify({"response": response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    if not OPENROUTER_API_KEY:
        print("Warning: OPENROUTER_API_KEY environment variable not set!")
        print("Please set it with: $env:OPENROUTER_API_KEY='your-api-key'")
    
    print("\n" + "="*60)
    print("ReAct Agent Server Starting...")
    print("="*60)
    print("What can I help you with: Calculate, Time, Get weather, or Wikipedia.")
    print("\nOpen http://localhost:5000 in your browser")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)
