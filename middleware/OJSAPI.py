import json
import os
from dotenv import load_dotenv
import requests

# OJS API reference: https://docs.pkp.sfu.ca/dev/api/ojs/3.3

class OJSAPI:

    # OJS constants
    WORKFLOW_STAGE_SUBMISSION = 1
    WORKFLOW_STAGE_INTERNAL_REVIEW = 2
    WORKFLOW_STAGE_EXTERNAL_REVIEW = 3
    WORKFLOW_STAGE_EDITING = 4
    WORKFLOW_STAGE_PRODUCTION = 5
    STATUS_QUEUED = 1
    STATUS_PUBLISHED = 3
    STATUS_DECLINED = 4
    STATUS_SCHEDULED = 5

    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path=".secrets.env")  # Loads secrets from .secrets.env into environment
        self.base_url = os.getenv('OJS_URL')
        self.username = os.getenv('OJS_USERNAME')
        self.password = os.getenv('OJS_PASSWORD')

        self.submissions = []
        self.issues = []
        self.future_issues = []
        self.sections = []

    # Generic function to fetch paginated OJS endpoints
    def fetch_endpoint(self, endpoint, params=''):
        offset = 0
        count = 50
        itemsMax = None
        result = {'items': []}
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        while True:
            journals_url = f"{self.base_url}/api/v1/{endpoint}?apiToken={self.password}&{params}&count={count}&offset={offset}"
            response = requests.get(journals_url, headers=headers)
            response.raise_for_status()
            page_data = response.json()

            if itemsMax is None:
                # if there is no itemsMax field we don't have a paginated response and can return immediately
                if 'itemsMax' not in page_data:
                    return page_data 
                itemsMax = page_data.get('itemsMax', 0)

            result['items'].extend(page_data.get('items', []))

            if len(result['items']) >= itemsMax or not page_data.get('items'):
                break
            offset += count
        result['itemsMax'] = itemsMax
        return result

    # Get all active submissions
    def getActiveSubmissions(self):
        self.submissions = self.fetch_endpoint('submissions', params=f'status={self.STATUS_QUEUED}')
        return self.submissions
    
    # itarator over all submissions
    def iterSubmissions(self):
        for submission in self.submissions.get('items', []):
            yield submission

    def getCurrentPublication(self, submission):
        currentPublicationId = submission.get('currentPublicationId', {})
        # fetch publication details via API, the publication object that comes with the submission is incomplete
        return self.fetch_endpoint(f'/submissions/{submission["id"]}/publications/{currentPublicationId}')

    def getIssuesAndSections(self):
        # get ojs issues, loop over all issues to extract and merge section arrays
        self.issues = self.fetch_endpoint('issues')
        section_map = {}
        for issue in self.issues.get('items', []):
            issue_details = self.fetch_endpoint(f'issues/{issue["id"]}')
            for section in issue_details.get('sections', []):
                section_id = section.get('id')
                if section_id and section_id not in section_map:
                    section_map[section_id] = section
        self.sections = list(section_map.values())
        self.future_issues = self.fetch_endpoint('issues', params=f'isPublished=0')
        return

    # simple test function to demonstrate usage
    def test_api(self):
        print("Running as:", self.username)

        # Get published submissions by direct API call
        published_submissions = self.fetch_endpoint('submissions', params=f'status={self.STATUS_PUBLISHED}')
        print("Published submissions:", json.dumps(published_submissions['itemsMax'], indent=2))

        # Get declined submissions by direct API call
        declined_submissions = self.fetch_endpoint('submissions', params=f'status={self.STATUS_DECLINED}')
        print("Declined submissions:", json.dumps(declined_submissions['itemsMax'], indent=2))

        # Get queued submissions by direct API call
        queued_submissions = self.fetch_endpoint('submissions', params=f'status={self.STATUS_QUEUED}')
        print("Queued (Active) submissions:", json.dumps(queued_submissions['itemsMax'], indent=2))

        # Get scheduled submissions by direct API call
        scheduled_submissions = self.fetch_endpoint('submissions', params=f'status={self.STATUS_SCHEDULED}')
        print("Scheduled submissions:", json.dumps(scheduled_submissions['itemsMax'], indent=2))

        return f"Fetched from {self.base_url} : {published_submissions['itemsMax']} published, {declined_submissions['itemsMax']} declined, {queued_submissions['itemsMax']} queued, and {scheduled_submissions['itemsMax']} scheduled submissions."
