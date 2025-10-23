# oa-wfms
Demo code for a workflow management solution for open access publishers

## Resources

- Wekan API reference: https://wekan.fi/api/v7.93/#wekan-rest-api
- OJS API reference: https://docs.pkp.sfu.ca/dev/api/ojs/3.3

## Installation

Clone repo. From inside the cloned folder run:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Available scripts

- ***test.py***: Simple script to test connections and output information from both plattforms
- ***basic_wekan_api_example.py***: A minimal example how to connect to Wekan, authenticate and make a simple request.
- ***python_wekan_api_example.py***: A minimal example how to use the WekanClient package [https://pypi.org/project/python-wekan](https://pypi.org/project/python-wekan). Attention: This package is limited and has issues which currently render it not usabale. Documentation is outdated. As of October 2025 this package should not be used. Might be tested again at a later satge.
- ***oa-wfms-demo.py***: The actual demonstrator that synchronizes OJS data with a given Wekan board.
- ***run_loop.sh***: Bash script to run the main demonstrator in a loop with configurable intervals.

## Usage

### Basic configuration

- Set variables and credetials in `.env` and `.secrets.env` files. Template for `.secrets.env`:

```bash
# .secrets.env
WEKAN_USERNAME="<my user name>"
WEKAN_PASSWORD="<my password>"

OJS_USERNAME="<my user name>"
OJS_PASSWORD="<API key>"
```

- Run `source venv/bin/activate` to set python venv
- Run `python3 test.py` to test basic access (no data is modified on either plattform). Output with information from both systems should be generated without any error messages.

### Running the demonstrator in a loop

The `run_loop.sh` script allows you to automatically run the synchronization process at regular intervals. This is useful for maintaining continuous synchronization between OJS and Wekan.

**Run with default 60-second interval:**
```bash
./run_loop.sh
```

**Run with custom interval (e.g., every 30 seconds):**
```bash
./run_loop.sh 30
```
- Press `Ctrl+C` to stop the loop

## Description of the demonstrator

The demonsrator consists of two classes `WekanAPI` and `OJSAPI` which handle, respectively, the two plattforms to be synchronized. These classes are bundled inside a python module (i.e. subfolder) named `middleware`.

The main function simply creates instances of both classes and calls the function to synchronize the instances.

### The OJSAPI class

The class `OJSAPI` currently only implements functions to fetch data from OJS. No information is written to the OJS instance. The core worker function is

`fetch_endpoint`

which performs an authenticated API call and returns the result as a JSON array.

An API endpoint is called by simply passing the endpoint path and parameters, e.g.:

`published_submissions = OJSPAI.fetch_endpoint('submissions', params=f'status={self.STATUS_PUBLISHED}')`

according to the OJS API reference.

### The WekanAPI class

The `WekanAPI` class implements a generic function `call_api` to interact with Wekan API endpoints. The method handles authentication and performs requests according to a given REST API request type (GET, POST or PUT).

The work horses of the WekanAPI class are the functions `synchronize` and `synchronizeCard` which perform the synchronization according to the discussed specifications, i.e. the provided structure of swimlanes, lists and cards.

For OJS objects that don't already exist in Wekan new Wekan objects are automatically created. In case a Wekan object already exists for a given OJS object the Wekan object will be updated.

Although objects in Wekan have specific IDs, synchronization actions and the update of card contents is generally based on literal comparision of object names (**Attention: be aware of typos !!!**). This is required, because otherwise the middleware would need its own database to store information about the relation between Wekan and OJS objects (which is not possible to handle in this small demonstrator).

### The `.env` settings file

The `.env` file is used to provide basic configuration options like, e.g. URLs of the instances to be synchronized, Wekan board name, list, swimlanes and checklist definitions.

These definitions configured here will be literally compared to respective names from the board to be synchronized and need to exactly match the ones used on the board.

The `.env` file currently provides two predefined checklists for issue or submission cards, respectively, that will be used to create new cards. The checklist name and items are provided as json arrays:

```json
## Wekan default checklists
CHECKLIST_TEMPLATE_ISSUE = '{"title": "Demo Issue Checklist", "items": ["item 1", "item 2", "item 3"]}'
CHECKLIST_TEMPLATE_SUBMISSION = '{"title": "Demo Submission Checklist", "items": ["item 1", "item 2", "item 3"]}'
```
