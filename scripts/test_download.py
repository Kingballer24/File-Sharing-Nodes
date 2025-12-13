import requests
import time
import os

base = 'http://localhost:5000'
s = requests.Session()

# wait for server to be ready
for i in range(30):
    try:
        r = s.get(base + '/api/files/list', timeout=3)
        break
    except Exception as e:
        print('Waiting for server...', i, str(e))
        time.sleep(1)
else:
    print('Server did not respond in time')
    raise SystemExit(1)

# login
print('Attempting login...')
r = s.post(base + '/api/auth/login', json={'username':'alice','password':'alice123'})
print('Login response:', r.status_code, r.text)
if r.status_code == 401:
    try:
        data = r.json()
    except Exception:
        data = {}
    if data.get('otp_required'):
        print('OTP required, fetching demo OTP...')
        otp_r = s.get(base + '/api/auth/demo-otp?username=alice')
        print('Demo OTP response:', otp_r.status_code, otp_r.text)
        otp = otp_r.json().get('otp_code')
        print('Using OTP:', otp)
        r = s.post(base + '/api/auth/login', json={'username':'alice','password':'alice123','otp_code':otp})
        print('OTP login response:', r.status_code, r.text)

# list files
r = s.get(base + '/api/files/list')
print('Files list:', r.status_code)
try:
    files = r.json().get('files', [])
except Exception:
    files = []
print('Files currently:', files)

# upload if none
if not files:
    print('Uploading a small test file...')
    files_payload = {'file': ('test.txt', b'hello world test')}
    r = s.post(base + '/api/files/upload', files=files_payload)
    print('Upload response:', r.status_code, r.text)
    time.sleep(1)
    r = s.get(base + '/api/files/list')
    files = r.json().get('files', [])
    print('Files after upload:', files)

if not files:
    print('No files available to download')
    raise SystemExit(1)

file = files[0]
file_id = file['file_id']
filename = file.get('filename') or f'{file_id}.bin'
print('Attempting download for', file_id, filename)

r = s.get(base + f'/api/files/download/{file_id}', stream=True)
print('Download status:', r.status_code)
if r.status_code == 200:
    out_path = os.path.join('.', 'downloaded_' + filename)
    with open(out_path, 'wb') as fh:
        for chunk in r.iter_content(8192):
            if chunk:
                fh.write(chunk)
    print('Saved to', out_path)
else:
    print('Download failed body:', r.text)
    raise SystemExit(1)

print('Test script completed')
