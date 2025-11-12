import json
import sys
import requests

try:
    from ollama import Client
except Exception as e:
    print('ERROR_IMPORT:', e)
    sys.exit(2)

HOST = 'http://localhost:11434'

# try to list models
try:
    resp = requests.get(HOST + '/v1/models', timeout=5)
    data = resp.json()
    models = [m.get('id') for m in data.get('data', []) if 'id' in m]
except Exception as e:
    print('ERROR_LIST_MODELS:', e)
    models = []

print('MODELS:', models)

# prefer gemma3:4b if present
if 'gemma3:4b' in models:
    model = 'gemma3:4b'
elif models:
    model = models[0]
else:
    model = 'gemma3:latest'

print('TEST_MODEL:', model)

try:
    client = Client(host=HOST)
except Exception as e:
    print('ERROR_CREATE_CLIENT:', e)
    sys.exit(3)

# Minimal prompt
messages = [{'role': 'user', 'content': 'Say hello in one word.'}]

try:
    resp = client.chat(model=model, messages=messages)
    # resp may have .message.content or dict form
    content = None
    try:
        content = resp.message.content
    except Exception:
        try:
            content = resp['message']['content']
        except Exception:
            content = str(resp)
    print('ASSISTANT_RESPONSE:')
    print(content)
except Exception as e:
    print('ERROR_CHAT_CALL:', e)
    sys.exit(4)

print('OK')
