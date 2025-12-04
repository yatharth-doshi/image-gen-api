import time, requests
import os

RUNPOD_URL=f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_ENDPOINT')}/run"
STATUS_URL=f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_ENDPOINT')}/status"


async def submit_job(prompt, image_urls: list = None) :
   
    if isinstance(image_urls, str):
        image_urls = [image_urls] 
        
    elif isinstance(image_urls, list):
        pass
    else:
        raise HTTPException(status_code=400, detail="image_urls must be string or list of strings")

    payload = {
        "input": {
            "prompt": prompt,
            "image_urls": image_urls
        }
    }

    res = requests.post(RUNPOD_URL, headers={"Authorization": os.getenv("RUNPOD_API_KEY")} , json = payload).json()
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