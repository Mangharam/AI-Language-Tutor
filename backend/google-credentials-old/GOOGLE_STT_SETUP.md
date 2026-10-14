# Google Speech-to-Text setup (one time)

Voice input already works without Google (it falls back to your browser's
speech recognition in Chrome or Edge). Do these steps to use Google Speech-to-Text.
Menu names may differ slightly in the Google Cloud console.

1. Go to https://console.cloud.google.com and sign in with a Google account.
2. Create a project: top bar > project picker > New Project > name it `language-tutor`.
3. Billing: Billing > link a billing account. Google asks for a payment method
   even for the free tier. New accounts get a trial credit, and Speech-to-Text V1
   includes 60 free minutes per month. Check the current pricing page before heavy use.
4. Enable the API: APIs & Services > Library > search "Cloud Speech-to-Text API" > Enable.
5. Create a service account: IAM & Admin > Service Accounts > Create service account
   > name `tutor-stt` > Done. If you later get a permission error, add the role
   "Cloud Speech Client" to this account.
6. Create a key: open the service account > Keys > Add key > Create new key > JSON.
   A .json file downloads.
7. Rename it to `google-credentials.json` and put it in the `backend` folder.
   Never share this file or upload it to GitHub.
8. In the activated venv: `pip install google-cloud-speech`
9. Restart the backend. Open http://localhost:8000/api/health and check for "stt":"google".
