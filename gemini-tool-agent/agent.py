from google import genai
import re
import json
      
class Agent:
    def __init__(self,key, model="gemini-2.0-flash-lite"):
        self.model = model
        self.tools=None
        self.history = []
        self.ai=genai.Client(api_key=key)


    def find_tool(self, tool_name):
        for tool in self.tools:
            if tool["name"] == tool_name:
                return tool
        return None
        

    def process_query(self, query):
        
        tools_str = ', '.join([f"{tool['name']}: {tool['description']}" for tool in self.tools])
        
        conversation_context = self.history[-10:] if len(self.history) >= 10 else self.history
        
        prompt = f"""
        QUERY: {query}
        
        AVAILABLE TOOLS: {tools_str}
        
        CONVERSATION HISTORY: {conversation_context}
        
        INSTRUCTIONS:
        1. Analyze if the query requires using any of the available tools, requires a direct response, or both.
        2. Consider the conversation history to understand the context of the current query.
        3. For hybrid requests (like "narrate X and save it"), identify both the information request and the tool action.
        4. For follow-up queries, determine if they relate to previous tool usage or direct responses.
        5. Respond in the following JSON format:
           {{
             "needs_tool": true/false,
             "tool_name": "tool_name_if_needed",
             "needs_direct_response": true/false,
             "direct_response_first": true/false,
             "reasoning": "brief explanation of your decision that considers conversation history"
           }}
        6. If no tool is needed, set "needs_tool" to false and leave "tool_name" empty.
        7. If a direct response is needed, set "needs_direct_response" to true.
        8. For hybrid requests, set both flags to true and use "direct_response_first" to indicate order.
        
        Your structured response:
        """
        
        response_text = self.generate_response(prompt)
        parsed_response = self.extract_json(response_text)
        
        # If a direct response is needed, generate it and add to the response dict
        if parsed_response.get("needs_direct_response", False):
            # Include conversation history in the direct response prompt
            direct_prompt = f"""
            You are a helpful assistant responding to the following query:
            
            QUERY: {query}
            
            CONVERSATION HISTORY: {conversation_context}
            
            Please provide a comprehensive and accurate response that considers the conversation history.
            If the query mentions saving information or using tools, focus on providing the information itself,
            as the tool actions will be handled separately.
            """
            
            direct_response = self.generate_response(direct_prompt)
            
            parsed_response["direct_response"] = direct_response
            
            self.history.append({"role": "assistant", "content": direct_response})
        
        return parsed_response
        
    def extract_json(self, text):
        """Extract JSON content from text using regex."""
        
      
        try:
            match = re.search(r'{.*}', text, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse JSON", "raw_text": json_str}
            else:
                return {"error": "No JSON found in response", "raw_text": text}
        except Exception as e:
            return {"error": str(e), "raw_text": text}

    def process_use_tool(self, tool_name):
     tool = self.find_tool(tool_name)
     if tool:
        prompt = f"""
        # Tool Calling Task
        
        ## Context
        You are analyzing a conversation to extract parameters for a tool call.
        
        ## Tool Information
        - Name: {tool["name"]}
        - Description: {tool["description"]}
        - Input Schema: {tool["input_schema"]}
        
        ## Previous Conversation: {self.history[-7:] if len(self.history) >= 7 else self.history}

            ## Instructions
            1. Carefully analyze the conversation above
            2. Extract all necessary parameters required by the tool's input schema
            3. Format values appropriately according to their expected types
            4. Do not add any parameters not specified in the schema
            5. If a required parameter is missing from the conversation, use a reasonable default or placeholder
            
            ## Response Format
            Respond ONLY with a valid JSON object in this exact format:
            {{
                "tool_name": "{tool["name"]}",
                "input": {{
                    "parameter1": "value1",
                    "parameter2": "value2",
                    ... 
                }}
            }}
            """
            
        response = self.generate_response(prompt)
        parsed_response = self.extract_json(response)
        print("Tool Call",parsed_response)
            
        return parsed_response
     else:
            return {"error": f"Tool '{tool_name}' not found"}

    def generate_response(self, prompt):
        if len(prompt) > 10000:  # Approximate threshold for long prompts
            print("Warning: Large prompt detected, optimizing for memory efficiency")
            
            if "CONVERSATION HISTORY" in prompt:
                parts = prompt.split("CONVERSATION HISTORY:")
                before_history = parts[0]
                after_parts = parts[1].split("\n\n", 1)
                
                history_part = after_parts[0]
                remaining_part = after_parts[1] if len(after_parts) > 1 else ""
                
                if len(history_part) > 5000:
                    history_lines = history_part.split("\n")
                    optimized_history = "\n".join(history_lines[-15:])  # Keep last 15 lines
                    prompt = before_history + "CONVERSATION HISTORY: " + optimized_history + "\n\n" + remaining_part
            elif "direct_response" in prompt and len(prompt) > 8000:
                print("Optimizing large direct response in prompt")
                start_part = prompt[:3000]
                end_part = prompt[-3000:]
                prompt = start_part + "\n...[content truncated for memory efficiency]...\n" + end_part
        
        response = self.ai.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return response.text
