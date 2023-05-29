import time
import datetime
import json
import gspread
import random
import mysql.connector
from oauth2client.service_account import ServiceAccountCredentials
from instagram_private_api import Client, ClientError, ClientLoginError, ClientCookieExpiredError
import signal
import sys
import math
from googleapiclient.errors import HttpError

# Your actual Instagram account username and password
INSTAGRAM_USERNAME = "instagram_username"
INSTAGRAM_PASSWORD = "instagram_password"

# These variables store the Instagram API credentials that will be used to log in to the Instagram account.

# The actual Instagram username of the competitor account you want to monitor
COMPETITOR_USERNAME = "competitor_username"
# This variable stores the username of the competitor account.

# Google Sheets Configuration
SPREADSHEET_NAME = "Instagram Follower Tracker"
FOLLOWERS_SHEET_NAME = "Followers"
FOLLOWING_SHEET_NAME = "Following"
NEW_FOLLOWERS_SHEET_NAME = "New Followers"
NEW_FOLLOWING_SHEET_NAME = "New Following"
FOLLOW_EACH_OTHER_SHEET_NAME = "Follow Each Other"
# These variables define the names of the spreadsheets and worksheets in your Google Sheets document.


GOOGLE_SHEETS_CREDENTIALS = "GOOGLE_SHEETS_CREDENTIALS_name.json"
# Replace "prefab-botany-385715-1ae7408bc2c4.json" with the actual file path to your Google Sheets API service account credentials JSON file. This file contains the necessary authentication information for accessing Google Sheets API.

# Initialize Google Sheets Client
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
google_sheets_client = gspread.authorize(credentials)
# This code sets up the Google Sheets client by creating credentials from the provided JSON keyfile and authorizing the client to access Google Sheets API.

# Create spreadsheets for new followers and following
def create_spreadsheets():
    try:
        spreadsheet = google_sheets_client.create(SPREADSHEET_NAME)
        spreadsheet.share("", perm_type="anyone", role="writer")  # Share the spreadsheet publicly with write access
        followers_sheet = spreadsheet.add_worksheet(title=FOLLOWERS_SHEET_NAME, rows="10000", cols="3")
        following_sheet = spreadsheet.add_worksheet(title=FOLLOWING_SHEET_NAME, rows="10000", cols="3")
        new_followers_sheet = spreadsheet.add_worksheet(title=NEW_FOLLOWERS_SHEET_NAME, rows="10000", cols="3")
        new_following_sheet = spreadsheet.add_worksheet(title=NEW_FOLLOWING_SHEET_NAME, rows="10000", cols="3")
        follow_each_other_sheet = spreadsheet.add_worksheet(title=FOLLOW_EACH_OTHER_SHEET_NAME, rows="10000", cols="2")
        print(f"Spreadsheets created: {spreadsheet.url}")
        return followers_sheet, following_sheet, new_followers_sheet, new_following_sheet, follow_each_other_sheet
    except Exception as e:
        print(f"An error occurred while creating spreadsheets: {str(e)}")
        return None, None, None, None


# Database Configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "instagram_follower_tracker"
# Update the above variables with your database configuration details.

# Execution Frequency
EXECUTION_FREQUENCY = 12 * 60 * 60 # 12 hours
# This variable determines the time frequency for script execution, measured in seconds. The current value is set to 12 hours because you need it to run at least twice per day. You can adjust this value according to your desired frequency.

# Initialize Instagram API Client
instagram_api = None

