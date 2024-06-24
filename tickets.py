import sqlite3
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time

# Initialize with your Slack token
token = ''
client = WebClient(token=token)

# Connect to SQLite database
db = sqlite3.connect('slack_users.db')
cursor = db.cursor()

# Initialize all tickets fields to 0 for every user
cursor.execute('''
    UPDATE users SET tickets = 0
''')
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

def main():
    users = fetch_users_from_db()
    for i, user in enumerate(users):
        if i > 0 and i % 45 == 0:
            print("Rate limit reached. Sleeping for 60 seconds...")
            time.sleep(60)
        user_id, user_name, total_hours = user
        count = search_messages_for_user_mentions(user_id)
        update_mention_count(user_id, count)
        print(f"Updated mention count for user {user_name} ({user_id}) to {count}")

if __name__ == '__main__':
    main()
    db.close()
