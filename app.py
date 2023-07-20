import uuid
from flask import Flask, redirect, request, render_template, url_for
import requests
import json

app = Flask(__name__)
app.config['SERVER_NAME'] = '127.0.0.1:5000'  # Replace with your server name or domain

# Replace with your Spotify API credentials
CLIENT_ID = '62e6163968de41cd8e9aac30b8224560'
CLIENT_SECRET = '4c605da6d1274f4c83d5d1af045eb266'
REDIRECT_URI = 'http://127.0.0.1:5000'

# Store user data (in production, use a secure database)
users_data = {}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/authorize_user')
def authorize_user():
    # Generate a unique identifier for the user
    user_id = str(uuid.uuid4())

    # Redirect the user to Spotify authorization page
    authorize_url = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}/callback_user&scope=user-read-recently-played&state={user_id}"
    return redirect(authorize_url)


@app.route('/callback_user')
def callback_user():
    # Extract the authorization code and state from the callback URL
    authorization_code = request.args.get('code')
    state = request.args.get('state')

    if not state:
        return "Invalid user identifier"

    # Use the authorization code to obtain access token and refresh token
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': authorization_code,
        'redirect_uri': f"{REDIRECT_URI}/callback_user",
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(token_url, data=payload)
    response_data = response.json()

    # Extract the access token and store it securely for the user
    access_token = response_data['access_token']
    users_data[state] = {'access_token': access_token}

    return redirect(url_for('compare', user_id=state))


@app.route('/compare/<user_id>')
def compare(user_id):
    # Retrieve user 1's tracks
    user1_tracks = users_data.get(user_id)
    if not user1_tracks:
        return "Invalid user ID"

    # Check if the current user has authorized
    if 'access_token' not in users_data[user_id]:
        authorize_url = url_for('authorize_user', _external=True)
        return render_template('authorize.html', authorize_url=authorize_url)

    # Retrieve the current user's tracks
    current_user_tracks = fetch_user_tracks(users_data[user_id]['access_token'])

    # Compare user 1's tracks with the current user's tracks
    common_tracks = compare_tracks(user1_tracks, current_user_tracks)

    return render_template('result.html', user_id=user_id, common_tracks=common_tracks)


def fetch_user_tracks(access_token):
    # Fetch user's recently played tracks
    url = "https://api.spotify.com/v1/me/player/recently-played"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    recently_played_data = response.json()
    tracks = [item['track']['name'] for item in recently_played_data['items']]
    return tracks


def compare_tracks(user1_tracks, user2_tracks):
    # Compare tracks and find common tracks
    common_tracks = set(user1_tracks).intersection(user2_tracks)
    return common_tracks


if __name__ == '__main__':
    app.run(debug=True)
