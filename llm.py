from openai import OpenAI
import os

OPENAI_API_KEY = "sk-bf0c949128694b609cc661ca78fafc30"
model = "deepseek-chat"

# Initialize the OpenAI client
client = OpenAI(
    base_url="https://api.deepseek.com/v1",
    api_key=OPENAI_API_KEY,
)
conversation_history = []

def ask_llm(prompt: str, callback, system_prompt: str) -> str:
    if prompt.strip() == "":
        return ""
    try:
        # Initialize messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]

        conversation_history.append({"role": "user", "content": prompt})
        messages.extend(conversation_history)
        if len(conversation_history) > 10:
            conversation_history.pop(0)

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                callback(chunk.choices[0].delta.content)

        response_text = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": response_text})
        return response_text
    except Exception as e:
        print(f"Error generating completion: {e}")
        return ""
