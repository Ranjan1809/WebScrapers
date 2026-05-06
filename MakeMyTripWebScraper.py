#USED MakeMyTrip JOB APIs for data scraping

import requests
import csv
import time
from html import unescape
from bs4 import BeautifulSoup
from datetime import datetime

JOB_LIST_API_URL = "https://careers.makemytrip.com/api/jobs"
JOB_DETAIL_API_URL = "https://careers.makemytrip.com/api/jobDetails"

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}

def clean_html(text):
    if not text: return "" 
    decoded_text_with_html_tags = unescape(text)
    soup = BeautifulSoup(decoded_text_with_html_tags, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def format_experience(exp_from, exp_to):
    if exp_from and exp_to:
        return f"{exp_from}-{exp_to} years"
    if exp_from:
        return f"{exp_from}+ years"
    return "-"

def get_job_type(is_remote):
    if is_remote == 1:
        return "Remote"
    return "Onsite"   # hybrid not explicitly available

def format_date(date_str):
    if not date_str:
        return ""

    try:
        # input format from API
        dt = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")

        # output format (you can change this)
        return dt.strftime("%d-%m-%Y")

    except Exception:
        return date_str  # fallback if parsing fails

def format_location(city_list):
    if not city_list:
        return ""
    
    return " | ".join(city_list)

# Get all jobs
def fetch_all_jobs():
    res = requests.get(JOB_LIST_API_URL, headers = headers)
    data = res.json()
    return data["allJobs"]

# Get job details
def fetch_job_details(job_id):
    url = f"{JOB_DETAIL_API_URL}?jobId={job_id}"
    res = requests.get(url)
    return res.json()["data"]

def save_csv(data, filename="makemytrip_jobs.csv"):
    keys = [
        "job_name",
        "job_description",
        "posting_date",
        "experience",
        "location",
        "company_name",
        "job_application_link",
        "type"
    ]
 
    with open(filename, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

def build_dataset():
    
    all_jobs = fetch_all_jobs()
    final_data = []

    for job in all_jobs:
        try:

            raw_date = job.get("job_created_timestamp", "")
            formatted_date = format_date(raw_date)
             # FILTER: only 2026 jobs
            if "2026" not in formatted_date:
                continue
                
            job_id = job["job_id"]
            details = fetch_job_details(job_id)

            row = {
                "job_name": job.get("job_title", ""),
                "job_description": clean_html(details.get("job_decription", "")),
                "posting_date": formatted_date,
                "experience": format_experience(
                    job.get("experience_from"),
                    job.get("experience_to")
                ),
                "location": format_location(job.get("location_city")),
                "company_name": job.get("group_company", ""),
                "job_application_link": details.get("applyUrl", ""),
                "type": get_job_type(job.get("is_remote", 0))
            }

            final_data.append(row)

            time.sleep(2)  # safe throttle

        except Exception as e:
            print(f"Error processing {job.get('job_id')}: {e}")

    # return final_data
    return final_data


# ---------------------------
# Main
# ---------------------------
 
if __name__ == "__main__":
    
    print("Fetching jobs...")
    data = build_dataset()
 
    print(f"Total number of jobs for year 2026: {len(data)}")
 
    save_csv(data)
