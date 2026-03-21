import requests
r = requests.post('http://localhost:5000/ask', json={'query':'peace','persona':'adult'}, timeout=10)
print('status', r.status_code)
print('body', r.text)
