import sqlite3
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
import os

bot_token = os.environ.get('API')
bot_client = WebClient(token=bot_token)


# Connect to SQLite database
db = sqlite3.connect('slack_users.db')
cursor = db.cursor()

# Create table to store user data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT
        total_hours REAL
        tickets REAL
    )
''')
db.commit()

def fetch_channel_members(channel_id):
    members = []
    cursor = None
    while True:
        try:
            response = bot_client.conversations_members(channel=channel_id, cursor=cursor)
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
            response = bot_client.users_list(cursor=cursor)
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


def fetch_users_from_db():
    cursor.execute('SELECT id, name, total_hours FROM users ORDER BY total_hours DESC')
    return cursor.fetchall()

def search_messages_for_user_mentions(user_id):
    mention_count = 0
    try:
        response = client.search_messages(
            query=f"from:hakkuun <@{user_id}> approved",
            count=1000
        )
        if response['ok']:
            messages = response['messages']['total']
            mention_count = messages
        else:
            print(f"Error searching messages for user {user_id}: {response['error']}")
    except SlackApiError as e:
        print(f"Error searching messages for user {user_id}: {e.response['error']}")
    return mention_count

def update_mention_count(user_id, count):
    cursor.execute('''
        UPDATE users SET tickets = ? WHERE id = ?
    ''', (count, user_id))
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

    user_token = os.environ.get('API2')
    user_client = WebClient(token=user_token)
    users = fetch_users_from_db()
    for i, user in enumerate(users):
        if i > 100:
            break
        elif i % 30 == 0:
            time.sleep(75)
        user_id, user_name, total_hours = user
        count = search_messages_for_user_mentions(user_id)
        update_mention_count(user_id, count)
        print(f"Updated mention count for user {user_name} ({user_id}) to {count}")


if __name__ == '__main__':
    channel_id = 'C06SBHMQU8G'  # Replace with your channel ID
    main(channel_id)
    db.close()