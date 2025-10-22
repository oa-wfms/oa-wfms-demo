from middleware.OJSAPI import OJSAPI
from middleware.WekanAPI import WekanAPI

DEBUG = False

# Usage example:
if __name__ == "__main__":

    # just run a simple test function to fetch data from OJS
    ojs_api = OJSAPI()
    data = ojs_api.test_api()

    # pass the OJS data to Wekan test function to demonstrate usage
    wekan_api = WekanAPI()
    wekan_api.test_api(data)