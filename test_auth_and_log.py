import os
import time
import json
from datetime import datetime
import requests

from firebase_admin import credentials, initialize_app, firestore, auth


def load_api_key():
    cfg_path = os.path.join(os.path.dirname(__file__), 'firebase_config.json')
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            return cfg.get('apiKey')
    return os.environ.get('FIREBASE_API_KEY')


def main():
    api_key = load_api_key()
    if not api_key:
        print('Missing Firebase API key (firebase_config.json or FIREBASE_API_KEY).')
        return

    sa_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
    if not os.path.exists(sa_path):
        print('Missing serviceAccountKey.json in project root. Aborting.')
        return

    # initialize admin SDK
    cred = credentials.Certificate(sa_path)
    initialize_app(cred)
    db = firestore.client()

    # create a temp test user
    ts = int(time.time())
    email = f'testuser+{ts}@example.local'
    password = 'TestPass123!'
    signup_url = f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}'
    payload = {'email': email, 'password': password, 'returnSecureToken': True}
    print('Registering test user:', email)
    r = requests.post(signup_url, json=payload)
    if r.status_code != 200:
        print('Sign-up failed:', r.text)
        return
    data = r.json()
    uid = data.get('localId')
    id_token = data.get('idToken')
    print('Created UID:', uid)

    # add a sample log
    doc = {
        'activity_type': 'Test',
        'activity_detail': 'Automated test event',
        'amount': 1,
        'description': 'Created by test_auth_and_log.py',
        'co2_impact': 0.5,
        'timestamp': datetime.now(),
        'user_id': uid,
    }
    print('Adding test log to Firestore...')
    ref = db.collection('logs').add(doc)
    print('Log added, doc id:', ref[1].id if isinstance(ref, tuple) else getattr(ref, 'id', ref))

    # aggregate user's total
    total = 0
    docs = db.collection('logs').where('user_id', '==', uid).stream()
    for d in docs:
        dd = d.to_dict()
        total += abs(dd.get('co2_impact', 0))
    print(f'Aggregated total for user {uid}:', total)

    # cleanup: delete the auth user we created
    try:
        auth.delete_user(uid)
        print('Deleted test auth user', uid)
    except Exception as ex:
        print('Failed to delete test user:', ex)


if __name__ == '__main__':
    main()
