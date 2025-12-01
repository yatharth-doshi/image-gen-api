import requests, time

RUNPOD_ENDPOINT = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"
STATUS_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/{}"


def submit_job(prompt):
    res = requests.post(RUNPOD_ENDPOINT, json={"input": {"prompt": prompt}}).json()
    return res["id"]


def check_status(job_id):
    return requests.get(STATUS_URL.format(job_id)).json()


def wait_for_output(job_id):
    while True:
        status = check_status(job_id)
        state = status["status"]

        if state == "COMPLETED":
            return status["output"]
        elif state == "FAILED":
            return {"error": "RunPod job failed"}
        
        time.sleep(2)

@app.post("/generate-image")
def generate_image(prompt: str):
    job_id = submit_job(prompt)
    result = wait_for_output(job_id)
    return result