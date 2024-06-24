import sqlite3
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize with your Slack token
token = 0
client = WebClient(token=token)

# Connect to SQLite database (or create it if it doesn't exist)
db = sqlite3.connect('slack_users.db')
cursor = db.cursor()

# Create table to store user data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT
    )
''')
db.commit()

def fetch_users():
    all_users = []
    for paginated_response in client.users_list(limit=1000):
        print(paginated_response["members"][0]['id'])
        all_users += paginated_response["members"]
    return all_users

def store_user_info(user):
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)
    ''', (user['id'], user['profile']['real_name']))
    db.commit()

def main():
    users = fetch_users()
    for user in users:
        store_user_info(user)

    # Fetch and sort user data from the database
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    for row in rows:
        print(f'User ID: {row[0]}, Name: {row[1]}')

if __name__ == '__main__':
    main()
    db.close()
