from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
base_config = types.GenerateContentConfig(
    system_instruction="Keep your response short"
)

chat = client.chats.create(model="gemini-2.5-flash",config=base_config)


def get_ai_response(user_input):
    # response = client.models.generate_content(
    #     model="gemini-2.5-flash",
    #     contents=user_input,
    #     config=base_config, )
    response = chat.send_message(user_input)
    for message in chat.get_history():
        print(f'role - {message.role}', end=": ")
        print(message)
        # print(message.parts[0].text)
    return response.text
