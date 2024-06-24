import sqlite3
import requests

# Connect to SQLite database
db = sqlite3.connect('slack_users.db')
cursor = db.cursor()

# Ensure the 'total_hours' column exists
cursor.execute('''
    ALTER TABLE users ADD COLUMN total_hours REAL
''')
db.commit()

# Function to fetch total hours from the Hack Hour API
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

# Update the database with total hours
def update_total_hours():
    cursor.execute('SELECT id FROM users')
    user_ids = cursor.fetchall()
    
    for user_id in user_ids:
        user_id = user_id[0]
        total_hours = fetch_total_hours(user_id)
        if total_hours is not None:
            cursor.execute('UPDATE users SET total_hours = ? WHERE id = ?', (total_hours, user_id))
            db.commit()
            print(f"Updated total hours for user {user_id}")

# Run the update function
update_total_hours()

# Close the database connection
db.close()
