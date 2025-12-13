import requests
import json
base='http://localhost:5000'
print('TESTING', base)
try:
    r = requests.post(base+'/api/auth/register', json={'username':'testuser','email':'test@example.com','password':'Password123!'}, timeout=10)
    print('REGISTER', r.status_code, r.text)
except Exception as e:
    print('REGISTER EXCEPTION', e)
try:
    s = requests.Session()
    r = s.post(base+'/api/auth/login', json={'username':'testuser','password':'Password123!'}, timeout=10)
    print('LOGIN', r.status_code, r.text)
    print('COOKIES', s.cookies.get_dict())
except Exception as e:
    print('LOGIN EXCEPTION', e)
