import time
import yaml
from flask import Flask, request, jsonify, render_template
from julep import Julep
from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'Software0923!'  # Replace with a secure random string

# Load environment variables
load_dotenv()

# Initialize Julep client with API key from environment variable
client = Julep(api_key=os.getenv("JULEP_API_KEY"))

# Create the agent once at the start
try:
    agent = client.agents.create(
        name="Meeting Summarizer",
        model="gpt-4o",
        about="You summarize meetings and extract key action items."
    )
    print("Agent created successfully.")
except Exception as e:
    print(f"Error creating agent: {str(e)}")
    agent = None

# Confluence API credentials
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")  # Example: 'https://14soulemanesow.atlassian.net/wiki'
CONFLUENCE_API_USERNAME = os.getenv("CONFLUENCE_API_USERNAME")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

# Jira API credentials
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")  # Example: 'https://14soulemanesow.atlassian.net'
JIRA_API_USERNAME = os.getenv("JIRA_API_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/summarizer')
def summarizer():
    return render_template('summarizer.html')


@app.route('/summarize', methods=['POST'])
def summarize_meeting():
    if agent is None:
        return jsonify({'error': 'Agent not created'}), 500

    data = request.json
    transcript = data.get('transcript')

    if not transcript:
        return jsonify({'error': 'No transcript provided'}), 400

    # Escape and format the transcript for YAML
    escaped_transcript = transcript.replace('"', '\\"').replace('\n', '\\n')

    # Create a task for the agent
    task_yaml = f"""
    name: Meeting Summarizer Task
    description: Summarize a meeting transcript and generate action items.

    tools: []

    main:
      - prompt:
          - role: system
            content: You are {{agent.name}}. {{agent.about}}
          - role: user
            content: >
              Here is the transcript of a meeting: "{escaped_transcript}"

              Please summarize the key points and generate action items.
              For each action item, include the assignee's name and a due date.
              Return your output in the following structure:

              ```yaml
              summary: "<string>"
              action_items:
              - task: "<string>"
                assignee: "<string>"
                due_date: "<YYYY-MM-DD>"
              ```
        unwrap: true

      - evaluate:
          result: load_yaml(_.split('```yaml')[1].split('```')[0].strip())
    """

    # Ensure all indentation is using spaces, not tabs
    task_yaml = task_yaml.replace('\t', '    ')

    try:
        task = client.tasks.create(
            agent_id=agent.id,
            **yaml.safe_load(task_yaml)
        )
    except yaml.YAMLError as e:
        return jsonify({'error': f'YAML parsing error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error creating task: {str(e)}'}), 500

    # Execute the task
    try:
        execution = client.executions.create(
            task_id=task.id,
            input={"transcript": transcript}
        )
    except Exception as e:
        return jsonify({'error': f'Error during execution creation: {str(e)}'}), 500

    # Wait for the result
    while True:
        try:
            result = client.executions.get(execution.id)
            if result.status in ['succeeded', 'failed']:
                break
            time.sleep(1)
        except Exception as e:
            return jsonify({'error': f'Error retrieving execution result: {str(e)}'}), 500

    # Process the result
    if result.status == "succeeded":
        action_items = result.output['result']['action_items']

        # Store summary in Confluence
        store_in_confluence(result.output['result']['summary'], action_items)

        # Create Jira issues for action items
        for item in action_items:
            try:
                create_jira_issue(item['task'], item['assignee'], item['due_date'])
            except Exception as e:
                print(f"Error creating Jira issue: {str(e)}")

        return jsonify({
            'summary': result.output['result']['summary'],
            'action_items': action_items
        })
    else:
        return jsonify({'error': result.error}), 500


def store_in_confluence(summary, action_items):
    page_title = "Meeting Summary - " + time.strftime("%Y-%m-%d %H:%M:%S")
    page_content = f"""
    <h1>Meeting Summary</h1>
    <p>{summary}</p>
    <h2>Action Items</h2>
    <ul>
    {''.join([f'<li><strong>{item["task"]}</strong> - Assigned to: {item["assignee"]}, Due: {item["due_date"]}</li>' for item in action_items])}
    </ul>
    """

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "type": "page",
        "title": page_title,
        "space": {"key": "~712020a9eff71a5a5a4d99a7b4663b8b5602d6"},
        "body": {
            "storage": {
                "value": page_content,
                "representation": "storage"
            }
        }
    }

    response = requests.post(
        url,
        auth=HTTPBasicAuth(CONFLUENCE_API_USERNAME, CONFLUENCE_API_TOKEN),
        json=data,
        headers=headers
    )

    if response.status_code in [200, 201]:
        print("Page created successfully in Confluence.")
    else:
        print(f"Failed to create page in Confluence:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")


def create_jira_issue(task, assignee, due_date):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/"
    headers = {
        "Content-Type": "application/json"
    }

    # Description in Atlassian Document Format (ADF)
    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Task: {task}"},
                    {"type": "text", "text": f"\nAssigned to: {assignee}"},
                    {"type": "text", "text": f"\nDue Date: {due_date}"}
                ]
            }
        ]
    }

    data = {
        "fields": {
            "project": {
                "key": "KAN"
            },
            "summary": task,
            "description": description_adf,  # ADF-compliant description
            "issuetype": {
                "name": "Task"
            },
            "assignee": {
                "emailAddress": assignee
            }
        }
    }

    response = requests.post(
        url,
        auth=HTTPBasicAuth(JIRA_API_USERNAME, JIRA_API_TOKEN),
        json=data,
        headers=headers
    )

    if response.status_code == 201:
        print("Jira issue created successfully.")
    else:
        print(f"Failed to create Jira issue:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")



if __name__ == '__main__':
    app.run(debug=True)
