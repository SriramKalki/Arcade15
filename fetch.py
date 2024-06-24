import sqlite3
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
        name TEXT
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

def store_user_info(user):
    cursor.execute('''
        INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)
    ''', (user['id'], user['profile']['real_name']))
    db.commit()

def main(channel_id):
    # Fetch members of the specified channel
    channel_members = fetch_channel_members(channel_id)
    
    # Fetch all users
    users = fetch_users()
    
    # Filter users based on membership in the specified channel
    users_in_channel = [user for user in users if user['id'] in channel_members]
    
    # Store filtered users in the database
    for user in users_in_channel:
        store_user_info(user)
    
    # Fetch and sort user data from the database
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    for row in rows:
        print(f'User ID: {row[0]}, Name: {row[1]}')

if __name__ == '__main__':
    channel_id = 'C06SBHMQU8G'  # Replace with your channel ID
    main(channel_id)
    db.close()
