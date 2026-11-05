# AFEWS mobile app (residents)

A React Native app built with Expo. Residents create an account, see their
zone's flood risk, read the alerts sent to their zone, and rate how useful an
alert was. It talks to the Django backend through the REST API in
`docs/api.md`.

## One-time setup

1. **Install Node.js** (the "LTS" version) from https://nodejs.org, then close and
   reopen Git Bash. Check it worked: `node --version` should print a number.
2. **Install Expo Go** on your phone (free): Play Store on Android, App Store on iPhone.
3. **Put the laptop and phone on the same Wi-Fi.** If the Wi-Fi blocks devices from
   seeing each other (common at universities), turn on your phone's hotspot and
   connect the laptop to it instead.

## Run it (every time)

Use two Git Bash windows.

**Window 1: the backend**

```bash
cd backend
source venv/Scripts/activate
python manage.py runserver 0.0.0.0:8000
```

The first time, edit `backend/.env` and set `DJANGO_ALLOWED_HOSTS=*` (for local
development only). When Windows asks about the firewall for Python, tick
**Private networks** and click **Allow access**.

**Window 2: the app**

```bash
cd mobile
npm install        # first time only, takes a few minutes
npx expo start
```

A QR code appears. On Android, open Expo Go and tap **Scan QR code**. On iPhone,
scan it with the Camera app. The app opens on your phone and updates by itself
when the code changes.

## If it says "Can't reach the server"

- Is `runserver 0.0.0.0:8000` still running in Window 1?
- Are the phone and laptop on the same Wi-Fi?
- Did you allow Python through the Windows firewall (Private networks)?
- Is `DJANGO_ALLOWED_HOSTS=*` in `backend/.env`? Restart the backend after changing it.
- Last resort: run `ipconfig` on the laptop, find the **IPv4 Address** (for example
  `192.168.1.50`), and type `http://192.168.1.50:8000/api` into `MANUAL_API_URL`
  in `src/config.js`. The Account screen shows which server address the app is using.

## Tests

```bash
npm test
```

## Files

- `App.js`: stays signed in, and switches between the screens
- `src/screens/`: Login, Register, Home (my zone), Alerts, Account
- `src/api.js`: every call to the Django API
- `src/config.js`: where the server is
