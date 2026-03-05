import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = os.getenv("ACTOR_ID")

job_title = input("Enter job title: ")

url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
payload = {
    "startUrls": [{"url": f"https://www.indeed.com/jobs?q={job_title}"}],
    "maxResults": 100
}
response = requests.post(url, json=payload)
run_data = response.json()
run_id = run_data["data"]["id"]  

status_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}"

print("\n Fetching jobs... Please wait, it may take up to a minute.\n")

while True:
    status_response = requests.get(status_url).json()
    status = status_response["data"]["status"]
    if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
        break   # stop waiting once job finishes
    print("...still fetching, please wait...")
    time.sleep(5)  # wait before checking again


dataset_id = status_response["data"]["defaultDatasetId"]
dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json&token={APIFY_TOKEN}"
data = requests.get(dataset_url).json()

cleaned = []
for job in data:

    desc_html = job.get("descriptionHTML", "")
    soup = BeautifulSoup(desc_html, "html.parser")
    desc_text = soup.get_text(" ", strip=True)

    
    cleaned.append({
        "Job Title": job.get("positionName"),
        "Company": job.get("company"),
        "Location": job.get("location"),
        "Salary": job.get("salary"),
        "Job Type": ", ".join(job.get("jobType", [])) if job.get("jobType") else "",
        "Rating": job.get("rating"),
        "Reviews": job.get("reviewsCount"),
        "Posted": job.get("postedAt"),
        "Apply Link": job.get("externalApplyLink") or job.get("url"),
        "Description": desc_text
    })


df = pd.DataFrame(cleaned)
df.to_excel(f"{job_title}_cleaned_jobs.xlsx", index=False)
print(f"\nSaved cleaned jobs to {job_title}_cleaned_jobs.xlsx")
