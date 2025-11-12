import sys
import requests

try:
    from ollama import Client
except Exception as e:
    print('ERROR_IMPORT:', e)
    sys.exit(2)

model = sys.argv[1] if len(sys.argv) > 1 else 'gemma3:4b'
HOST = 'http://localhost:11434'

print('TRY_MODEL:', model)

# list models
try:
    data = requests.get(HOST + '/v1/models', timeout=5).json()
    models = [m.get('id') for m in data.get('data', []) if 'id' in m]
    print('AVAILABLE_MODELS:', models)
except Exception as e:
    print('ERROR_LIST_MODELS:', e)
    models = []

try:
    client = Client(host=HOST)
except Exception as e:
    print('ERROR_CREATE_CLIENT:', e)
    sys.exit(3)

messages = [{'role': 'user', 'content': 'Hello, reply with one word.'}]

try:
    resp = client.chat(model=model, messages=messages)
    try:
        print('RESPONSE:', resp.message.content)
    except Exception:
        try:
            print('RESPONSE:', resp['message']['content'])
        except Exception:
            print('RESPONSE_RAW:', resp)
except Exception as e:
    print('ERROR_CHAT_CALL:', e)
    sys.exit(4)

print('OK')
