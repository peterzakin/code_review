import os
import requests
from openai import OpenAI

def ask_openai(prompt, model="gpt-4o-2024-08-06"):
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

github_token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPOSITORY")
ref = os.getenv("GITHUB_REF")

pull_request_number = ref.split('/')[-2]
files_url = f"https://api.github.com/repos/{repo}/pulls/{pull_request_number}/files"
headers = {
    "Authorization": f"Bearer {github_token}",
    "Accept": "application/vnd.github.v3+json",
}

response = requests.get(files_url, headers=headers)
if response.status_code != 200:
    print(f"working on pull_request_number: {pull_request_number}, files_url: {files_url}")
    print(f"Failed to fetch files: {response.status_code} - {response.text}")
    exit(1)

files = response.json()

# Fetch diffs and full contents for each file
diffs = []
full_files = []
for file in files:
    filename = file["filename"]
    patch = file.get("patch", "")
    raw_url = file["raw_url"]

    print(f"Fetching full content for file: {filename}")
    file_response = requests.get(raw_url, headers=headers)
    if file_response.status_code == 200:
        full_content = file_response.text
    else:
        print(f"Failed to fetch full content for {filename}")
        full_content = "Error fetching file content."

    # Append diff and full file content
    diffs.append(f"File: {filename}\nDiff:\n{patch}\n")
    full_files.append(f"File: {filename}\nFull Content:\n{full_content}\n")

# Combine diffs and full files into a single prompt
diffs_text = "\n\n".join(diffs)
full_files_text = "\n\n".join(full_files)

review_prompt = (
    "You are a code reviewer. Review the following changes and provide comments "
    "on improvements and potential issues.\n\n"
    f"### Diffs:\n{diffs_text}\n\n"
    f"### Full File Contents:\n{full_files_text}"
)

response = ask_openai(review_prompt)
comments_url = f"https://api.github.com/repos/{repo}/issues/{pull_request_number}/comments"
data = {"body": response}

response = requests.post(comments_url, headers=headers, json=data)
if response.status_code == 201:
    print("Comments posted successfully!")
else:
    print(f"Failed to post comments: {response.status_code} - {response.text}")
