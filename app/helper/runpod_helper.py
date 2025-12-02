import time, requests
import os

RUNPOD_ENDPOINT = f"https://api.runpod.ai/v2/{os.getenv("RUNPOD_ENDPOINT")}/run"
STATUS_URL = f"https://api.runpod.ai/v2/{os.getenv("RUNPOD_ENDPOINT")}/status"


async def submit_job(prompt):
    res = requests.post(RUNPOD_ENDPOINT, headers={"Authorization": os.getenv("RUNPOD_API_KEY")} , json={"input": {"prompt": prompt}}).json()
    return res["id"]


async def check_status(job_id):
    return requests.get(STATUS_URL + "/" + job_id, headers={"Authorization": os.getenv("RUNPOD_API_KEY")}).json()


async def wait_for_output(job_id):
    while True:
        status = await check_status(job_id)
        state = status["status"]

        if state == "COMPLETED":
            return status["output"]
        elif state == "FAILED":
            return {"error": "RunPod job failed"}
        
        time.sleep(2)