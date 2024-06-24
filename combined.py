import os
import sqlite3
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize with your Slack token
token = os.environ.get('API')
client = WebClient(token=token)

# Connect to SQLite database (or create it if it doesn't exist)
db = sqlite3.connect('slack_users.db')
cursor = db.cursor()

# Create table to store user data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT,
        total_hours REAL
    )
''')
db.commit()

def fetch_channel_members(channel_id):
    members = []
    cursor = None
    while True:
        try:
            response = client.conversations_members(channel=channel_id, cursor=cursor)
            if response['ok']:
                members.extend(response['members'])
                cursor = response['response_metadata'].get('next_cursor')
                if not cursor:
                    break
            else:
                print('Error fetching channel members:', response['error'])
                break
        except SlackApiError as e:
            print('Error fetching channel members:', e.response['error'])
            break
    return members

def fetch_users():
    users = []
    cursor = None
    while True:
        try:
            response = client.users_list(cursor=cursor)
            if response['ok']:
                users.extend(response['members'])
                cursor = response['response_metadata'].get('next_cursor')
                if not cursor:
                    break
            else:
                print('Error fetching users:', response['error'])
                break
        except SlackApiError as e:
            print('Error fetching users:', e.response['error'])
            break
    return users

def fetch_total_hours(user_id):
    try:
        response = requests.get(f'https://hackhour.hackclub.com/api/stats/{user_id}')
        data = response.json()
        if data['ok']:
            total_hours = data['data']['total'] / 60  # Convert minutes to hours
            return total_hours
        else:
            print(f"Error fetching stats for user {user_id}: {data['error']}")
            return None
    except Exception as e:
        print(f"Error fetching stats for user {user_id}: {e}")
        return None

def store_user_info(user):
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, name, total_hours) VALUES (?, ?, ?)
    ''', (user['id'], user['profile']['real_name'], user['total_hours']))
    db.commit()

def main(channel_id):
    # Fetch members of the specified channel
    channel_members = fetch_channel_members(channel_id)
    
    # Fetch all users
    users = fetch_users()
    
    # Filter users based on membership in the specified channel
    users_in_channel = [user for user in users if user['id'] in channel_members]
    
    # Fetch total hours for each user and store in the database
    for user in users_in_channel:
        total_hours = fetch_total_hours(user['id'])
        if total_hours is not None:
            user['total_hours'] = total_hours
            store_user_info(user)
            print(f"Updated total hours for user {user['id']}")

# Run the main function
if __name__ == '__main__':
    channel_id = 'C06SBHMQU8G'  # Replace with your channel ID
    main(channel_id)
    db.close()
