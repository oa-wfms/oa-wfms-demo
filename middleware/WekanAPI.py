import json
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import requests
import re

# Wekan API reference: https://wekan.fi/api/v7.93/#wekan-rest-api

PROCESS_GROUP_INBOX = os.getenv('PROCESS_GROUP_INBOX', 'Vorlauf')
PROCESS_GROUP_PROOF = os.getenv('PROCESS_GROUP_PROOF', 'Prüfung')
PROCESS_GROUP_COPYEDITING = os.getenv('PROCESS_GROUP_COPYEDITING', 'Lektorat')
PROCESS_GROUP_PRODUCTION = os.getenv('PROCESS_GROUP_PRODUCTION', 'Satz / Produktion')
PROCESS_GROUP_POST_PRODUCTION = os.getenv('PROCESS_GROUP_POST_PRODUCTION', 'Post-Produktion')
PROCESS_GROUP_CONTROL = os.getenv('PROCESS_GROUP_CONTROL', 'Kontrolle')

PRODUCT_GROUP_JOURNALS = os.getenv('PRODUCT_GROUP_JOURNALS', 'Zeitschriften')
PRODUCT_GROUP_BOOKSERIES = os.getenv('PRODUCT_GROUP_BOOKSERIES', 'Schriftenreihen')
PRODUCT_GROUP_ANTHOLOGY = os.getenv('PRODUCT_GROUP_ANTHOLOGY', 'Sammelbände')
PRODUCT_GROUP_MONOGRAPH = os.getenv('PRODUCT_GROUP_MONOGRAPH', 'Monographien')

