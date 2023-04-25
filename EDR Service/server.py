import functools

import uvicorn
from fastapi import FastAPI, UploadFile, requests, HTTPException
from pymongo import MongoClient
import models
import requests

app = FastAPI()

@functools.lru_cache()
def mongo_data_collection():
    client = MongoClient('mongodb://mongo:27017/',
                         username='root',
                         password='example'
                         )

    db = client['data']
    collection = db['verdicts']

    return collection


collection = mongo_data_collection()


def get_verdict_item(hash):
    item = collection.find_one({'hash': hash})
    if item is None:
        verdict_item = models.VerdictItem(hash=hash, risk_level=-1)
    else:
        verdict_item = item
        verdict_item.pop("_id")

    return verdict_item


@app.post("/events/")
async def events(event: models.Event):
    # file_verdict = get_verdict_item(event.file.file_hash)
    # process_verdict = get_verdict_item(event.last_access.hash)
    #
    # verdict = models.Verdict(file=file_verdict, process=process_verdict)
    # return verdict
    response = {}

    for key, md5 in [('file', event.file.file_hash), ('process', event.last_access.hash)]:
        data = collection.find_one({"hash": md5})
        if data is not None:
            risk_level = data['risk_level']
        else:
            risk_level = -1

        response[key] = models.VerdictItem(hash=md5, risk_level=risk_level)

    return models.Verdict(**response)

@app.post("/scan_file/")
async def scan_file(file: UploadFile):
    file_content = await file.read()

    url = "https://beta.nimbus.bitdefender.net/liga-ac-labs-cloud/blackbox-scanner/"
    try:
        black_box_api_response = requests.post(url, files={"file": ("file.txt", file_content)}).json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    md5 = black_box_api_response['hash']
    risk_level = black_box_api_response['risk_level']
    verdict = models.VerdictItem(hash=md5, risk_level=risk_level)
    collection.insert_one(verdict.dict())
    print(f'Item created, {verdict=}')
    return verdict


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host='0.0.0.0')
