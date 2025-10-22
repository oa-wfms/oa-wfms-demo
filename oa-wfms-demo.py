from middleware.OJSAPI import OJSAPI
from middleware.WekanAPI import WekanAPI

DEBUG = False

# Usage example:
if __name__ == "__main__":
    wekan_api = WekanAPI()
    wekan_api.synchronize(OJSAPI())