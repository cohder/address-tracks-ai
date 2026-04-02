# Address Tracks AI — Streamlit Deployment Guide

## What you need
- A free personal GitHub account (gmail ID)
- A free Streamlit Cloud account (streamlit.io)
- Your Anthropic API key

---

## Step 1 — Push to GitHub (5 minutes)

1. Log in to github.com with your personal account
2. Click **New repository** → name it `address-tracks-ai` → set it to **Private** → click Create
3. Upload these files to the repo (drag and drop via GitHub UI):
   - `app.py`
   - `requirements.txt`
   - `.gitignore`
   - (Do NOT upload `.streamlit/secrets.toml` — that stays local)

---

## Step 2 — Deploy on Streamlit Cloud (5 minutes)

1. Go to share.streamlit.io and sign up free (connect with your GitHub account)
2. Click **New app**
3. Select your `address-tracks-ai` repository
4. Main file path: `app.py`
5. Click **Advanced settings** → open the **Secrets** section
6. Paste this (replace with your real key):
   ```
   ANTHROPIC_API_KEY = "your-anthropic-api-key-here"
   ```
7. Click **Deploy** — your app will be live in about 2 minutes

---

## Step 3 — Restrict access to leadership only

This is important — without this, anyone with the URL can access it.

1. In Streamlit Cloud, open your app settings
2. Go to **Sharing** → **Invite viewers**
3. Add each leader's email address individually
4. They'll receive an email invitation to access the app
5. Only those emails can log in — everyone else is blocked

---

## Step 4 — Share with leadership

Send leadership this message:

> "I've set up an AI assistant you can use to ask questions about our address tracks roadmap. 
> You'll receive a Streamlit invite to your email — click the link to access it.
> Just sign in with Google and start asking questions."

---

## How to update the context

There is no redeployment needed. Just:
1. Open the app
2. Click "Edit context" 
3. Paste updated roadmap information
4. Click "Activate portal"

Each session starts fresh — so you'll need to reload context each time you open the app. If you want the context to be permanently pre-loaded, let me know and I can update the code to hard-code it.

---

## Files in this folder

| File | Purpose |
|---|---|
| `app.py` | The entire application |
| `requirements.txt` | Python packages Streamlit Cloud will install |
| `.gitignore` | Prevents secrets from being pushed to GitHub |
| `.streamlit/secrets.toml` | Local testing only — never push this |
