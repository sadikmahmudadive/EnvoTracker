# EcoTrack — Desktop Carbon Tracker (Tkinter)

>A lightweight desktop application to track personal carbon footprint, sync logs to Firebase Firestore, and view community totals and leaderboards.

## Quick summary
- UI: Tkinter with `ttkbootstrap` theme
- Data backend: Firebase Firestore via `firebase-admin` and Firebase Authentication (REST) for email/password
- Main script: `main_tk.py`

## Prerequisites
- Python 3.8 or newer
- A Firebase project with Firestore and Email/Password authentication enabled

## Install (recommended: virtual environment)
Windows (cmd):

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install requests
```

macOS / Linux (bash):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install requests
```

Note: `requirements.txt` includes `firebase-admin`, `ttkbootstrap`, and `matplotlib`. `requests` is used by the app for Firebase REST auth and is installed separately above.

## Firebase setup
1. Open the Firebase Console and create (or open) a project.
2. Enable Firestore Database (in native mode).
3. Enable Authentication → Sign-in method → Email/Password.
4. Generate a service account private key: Project settings → Service accounts → Generate new private key. Save the JSON and place it in the project root as `serviceAccountKey.json`.
5. Obtain your Web API key (Project settings → General → Web API Key) and add it to `firebase_config.json` like this:

```json
{
  "apiKey": "YOUR_FIREBASE_API_KEY"
}
```

Alternatively, set an environment variable `FIREBASE_API_KEY` and the app will read that if `firebase_config.json` is not present.

Security note: Do NOT commit `serviceAccountKey.json` into source control. Keep it private.

## Configuration files in repo
- `serviceAccountKey.json` — Firebase Admin service account key (you must provide this)
- `firebase_config.json` — small JSON with `apiKey` used for Firebase Authentication (or set `FIREBASE_API_KEY` env var)

## Run the app
From the project root after activating your virtualenv:

```bash
python main_tk.py
```

You should see the EcoTrack desktop window. If the app warns about a missing API key, either create `firebase_config.json` (above) or set `FIREBASE_API_KEY`.

## Usage notes
- Create logs on the Dashboard tab; logs are saved to Firestore.
- Register or sign in using Email/Password to store logs under your user id and enable editing/deleting your entries.
- Export CSVs from the Dashboard or Community tabs.

## Emission factors
The app uses a built-in `EM` dictionary in `main_tk.py` to calculate CO2 impact per activity. Edit the dictionary in `main_tk.py` if you need to change values.

## Troubleshooting
- If you see `ModuleNotFoundError`, ensure your virtual environment is active and dependencies are installed.
- If Firestore calls fail, confirm `serviceAccountKey.json` is present and Firestore is enabled.
- If Firebase Authentication fails, confirm `firebase_config.json` contains a valid `apiKey` or set `FIREBASE_API_KEY`.

## Development
- The UI code lives in `main_tk.py`. The app is structured for quick edits and small experiments.

---

If you want, I can also:
- add `requests` to `requirements.txt` so `pip install -r requirements.txt` installs everything, or
- create a small `run.ps1` / `run.sh` helper to start the app.

Made with 💚 — help us make it greener!
