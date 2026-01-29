import openai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=api_key)

# Test non-streaming
print("Testing non-streaming responses API...")
try:
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": "Say hello"}],
    )
    print(f"Response type: {type(response)}")
    print(f"Response dir: {[attr for attr in dir(response) if not attr.startswith('_')]}")
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test streaming
print("\n\nTesting streaming responses API...")
try:
    stream = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": "Say hello"}],
        stream=True,
    )
    print(f"Stream type: {type(stream)}")

    for i, event in enumerate(stream):
        print(f"\nEvent {i}:")
        print(f"  Type: {type(event)}")
        print(f"  Attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
        print(f"  Event: {event}")
        if i > 5:  # Only print first few events
            break
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
