from fastapi import FastAPI
import subprocess
from livekit import api
import json
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    python_path = r"C:\Users\lenovo\Desktop\Sample\myenv\Scripts\python.exe"
    subprocess.Popen([python_path, "agent3.py", "start"])
    print("Agent started")
    yield
    print("Agent stopped")

app = FastAPI(lifespan=lifespan)

@app.get("/api")
async def get_token():
    user_id = "005fK000001oNIbQAM"
    access_token = "00DfK000008J5xC!AQEAQBIlAT05Ei9oAzvH3Xc8l3ol.FpZVy1.keQb.AZwJXJx6UFNx1ZTU8NAJfBu3xSfG41b.0g44LVYkqJGqG9pSL8.XO.M"
    url = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com"
    token = api.AccessToken("APIhmfPSNUrj8vm", "CVyV01Uaa3KYEKofgiEZv1TLGBzf1plggM2dsE0pJDe") \
        .with_identity("visits-agent") \
        .with_name("Visit Agent") \
        .with_metadata(json.dumps({
            "user_id": user_id,
            "access_token": access_token,
            "url": url
        })) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room="my-room"
        ))
    return token.to_jwt()