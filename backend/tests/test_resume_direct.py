import json
import urllib.request

def test_resume(exec_id):
    url = f"http://localhost:8000/executions/{exec_id}/resume"
    data = json.dumps({"decision": "APPROVED"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            print(f"Resumed execution #{exec_id}:", res)
    except Exception as e:
        print("Error resuming execution:", e)

if __name__ == "__main__":
    test_resume(22)
