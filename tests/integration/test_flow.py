
from fastapi.testclient import TestClient

from palantir import app

client = TestClient(app)



def test_upload_report_flow():

    resp=client.post('/upload',files={'file':('s.csv',b'a,b\n1,2','text/csv')})

    assert resp.status_code==200

    job_id=resp.json()['job_id']

    report=client.get(f'/report/{job_id}', headers={"accept": "application/json"})

    assert report.status_code==200

    assert report.json()['type']=='table'

