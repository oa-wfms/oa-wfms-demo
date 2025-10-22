import os
from dotenv import load_dotenv
from wekan import WekanClient

# Basic Wekan API example using python-wekan package

# https://pypi.org/project/python-wekan/
# ATTENTION: documentation is outdated !!!
# package code seems to be buggy

if __name__ == '__main__':
    board_name = "Testboard" # name of the board to work with

    load_dotenv()  # Loads variables from .env into environment
    load_dotenv(dotenv_path=".secrets.env")  # Loads secrets from .secrets.env into environment
    wekan = WekanClient(
        base_url=os.getenv('WEKAN_URL'),
        username=os.getenv('WEKAN_USERNAME'),
        password=os.getenv('WEKAN_PASSWORD'))

    boards = wekan.list_boards() # This call crashes with testuser but works with admin
    print("Boards:")
    for board in boards:
        print("Board title: " + board.title)
        for member in board.members:
            print(f" - {member}")

    board = wekan.list_boards(regex_filter=board_name)[0]
    wekan_list = board.get_lists()[0]
    swimlane = board.list_swimlanes()[0]
    wekan_list.create_card(
        title="My first SUPER card",
        swimlane=swimlane,
        description="My first SUPER description")

    # board = wekan.list_boards(regex_filter='Testboard')[0]
    # swimlane = board.list_swimlanes()[0]
    # board.create_list(title="My first list")
    # board.create_list(title="My second list")

    # # time.sleep(2)
    # wekan_list = wekan.fetch_json(f'/api/boards/{board.id}/lists')[0]
    # # wekan_list = board.get_lists()
    # # wekan_list = board.get_lists(regex_filter="My second list")[0]
    # wekan_list.create_card(
    #     title="My first card",
    #     description="My first description")

    # print(wekan.fetch_json(f'/api/boards_count'))

    