# Define signal handler for script termination
def signal_handler(signal, frame):
    print("\nScript stopped.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Define Helper Functions
def get_followers():
    try:
        user_id = instagram_api.username_info(COMPETITOR_USERNAME)["user"]["pk"]
        rank_token = instagram_api.generate_uuid()
        followers = []
        next_max_id = None

        while True:
            response = instagram_api.user_followers(user_id, rank_token=rank_token, max_id=next_max_id)
            followers.extend(response.get("users", []))
            next_max_id = response.get("next_max_id")

            if not next_max_id:
                break

        return followers
    except ClientError as e:
        if e.code == 429:
            wait_time = int(e.error_response["message"].split("retry after ")[1])
            print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
            return get_followers()
        else:
            print(f"An error occurred while fetching followers: {str(e)}")
            return []
    except Exception as e:
        print(f"An error occurred while fetching followers: {str(e)}")
        return []

def get_following():
    try:
        user_id = instagram_api.username_info(COMPETITOR_USERNAME)["user"]["pk"]
        rank_token = instagram_api.generate_uuid()
        following = []
        next_max_id = None

        while True:
            response = instagram_api.user_following(user_id, rank_token=rank_token, max_id=next_max_id)
            following.extend(response.get("users", []))
            next_max_id = response.get("next_max_id")

            if not next_max_id:
                break

        return following
    except ClientError as e:
        if e.code == 429:
            wait_time = int(e.error_response["message"].split("retry after ")[1])
            print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
            time.sleep(wait_time)
            return get_following()
        else:
            print(f"An error occurred while fetching following: {str(e)}")
            return []
    except Exception as e:
        print(f"An error occurred while fetching following: {str(e)}")
        return []

#Add a new function named get_follow_each_other to retrieve the followers and following who follow each other:
def get_follow_each_other():
    try:
        followers = get_followers()
        following = get_following()
        
        followers_usernames = {follower['username'] for follower in followers}
        following_usernames = {follow['username'] for follow in following}
        
        follow_each_other = list(followers_usernames.intersection(following_usernames))
        return follow_each_other
    except Exception as e:
        print(f"An error occurred while fetching followers and following who follow each other: {str(e)}")
        return []

# Define the login function with error handling
def login():
    global instagram_api
    try:
        instagram_api = Client(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, auto_patch=True, drop_incompat_keys=False)
        instagram_api.login()
        print("Login successful.")
    except ClientLoginError as e:
        print(f"Failed to log in: {str(e)}")
        sys.exit(1)

# Connect to the database
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = db.cursor()

# Create the followers and following tables if they don't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS followers (
        username VARCHAR(255),
        full_name VARCHAR(255),
        timestamp DATETIME
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS following (
        username VARCHAR(255),
        full_name VARCHAR(255),
        timestamp DATETIME
    )
""")

# Define a function to handle rate limit exceeded errors
def handle_rate_limit_error(e):
    if e.code == 50:
        wait_time = int(e.error_response["message"].split("retry after ")[1])
        print(f"Rate limit exceeded. Waiting for {wait_time} seconds...")
        time.sleep(wait_time)
    else:
        print(f"An error occurred: {str(e)}")

def is_new_follower(username, followers_sheet):
    existing_usernames = [row[0] for row in followers_sheet.get_all_values()]
    return username not in existing_usernames

def is_new_following(username, following_sheet):
    existing_usernames = [row[0] for row in following_sheet.get_all_values()]
    return username not in existing_usernames


#Create a new function named update_follow_each_other to update the "follow_each_other" worksheet with the followers and following who follow each other:
def update_follow_each_other(follow_each_other_sheet):
    try:
        follow_each_other = get_follow_each_other()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write the headers to the follow each other sheet
        headers = ["Username", "Full Name", "Timestamp"]
        follow_each_other_sheet.insert_row(headers, index=1)
        
        # Write the follow each other data to the sheet
        for username in follow_each_other:
            full_name = ""
            timestamp = current_time
            data = [username, full_name, timestamp]
            follow_each_other_sheet.insert_row(data, index=len(follow_each_other_sheet.get_all_values()) + 1)
            time.sleep(1)
        
        print("Follow each other sheet updated.")
    except Exception as e:
        print(f"An error occurred while updating follow each other sheet: {str(e)}")  

# Update Followers and Following Sheets
def update_followers(followers_sheet, new_followers_sheet, follow_each_other_sheet):
    try:
        followers = get_followers()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Write the headers to the followers sheet
        headers = ["Username", "Full Name", "Timestamp"]
        followers_sheet.insert_row(headers, index=1)
        new_followers_sheet.insert_row(headers, index=1)

        # Write the followers data to the followers sheet and database
        for i in range(len(followers)):
            username = followers[i]["username"]
            full_name = followers[i]["full_name"]
            timestamp = current_time
            data = [username, full_name, timestamp]
            followers_sheet.insert_row(data, index=len(followers_sheet.get_all_values()) + 1)
            data2 = (username, full_name, timestamp)
            cursor.execute("INSERT INTO followers (username, full_name, timestamp) VALUES (%s, %s, %s)", data2)
            # Check if the follower is new and store in new_followers_sheet
            if is_new_follower(username, followers_sheet):
                new_followers_sheet.insert_row(data, index=len(new_followers_sheet.get_all_values()) + 1)
            time.sleep(1)

        db.commit()
        print("Followers sheet and database updated.")
        # Update the follow each other sheet
        update_follow_each_other(follow_each_other_sheet)
    except ClientError as e:
        handle_rate_limit_error(e)
        update_followers(followers_sheet)
    except Exception as e:
        print(f"An error occurred while updating followers sheet: {str(e)}")

def update_following(following_sheet, new_following_sheet):
    try:
        following = get_following()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Write the headers to the followers sheet
        headers = ["Username", "Full Name", "Timestamp"]
        following_sheet.insert_row(headers, index=1)
        new_following_sheet.insert_row(headers, index=1)
        print(len(following))
        # Write the following data to the following sheet and database
        for i in range(len(following)):
            username = following[i]["username"]
            full_name = following[i]["full_name"]
            timestamp = current_time
            data = [username, full_name, timestamp]
            following_sheet.insert_row(data, index=len(following_sheet.get_all_values()) + 1)
            data2 = (username, full_name, timestamp)
            cursor.execute("INSERT INTO following (username, full_name, timestamp) VALUES (%s, %s, %s)", data2)
            # Check if the following is new and store in new_following_sheet
            if is_new_following(username, following_sheet):
                new_following_sheet.insert_row(data, index=len(new_following_sheet.get_all_values()) + 1)
            time.sleep(1)

        db.commit()
        print("Following sheet and database updated.")
    except ClientError as e:
        handle_rate_limit_error(e)
        update_following(following_sheet)
    except Exception as e:
        print(f"An error occurred while updating following sheet: {str(e)}")
          


# Run the Script
def run_script():
    login()  # Authenticate with Instagram API
    # Create spreadsheets for new followers and following
    followers_sheet, following_sheet, new_followers_sheet, new_following_sheet, follow_each_other_sheet = create_spreadsheets()
    
    if followers_sheet is None or following_sheet is None or new_followers_sheet is None or new_following_sheet is None:
        print("Failed to create spreadsheets. Script stopped.")
        sys.exit(1)

    # Retrieve followers and following in batches and update the sheets and database
    while True:
        update_followers(followers_sheet, new_followers_sheet, follow_each_other_sheet)
        update_following(following_sheet, new_following_sheet)
        print(f"Waiting for {EXECUTION_FREQUENCY} seconds before next retry...")
        time.sleep(EXECUTION_FREQUENCY)

# Run the script
run_script()