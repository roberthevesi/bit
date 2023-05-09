import functools
import os
from prometheus_fastapi_instrumentator import Instrumentator

import uvicorn
from fastapi import FastAPI, UploadFile, requests, HTTPException
from pymongo import MongoClient
import models
import requests
import aiohttp
import redis
import json

MONGO_URL = os.getenv('MONGO_URL') or "mongodb://root:example@localhost:27017"

app = FastAPI()

Instrumentator().instrument(app).expose(app)

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


redis_client = redis.Redis(host='redis', port=6379, db=0)


@app.post("/events/")
async def events(event: models.Event):
    response = {}

    for key, md5 in [('file', event.file.file_hash), ('process', event.last_access.hash)]:
        redis_result = redis_client.get(md5)
        if redis_result is None:
            data = collection.find_one({"hash": md5})
            if data is not None:
                data.pop('_id', None)
                redis_client.set(md5, json.dumps(data))
        else:
            data = json.loads(redis_result)

        if data is not None:
            risk_level = data['risk_level']
        else:
            risk_level = -1

        response[key] = models.VerdictItem(hash=md5, risk_level=risk_level)

    return models.Verdict(**response)


async def scan_file_async(file_content):
    url = "https://beta.nimbus.bitdefender.net/liga-ac-labs-cloud/blackbox-scanner/"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data={"file": file_content}) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail=f"Request failed with status code {response.status}")
            response_json = await response.json()
            md5 = response_json['hash']
            risk_level = response_json['risk_level']
            verdict = models.VerdictItem(hash=md5, risk_level=risk_level)
            collection.insert_one(verdict.dict())
            print(f'Item created, {verdict=}')
            return verdict


@app.post("/scan_file/")
async def scan_file(file: UploadFile):
    file_content = await file.read()

    url = "https://beta.nimbus.bitdefender.net/liga-ac-labs-cloud/blackbox-scanner/"

    # async
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data={"file": file_content}) as response:
                json_response = await response.json()
                md5 = json_response['hash']
                risk_level = json_response['risk_level']
                verdict = models.VerdictItem(hash=md5, risk_level=risk_level)
                collection.insert_one(verdict.dict())
                print(f'Item created, {verdict=}')
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # # sync
    # try:
    #     black_box_api_response = requests.post(url, files={"file": ("file.txt", file_content)}).json()
    #     md5 = black_box_api_response['hash']
    #     risk_level = black_box_api_response['risk_level']
    #     verdict = models.VerdictItem(hash=md5, risk_level=risk_level)
    #     collection.insert_one(verdict.dict())
    #     print(f'Item created, {verdict=}')
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=str(e))

    return verdict


if __name__ == "__main__":
    uvicorn.run(app, port=8000, host='0.0.0.0')