class WekanAPI:

    DEBUG = False

    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path=".secrets.env")  # Loads secrets from .secrets.env into environment
        self.base_url = os.getenv('WEKAN_URL')
        self.username = os.getenv('WEKAN_USERNAME')
        self.password = os.getenv('WEKAN_PASSWORD')
        self.board_name = os.getenv('DEMO_BOARD_NAME', 'Testboard')
        self.token = None
        self.user_id = None

    def get_login_data(self):
        headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*'
        }
        login_url = f"{self.base_url}/users/login"
        payload = {"username": self.username, "password": self.password}
        response = requests.post(login_url, json=payload, headers=headers)
        response.raise_for_status()
        data = self.handle_response(response)
        self.token = data['token']
        self.user_id = data['id']
        return data

    def call_api(self, method, url, params=None, data=None, json_data=None, headers=None):
        params = params or {}
        data = data or {}
        json_data = json_data or {}
        headers = headers or {}

        default_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        merged_headers = {**default_headers, **headers}
        if self.DEBUG:
            print(f"\033[92m=== {method.upper()} {url} ===\033[0m")
            print(f"Params: {params}")
            print(f"Data: {data}")
            print(f"JSON: {json_data}")
            print(f"Headers: {merged_headers}")

        method = method.lower()
        if method == 'get':
            response = requests.get(url, params=params, headers=merged_headers)
        elif method == 'post':
            response = requests.post(url, data=data, json=json_data, headers=merged_headers)
        elif method == 'put':
            response = requests.put(url, data=data, json=json_data, headers=merged_headers)
        else:
            raise ValueError("Method must be 'get', 'put' or 'post'")
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"\033[91mHTTP error: {e}\033[0m")
            print(f"\033[91mResponse content: {response.text}\033[0m")
            raise
        return self.handle_response(response)

    def handle_response(self, response):
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return response.json()
        elif 'text/html' in content_type:
            print(f"\033[91mWarning: Received HTML response instead of JSON when fetching URL {response.url}.\033[0m")
            exit(1)
        else:
            return {"content": response.text}
        
    def synchronize(self, ojs_api):
        self.get_login_data()

        # fetch issues and sections from OJS
        ojs_api.getIssuesAndSections()

        # create a default card for the journal itself in the inbox
        journal_name = self.get_journal_name()
        default_journal_card = self.synchronizeCard(
            board_title=self.board_name,
            swimlane_title=PRODUCT_GROUP_JOURNALS,
            list_title=PROCESS_GROUP_INBOX,
            card_title=journal_name,
            card_description=f"Zeitschrift {journal_name}",
            color="blue",
            title=journal_name,
            checklist=json.loads(os.getenv('CHECKLIST_TEMPLATE_JOURNAL', {}))
        )

        # loop through all issues and create cards if they don't exist
        sections = {}
        for issue in ojs_api.future_issues.get('items', []):
            print(f"Found future issue: {issue['identification']}")
            locale = issue.get('locale', 'de_DE')
            issue_number = issue.get('volume', 'No volume number')
            issue_year = issue.get('year', 'No Year')
            print(f"\033[92mSynchronizing issue ID {issue['id']} with number '{issue_number}' and year '{issue_year}'\033[0m")

            card_title = f"{journal_name} Heft {issue_number} ({issue_year})"
            self.synchronizeCard(
                board_title=self.board_name,
                swimlane_title=PRODUCT_GROUP_JOURNALS,
                list_title=PROCESS_GROUP_INBOX,
                card_title=card_title,
                card_description=f"Heft {issue_number} ({issue_year})",
                color="green", title=issue.get('title', 'No Title').get(locale, 'No Title'),
                checklist=json.loads(os.getenv('CHECKLIST_TEMPLATE_ISSUE', {}))
            )

            # collect sections from the issues
            sections.update({sec['id']: sec for sec in issue.get('sections', [])})
            # remove duplicate sections by their id (sections is already a dict)
            ojs_api.sections = list(sections.values())
        print(f"\033[92mCollected {len(ojs_api.sections)} unique sections from issues.\033[0m")

        # fetch OJS submissions and iterate over them
        ojs_api.getActiveSubmissions()
        for submission in ojs_api.iterSubmissions():
            locale = submission.get('locale')
            current_publication = ojs_api.getCurrentPublication(submission)
            if self.DEBUG:
                print("Active submission:", json.dumps(submission, indent=2))

            title = current_publication.get('fullTitle', 'No Title')[locale]
            url = current_publication.get('_href', 'No URL')
            url = re.sub(r'/api/v1/.*$', f'/workflow/index/{submission["id"]}/{submission["stageId"]}', url)
            authors = current_publication.get('authorsStringShort', "No Authors")
            description = f"URL: {url} Title: {title}\n\n\nAuthors: {authors}\n\n"
            print(f"\033[92mSynchronizing submission ID {submission['id']} with title '{title}'\033[0m")

            # get submission workflow stage and map to list
            workflow_stage = submission.get('stageId', ojs_api.WORKFLOW_STAGE_SUBMISSION)
            if workflow_stage == ojs_api.WORKFLOW_STAGE_SUBMISSION:
                list_name = PROCESS_GROUP_INBOX
            elif workflow_stage == ojs_api.WORKFLOW_STAGE_INTERNAL_REVIEW or workflow_stage == ojs_api.WORKFLOW_STAGE_EXTERNAL_REVIEW:
                list_name = PROCESS_GROUP_PROOF
            elif workflow_stage == ojs_api.WORKFLOW_STAGE_EDITING:
                list_name = PROCESS_GROUP_COPYEDITING
            elif workflow_stage == ojs_api.WORKFLOW_STAGE_PRODUCTION:
                list_name = PROCESS_GROUP_PRODUCTION
            else:
                list_name = PROCESS_GROUP_INBOX  # default to inbox if unknown

            # get section name from OJS sections indexing by current_publication sectionId
            section_name = self.get_section_name(ojs_api, current_publication, locale)
            card_title = self.get_card_title(journal_name, section_name, submission['id'], authors)

            self.synchronizeCard(
                board_title=self.board_name,
                swimlane_title=PRODUCT_GROUP_JOURNALS,
                list_title=list_name,
                card_title=card_title,
                card_description=description,
                title=title,
                checklist=json.loads(os.getenv('CHECKLIST_TEMPLATE_SUBMISSION', {}))
            )

        # if the publications issueId is set, find the corresponding issue and set the cards parentId to the issue card
        # this requires that the issue cards have been created first
        
        # find the board and swimlane once for all linking operations
        boards = self.call_api('get', f"{self.base_url}/api/users/{self.user_id}/boards")
        board = next((b for b in boards if b['title'] == self.board_name), None)
        if not board:
            print(f"\033[91mBoard '{self.board_name}' not found.\033[0m")
            return

        swimlanes = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/swimlanes")
        swimlane = next((sl for sl in swimlanes if sl['title'] == PRODUCT_GROUP_JOURNALS), None)
        if not swimlane:
            print(f"\033[91mSwimlane '{PRODUCT_GROUP_JOURNALS}' not found.\033[0m")
            return

        # get all cards in the swimlane once
        cards = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/swimlanes/{swimlane['_id']}/cards")

        for submission in ojs_api.iterSubmissions():
            current_publication = ojs_api.getCurrentPublication(submission)
            # print(current_publication) # for debugging
            issue_id = current_publication.get('issueId')
            print(f"\033[92mProcessing card linking information for submission ID {submission['id']} with current publication issueId = {issue_id}\033[0m")
            if issue_id:
                issue = next((iss for iss in ojs_api.issues.get('items', []) if iss['id'] == issue_id), None)
                if issue:
                    locale = issue.get('locale', 'de_DE')
                    issue_number = issue.get('volume', 'No volume number')
                    issue_year = issue.get('year', 'No Year')
                    issue_card_title = f"{journal_name} Heft {issue_number} ({issue_year})"
                    submission_locale = submission.get('locale')
                    current_publication = ojs_api.getCurrentPublication(submission)
                    title = current_publication.get('fullTitle', 'No Title')[submission_locale]
                    authors = current_publication.get('authorsStringShort', "No Authors")

                    # get section name from OJS sections indexing by current_publication sectionId
                    section_name = self.get_section_name(ojs_api, current_publication, locale)
                    card_title = self.get_card_title(journal_name, section_name, submission['id'], authors)

                    print(f"\033[92mLinking submission ID {submission['id']} to issue ID {issue_id}\033[0m")

                    # find issue card and submission card by title
                    issue_card = next((card for card in cards if card['title'] == issue_card_title), None)
                    submission_card = next((card for card in cards if card['title'] == card_title), None)

                    # remove existing links to default journal card from submission card
                    ## ToDO @ronste: implement removal of existing links if any. First check the problem that OJS returns issueIds even if submissions are not assigned to an issue yet.

                    # add parentId to submission card if not already set
                    if issue_card and submission_card:
                        if submission_card.get('parentId') != issue_card.get('_id'):
                            print(f"Updating parentId of submission card '{card_title}' to issue card '{issue_card_title}'")
                            updated_card = self.call_api(
                                'put',
                                f"{self.base_url}/api/boards/{board['_id']}/lists/{submission_card['listId']}/cards/{submission_card['_id']}",
                                json_data={"parentId": issue_card.get('_id')}
                            )
                            if self.DEBUG:
                                print("Updated card:", json.dumps(updated_card, indent=2))
            else:
                print(f"Submission ID {submission['id']} has no issue assigned, linking to default journal card '{default_journal_card['title']}'.")
                # link to default journal card via id provided by default_journal_card
                if default_journal_card:
                    card_title = self.get_card_title(
                        journal_name,
                        self.get_section_name(ojs_api, ojs_api.getCurrentPublication(submission), submission.get('locale')),
                        submission['id'],
                        ojs_api.getCurrentPublication(submission).get('authorsStringShort', "No Authors")
                    )
                    submission_card = next((card for card in cards if card['title'] == card_title), None)
                    if submission_card:
                        self.call_api(
                            'put',
                            f"{self.base_url}/api/boards/{board['_id']}/lists/{submission_card['listId']}/cards/{submission_card['_id']}",
                            json_data={"parentId": default_journal_card['_id']}
                        )

    # simple test function to demonstrate usage
    def test_api(self, data=''):
        print("Running as:", self.username)
        login_data = self.get_login_data()
        print("Auth token:", self.token)

        # GET user boards
        boards = self.call_api('get', f"{self.base_url}/api/users/{self.user_id}/boards")
        print("GET response:", boards)

        # Get specific board
        board = next((b for b in boards if b['title'] == self.board_name), None)
        if board:
            print(f"Found board '{self.board_name}' with ID:", board['_id'])
            board_details = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}")
            if self.DEBUG:
                print("Board details:", json.dumps(board_details, indent=2))
        else:
            print(f"\033[91mBoard '{self.board_name}' not found.\033[0m")
            exit(1)

        # GET swimlanes of the board
        swimlanes = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/swimlanes")
        print("Swimlanes:", json.dumps(swimlanes, indent=2))

        # GET lists of the board
        lists = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/lists")
        print("Lists:", json.dumps(lists, indent=2))
        current_list = lists[0] if lists else None

        # GET cards in current list
        cards = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/lists/{current_list['_id']}/cards")
        print("Cards in list " + current_list['_id'] + ":", json.dumps(cards, indent=2))

        card = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/lists/{current_list['_id']}/cards/{cards[0]['_id']}")
        card_custom_fields = card.get('customFields', {})
        print("Card details:", json.dumps(card, indent=2))
        custom_field = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/custom-fields/{card_custom_fields[0].get('_id')}")
        print("Custom field definition:", json.dumps(custom_field, indent=2))

    def synchronizeCard(self, board_title, swimlane_title, list_title, card_title, title, card_description, card_id=None, color=None, checklist=None):        
        board = self.find_board(board_title)
        if not board:
            print(f"\033[91mBoard '{board_title}' not found.\033[0m")
            return

        swimlane = self.find_swimlane(board['_id'], swimlane_title)
        if not swimlane:
            print(f"\033[91mSwimlane '{swimlane_title}' not found in board '{board_title}'.\033[0m")
            return

        target_list = self.find_list(board['_id'], list_title)
        if not target_list:
            print(f"\033[91mList '{list_title}' not found in board '{board_title}'.\033[0m")
            return

        # Get all cards in the swimlane
        existing_card = self.find_card_by_title(board['_id'], swimlane['_id'], card_title)

        # Update existing card or create a new one
        if existing_card:
            print(f"Card '{card_title}' already exists. Updating...")
            card = self.call_api(
                'put',
                f"{self.base_url}/api/boards/{board['_id']}/lists/{existing_card['listId']}/cards/{existing_card['_id']}",
                json_data={
                    "newBoardId": board['_id'],
                    "newSwimlaneId": swimlane['_id'],
                    "listId": target_list['_id'],
                    "archive": "false",
                    "title": card_title,
                    "description": card_description
                }
            )
            if self.DEBUG:
                print("Updated card:", json.dumps(card, indent=2))
        else:
            print(f"Creating new card '{card_title}'...")
            new_card = {
                "authorId": self.user_id,
                "title": card_title,
                "description": card_description,
                "swimlaneId": swimlane['_id']
            }
            card = self.call_api(
                'post',
                f"{self.base_url}/api/boards/{board['_id']}/lists/{target_list['_id']}/cards",
                json_data=new_card
            )
            if color:
                # we need to edit the card again to set the color
                card = self.call_api(
                    'put',
                    f"{self.base_url}/api/boards/{board['_id']}/lists/{target_list['_id']}/cards/{card['_id']}",
                    json_data={"color": color}
                )
            # add checklist to the card
            checklist = self.call_api(
                'post',
                f"{self.base_url}/api/boards/{board['_id']}/cards/{card['_id']}/checklists",
                json_data=checklist
            )
            if self.DEBUG:
                print("Created card:", json.dumps(card, indent=2))
        
        # get card details, find custom field with name Title and update it
        card_details = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/lists/{target_list['_id']}/cards/{card['_id']}")
        custom_fields = card_details.get('customFields', {})
        # get details for custom field named Title
        title_field = None
        for field in custom_fields:
            custom_field_details = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/custom-fields/{field.get('_id')}")
            if self.DEBUG:
                print("Custom field details:", json.dumps(custom_field_details, indent=2))
            if custom_field_details.get('name') == 'Title':
                title_field = custom_field_details
                break
        if not title_field:
            # get all custom fields of the board
            board_custom_fields = self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/custom-fields")
            title_field = next((cf for cf in board_custom_fields if cf.get('name') == 'Title'), None)
            # create new custom field Title if it doesn't exist
            if not title_field:
                print(f"\033[91mCustom field 'Title' not found. Creating it...\033[0m")
                title_field = self.call_api(
                    'post',
                    f"{self.base_url}/api/boards/{board['_id']}/custom-fields",
                    json_data={
                        "name": "Title",
                        "type": "text",
                        "settings": {},
                        "showOnCard": False,
                        "automaticallyOnCard": True,
                        "alwaysOnCard": True,
                        "showLabelOnMiniCard": True,
                        "showSumAtTopOfList": False
                    }
                )
                if self.DEBUG:
                    print("Created custom field 'Title':", json.dumps(title_field, indent=2))
        
        # update custom field Title with the provided title
        if title_field:
            # Handle both dict and string responses from API
            field_id = title_field.get('_id') if isinstance(title_field, dict) else title_field
            self.call_api(
                'put',
                f"{self.base_url}/api/boards/{board['_id']}/lists/{target_list['_id']}/cards/{card['_id']}",
                json_data={"customFields": [
                    { "_id": field_id, "value": title }
                ]}
            )

        # return card updated card details
        return self.call_api('get', f"{self.base_url}/api/boards/{board['_id']}/lists/{target_list['_id']}/cards/{card['_id']}")

    def get_journal_name(self):
        """Extract journal name from OJS URL"""
        return os.path.basename(urlparse(os.getenv('OJS_URL')).path).upper()

    def get_card_title(self, journal_name, section_name, submission_id, authors):
        """Generate card title for submissions"""
        return f"{journal_name}: {section_name} #{submission_id} {authors}"

    def get_section_name(self, ojs_api, current_publication, locale):
        """Get section name from OJS sections indexing by current_publication sectionId"""
        section = next((sec for sec in ojs_api.sections if sec['id'] == current_publication.get('sectionId')), {})
        if section:
            return section.get('title', '')[locale]
        else:
            if os.getenv('DEFAULT_SECTION_NAME') == '':
                return f"Section #{current_publication.get('sectionId', '')}"
            else:
                return f"{os.getenv('DEFAULT_SECTION_NAME', 'Section')}"

    def find_board(self, board_title):
        boards = self.call_api('get', f"{self.base_url}/api/users/{self.user_id}/boards")
        return next((b for b in boards if b['title'] == board_title), None)

    def find_swimlane(self, board_id, swimlane_title):
        swimlanes = self.call_api('get', f"{self.base_url}/api/boards/{board_id}/swimlanes")
        return next((s for s in swimlanes if s['title'] == swimlane_title), None)

    def find_list(self, board_id, list_title):
        lists = self.call_api('get', f"{self.base_url}/api/boards/{board_id}/lists")
        return next((lst for lst in lists if lst['title'] == list_title), None)

    def find_card_by_title(self, board_id, swimlane_id, card_title):
        cards = self.call_api('get', f"{self.base_url}/api/boards/{board_id}/swimlanes/{swimlane_id}/cards")
        return next((card for card in cards if card_title == card['title']), None)