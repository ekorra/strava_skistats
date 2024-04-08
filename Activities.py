import yaml
import json
import requests
import io
import csv
import shutil
import os
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import parse_qs
from pathlib import Path
from strava_activity import Strava_activity
from datetime import datetime
# from requests_oauthlib import OAuth2Session


try:
    client_id = os.environ['STRAVASTAT_CLIENT_ID']
    client_secret = os.environ['STRAVASTAT_CLIENT_SECRET']
except KeyError as key_error:
    raise Exception(f'Could not load environment: {key_error.args}')

with open("config.yml", "r") as stream:
    config = yaml.safe_load(stream)

    if config is not None:
        activities_url = config['strava']["activities_url"]
        scopes = config['strava']["scopes"]
        token_url = config['strava']["token_url"]
        authorize_url = config['strava']["authorize_url"]
        redirect_uri = config['strava']["redirect_uri"]
    else:
        raise Exception(f'Failed to load config')


def save_csv(strava_activities: Strava_activity):
    csv_output = io.StringIO()
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow(['Tittel', 'Dato', 'Type', 'Høydemeter', 'Distanse',
                        'Varighet', 'Tid i bevegelse', 'Maks fart', 'Høeste punkt', 'Laveste punkt'])

    for strava_activity in strava_activities:
        csv_writer.writerow([strava_activity.activity_name,
                            strava_activity.date,
                            strava_activity.sport_type,
                            str(strava_activity.elevation_gain).replace('.', ','),
                            str(strava_activity.distance).replace('.', ','),
                            str(strava_activity.elapsed_time).replace('.', ','),
                            str(strava_activity.moving_time).replace('.', ','),
                            str(strava_activity.max_speed).replace('.', ','),
                            str(strava_activity.elevation_low).replace('.', ','),
                            str(strava_activity.elevation_high).replace('.', ',')])

    csv_output.seek(0)
    filename = "season24"
    file = Path(f"output/{filename}.csv")
    file.parent.mkdir(parents=True, exist_ok=True)

    with open(file, "w") as stream:
        shutil.copyfileobj(csv_output, stream)


def get_access_token() -> str:
    response_type = 'code'

    authorize_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scopes,
        'response_type': response_type,
    }

    # For å bruke annet bibliotek
    # strava = OAuth2Session(client_id=client_id, scope=scopes,
    #                        redirect_uri=redirect_uri, response_type=response_type)
    # authorization_url, state = strava.authorization_url(authorize_url)

    enc = urlencode(authorize_params)
    print('Please go here and authorize', authorize_url + '?' + enc)

    code_url = input('Paste the full redirect URL here: ')
    parsed_url = urlparse(code_url)
    code = parse_qs(parsed_url.query)['code'][0]
    print(code)
    token_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code'
    }

    response = requests.post(token_url, data=token_payload)
    if not response:
        raise Exception(f"Non-success status code: {response.status_code}")

    text = response.text
    token_info = json.loads(text)
    token_info['access_token']
    access_token = token_info['access_token']
    refresh_token = token_info['refresh_token']
    expires_at = token_info['expires_at']
    expires_in = token_info['expires_in']

    print('Access token: ' + access_token)
    return access_token


access_token = ''

if not access_token:
    access_token = get_access_token()

# Define the date range for the last year
today = datetime.now()
season_start = datetime(2023, 10, 1)


# Define parameters for activity retrieval
activities_params = {
    'before': int(today.timestamp()),
    'after': int(season_start.timestamp()),
    # 'after': int(last_year.timestamp()),
    'sport_type': 'BackcountrySki',
    'per_page': 200,
    'page': 1
}

# Make the API request to retrieve activities
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get(
    activities_url, params=activities_params, headers=headers)

if response:
    activities = response.json()
    activity_list = []
    unique_skidates = []

    bc_dict = {'total_elevation_gain': 0, 'number_of_trips': 0, 'max_speed': 0, 'total_elevation': 0, 'longest_trip_distance': 0, 'longest_trip': '',
               'max_elevation': 0, 'max_elevaton_trip': '', 'max_suffer_score': 0, 'max_suffer_score_trip': ''}
    alpine_dict = {'number_of_trips': 0, 'max_speed': 0}

    for activity in activities:
        # Process each activity as needed
        # print(json.dumps(activity, indent=4))
        if activity["sport_type"] == 'BackcountrySki' or activity["sport_type"] == 'AlpineSki':

            strava_activity = Strava_activity(
                activity["name"],
                datetime.strptime(
                    activity["start_date_local"], '%Y-%m-%dT%H:%M:%SZ'),
                activity["location_country"],
                activity["sport_type"],
                activity["elapsed_time"],
                activity["total_elevation_gain"],
                activity["distance"],
                activity["moving_time"],
                None,  # activity["suffer_score"],
                activity["elev_low"],
                activity["elev_high"],
                activity["max_speed"]

            )

            if strava_activity.sport_type == 'BackcountrySki':

                bc_dict['total_elevation_gain'] += activity["total_elevation_gain"]
                bc_dict['number_of_trips'] += 1

                if 'suffer_score' in activity:
                    strava_activity.suffer_score = activity["suffer_score"]
                    if activity["suffer_score"] > bc_dict['max_suffer_score']:
                        bc_dict['max_suffer_score'] = activity["suffer_score"]
                        bc_dict['max_suffer_score_trip'] = activity["name"]
                if activity["distance"] > bc_dict['longest_trip_distance']:
                    bc_dict['longest_trip_distance'] = activity["distance"]
                    bc_dict['longest_trip'] = activity["name"]
                if activity['total_elevation_gain'] > bc_dict['max_elevation']:
                    bc_dict['max_elevation'] = activity['total_elevation_gain']
                    bc_dict['max_elevaton_trip'] = activity["name"]
                if activity['max_speed'] > bc_dict['max_speed']:
                    bc_dict['max_speed'] = activity['max_speed']

                    bc_dict['total_elevation'] += activity["total_elevation_gain"]

            if strava_activity.sport_type == 'AlpineSki':
                alpine_dict['number_of_trips'] += 1
                if activity['max_speed'] > alpine_dict['max_speed']:
                    alpine_dict['max_speed'] = activity['max_speed']

            activity_date = datetime.strptime(
                activity["start_date_local"], '%Y-%m-%dT%H:%M:%SZ').date()

            if activity_date not in unique_skidates:
                unique_skidates.append(activity_date)

            activity_list.append(strava_activity)

    save_csv(activity_list)
    print('Anall skidager:' + str(len(unique_skidates)))

    bc_dict['max_speed'] = bc_dict['max_speed']*3.6
    alpine_dict['max_speed'] = alpine_dict['max_speed']*3.6
    print(bc_dict)
    print(alpine_dict)

else:
    print(
        f"Failed to retrieve activities. Status code: {response.status_code}")
    print(response.text)
