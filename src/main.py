import logging
import os
import random
import time
import sys
import json
from datetime import date

from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.mixins.challenge import ChallengeChoice

from utils.unfollowers_provider import get_unfollowers


SESSION_FILE = 'session.json'
LOGGING_FILE = f'logs/records_{date.today()}.log'
UNFOLLOWED_FILE = 'data/unfollowed.json'


USERNAME = ''
PASSWORD = ''


logger = logging.getLogger()


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    cl = Client()
    if SESSION_FILE in os.listdir():
        session = cl.load_settings(SESSION_FILE)
    else:
        session = None

    login_via_session = False
    login_via_pw = False

    if session:
        try:
            cl.set_settings(session)
            cl.login(USERNAME, PASSWORD)

            # check if session is valid
            try:
                cl.get_timeline_feed()
            except LoginRequired:
                logger.info("Session is invalid, need to login via username and password")

                old_session = cl.get_settings()

                # use the same device uuids across logins
                cl.set_settings({})
                cl.set_uuids(old_session["uuids"])

                cl.login(USERNAME, PASSWORD)
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information: %s" % e)

    if not login_via_session:
        try:
            logger.info("Attempting to login via username and password. username: %s" % USERNAME)
            if cl.login(USERNAME, PASSWORD):
                login_via_pw = True
                cl.dump_settings(SESSION_FILE)
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e)

    if not login_via_pw and not login_via_session:
        raise Exception("Couldn't login user with either password or session")
    
    return cl


def unfollow_user(cl, username_to_unfollow):
    """
    Unfollows a user by their username.
    
    :param username_to_unfollow: The username of the user to unfollow.
    """
    try:
        user_id = cl.user_id_from_username(username_to_unfollow)
        logging.info(cl.user_info(user_id))
        unfollow_result = cl.user_unfollow(user_id)
        if unfollow_result:
            logging.info(f"Successfully unfollowed {username_to_unfollow}")
            return True
        else:
            logging.info(f"Failed to unfollow {username_to_unfollow}")
            return False
    except Exception as e:
        error_message = f"Error unfollowing {username_to_unfollow}: {e}"
        logging.info(error_message)
        return False


def update_unfollowed(unfollowed):
    with open('unfollowed.json', 'w') as file:
        json.dump(unfollowed, file)


def unfollow_users(cl, usernames_to_unfollow: list, unfollowed: list = []):
    """
    Unfollows a list of users.
    
    :param usernames_to_unfollow: A list of usernames to unfollow.
    """
    for username in usernames_to_unfollow:
        if unfollow_user(cl, username):
            unfollowed.append(username)
            update_unfollowed(unfollowed)
        delay = random.randint(300, 900)  # Random delay between 5 and 15 minutes
        logging.info(f"Time until next unfollow: {delay} seconds")
        time.sleep(delay)
    return unfollowed
    

def set_up_logging():
    # Set up logging to write to sys out
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    # Set up logging to write to a file
    file_handler = logging.FileHandler(LOGGING_FILE)
    file_handler.setLevel(logging.INFO)

    # Create a formatter and add it to the file handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Get the root logger and add the file handler
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    return root_logger


def load_unfollowed():
    """
    Loads the list of already unfollowed users from the 'unfollowed.json' file.
    Returns an empty list if the file doesn't exist.
    """
    unfollowed = []
    if 'unfollowed.json' in os.listdir():
        with open('unfollowed.json', 'r') as file:
            unfollowed = json.load(file)
    return unfollowed


def filter_unfollowed(unfollowers, unfollowed):
    """
    Filters out the already unfollowed users from the list of unfollowers.
    Returns the filtered list of unfollowers.
    """
    return [user for user in unfollowers if user not in unfollowed]


def main():

    set_up_logging()

    cl = login_user()

    unfollowers = get_unfollowers()

    unfollowed = load_unfollowed()

    unfollowers = filter_unfollowed(unfollowers, unfollowed)

    unfollow_users(cl, unfollowers, unfollowed)


if __name__ == '__main__':
    main()


