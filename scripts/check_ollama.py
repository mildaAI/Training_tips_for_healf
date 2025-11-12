import sys

try:
    from ollama import Client
except Exception as e:
    print('ERROR_IMPORT:', e)
    sys.exit(2)

try:
    c = Client(host='http://localhost:11434')
    print('CLIENT_CREATED')
except Exception as e:
    print('ERROR_CREATE_CLIENT:', e)
    sys.exit(3)

# Try a light chat call with an empty prompt? We avoid heavy calls.
# Instead, try to access a simple client attribute or a /ping if available.
try:
    # Some Client implementations may expose a .host attribute
    print('CLIENT_HOST:', getattr(c, 'host', 'unknown'))
except Exception as e:
    print('ERROR_INSPECT_CLIENT:', e)
    sys.exit(4)

print('OK')
