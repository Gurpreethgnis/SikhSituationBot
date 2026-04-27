# Google OAuth (Expo / production)

## Why Google shows "Custom scheme URIs are not allowed for 'WEB' client type"

If the app only has `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` (a **Web** OAuth client) and no **iOS** / **Android** client id, `expo-auth-session` sends `redirect_uri` like `com.gianiji.app:/oauthredirect` on native builds. **Web** clients only allow `https` redirect URIs, so Google can show *“Custom scheme URIs are not allowed for 'WEB' client type.”*

In **Expo Go** only, the app uses the **https** `auth.expo.io/@owner/slug` redirect with your Web client (add that URI under the Web client). **Development / production native builds** must use **iOS** and/or **Android** OAuth clients below — not the proxy.

## Authorized redirect URI (Google Cloud Console)

Add this **exact** redirect URI to your **Web application** OAuth client (same as `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID` / Next.js `GOOGLE_CLIENT_ID`):

`https://auth.expo.io/@gurpreethgnis/gianiji`

Path: [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → your Web client → **Authorized redirect URIs** → Add URI → Save.

If `owner` or `slug` in `app.json` changes, update this URI to match (or read the `Redirect URI` line from Metro logs when opening Google sign-in).

## Development builds (`expo run:ios`, TestFlight, App Store)

These run as **native** apps (`ExecutionEnvironment.Bare` / `Standalone`), not Expo Go. **`https://auth.expo.io/...` must not be used** as `redirect_uri` here: Google may complete, but Expo’s proxy often cannot return to `exp+…` / your app scheme, and you see *“Something went wrong trying to finish signing in”* with a **`cancel`** response in JS.

**Required:** create an **OAuth client ID** of type **iOS** in the same Google Cloud project:

1. [Credentials](https://console.cloud.google.com/apis/credentials) → **Create credentials** → **OAuth client ID** → Application type **iOS**.
2. **Bundle ID:** `com.gianiji.app` (must match `app.json` → `ios.bundleIdentifier`).
3. Copy the new client id (ends with `.apps.googleusercontent.com`).

Set **`EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`** to that value in `mobile/.env` and in EAS production env if you use EAS. Rebuild the native app (`npx expo run:ios` or a new EAS build).

`expo-auth-session` will then use this client on iOS and redirect to `com.gianiji.app:/oauthredirect`, which Google accepts for an **iOS** client (not for a **Web** client).

## Android (emulator, dev client, Play internal testing)

Same idea as iOS: use an **OAuth client ID** of type **Android** (not Web only).

Without **`EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`**, the app falls back to your **Web** client while still using redirect `com.gianiji.app:/oauthredirect`. That mismatch often looks like “sign-in worked” but the browser ends on **`google.com`** or never returns to the app.

1. [Credentials](https://console.cloud.google.com/apis/credentials) → **Create credentials** → **OAuth client ID** → Application type **Android**.
2. **Package name:** `com.gianiji.app` (must match `app.json` → `android.package`).
3. **SHA-1 certificate fingerprint** (required by Google for Android OAuth):
   - **Debug / local `expo run:android`:** from the project, after a successful Android build:
     ```bash
     cd mobile/android && ./gradlew signingReport
     ```
     Under `Variant: debug`, copy **SHA1** for `debugAndroidTest` or the `debug` config that matches your install.
   - Or default debug keystore:  
     `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android`  
     and use the **SHA1** line.
4. Paste that SHA-1 into the Android OAuth client in Google Cloud, save, then copy the **client id** into `mobile/.env`:

   `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=<…>.apps.googleusercontent.com`

5. Rebuild: `npx expo run:android` (env changes need a new JS bundle at minimum; native changes need a rebuild).

Release / Play Store builds use a **different** signing key; add that SHA-1 to the same Android client (or create a second Android OAuth client for production) when you ship.

## Expo Go only (optional)

If you still test inside **Expo Go**, the app may use the **https** `auth.expo.io/@owner/slug` redirect with your **Web** client. Keep that URI on the Web client’s **Authorized redirect URIs** list.

## EAS / TestFlight: internal key

`POST /api/auth/oauth-sync` sends `X-Internal-Key` from `EXPO_PUBLIC_FLASK_INTERNAL_KEY`. For **EAS cloud builds**, add it as an Expo environment variable (do not commit secrets to `eas.json`):

```bash
cd mobile
eas login
# Match Railway `FLASK_INTERNAL_API_KEY` (same value as in root .env / Vercel)
eas env:create production --name EXPO_PUBLIC_FLASK_INTERNAL_KEY --value "<your FLASK_INTERNAL_API_KEY>" --visibility secret --non-interactive --force
```

If the CLI rejects flags, use **expo.dev → Project → Environment variables** and set `EXPO_PUBLIC_FLASK_INTERNAL_KEY` for **production**.

Local dev uses `mobile/.env` (gitignored).
