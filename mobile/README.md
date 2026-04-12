# SikhSituationBot — Mobile App

React Native / Expo app for iOS and Android, sharing the same Flask backend as the web client.

---

## Quick Start

```bash
cd mobile
cp .env.example .env.local
# Fill in your values (see sections below)
npm install
npx expo start
```

Press `i` to open in iOS Simulator, `a` for Android Emulator, or scan the QR code with the **Expo Go** app on your phone.

### Run a development build on Android (recommended)

Requires [Android Studio](https://developer.android.com/studio) (SDK + an emulator or USB device with USB debugging).

#### If you see `Failed to resolve the Android SDK path` or `spawn adb ENOENT`

The Android SDK is not installed at the default location, or **`ANDROID_HOME`** is unset.

1. Install **Android Studio** and open it once so it downloads the **Android SDK**.
2. In Android Studio: **Settings** (macOS: **Android Studio → Settings**) → **Languages & Frameworks** → **Android SDK**. Note **Android SDK Location** (often `~/Library/Android/sdk`).
3. On the same screen, install at least one **SDK Platform** (e.g. Android 15 / API 35), **Android SDK Build-Tools**, **Android SDK Platform-Tools**, and **Android Emulator**.
4. Point your shell at that path (use the path shown in Android Studio, not a guess):

   ```bash
   # Typical macOS default — replace if your SDK location differs
   export ANDROID_HOME="$HOME/Library/Android/sdk"
   export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"
   ```

   Add the same `export` lines to `~/.zshrc` so new terminals pick them up. **`adb`** lives in `platform-tools`; without it you get `spawn adb ENOENT`.

5. Confirm:

   ```bash
   echo "$ANDROID_HOME"
   adb version
   ```

6. **Java for Gradle:** `expo run:android` runs `./android/gradlew`, which needs a **JDK**. If you see *“Unable to locate a Java Runtime”*, point **`JAVA_HOME`** at the JDK bundled with Android Studio (no separate Java install required):

   ```bash
   export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
   ```

   Add that line to `~/.zshrc` next to your `ANDROID_HOME` exports. Check with `java -version` (should print OpenJDK 17 or 21 from that path once `JAVA_HOME/bin` is on `PATH`, or run `"$JAVA_HOME/bin/java" -version`).

7. Then: `cd mobile && npx expo run:android`

First run may generate `mobile/android/` and take several minutes. Google Sign-In on a **dev client** needs **`EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`** plus your debug **SHA-1** in Google Cloud — see [docs/GOOGLE_OAUTH_PRODUCTION.md](./docs/GOOGLE_OAUTH_PRODUCTION.md#android-emulator-dev-client-play-internal-testing).

---

## Environment Setup

Copy `.env.example` to `.env.local` and fill in:

| Variable | Description |
|---|---|
| `EXPO_PUBLIC_API_URL` | Your Railway Flask URL |
| `EXPO_PUBLIC_FLASK_INTERNAL_KEY` | Must match `FLASK_INTERNAL_API_KEY` on Flask |
| `EXPO_PUBLIC_GOOGLE_*_CLIENT_ID` | Google OAuth client IDs (see below) |

---

## Google OAuth Setup (Step-by-Step)

You need **4 OAuth client IDs** — one for each platform. All live in the same Google Cloud project as your web app.

### 1. Open Google Cloud Console
1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Select your existing project (the one used by the web app's `GOOGLE_CLIENT_ID`)
3. Navigate to: **APIs & Services → Credentials**

### 2. Create the Expo Go Client (for development)
1. Click **Create Credentials → OAuth 2.0 Client ID**
2. Application type: **Web application**
3. Name: `SikhSituationBot - Expo Go`
4. Authorised redirect URIs: add `https://auth.expo.io/@YOUR_EXPO_USERNAME/gianiji` (see `app.json` slug / `owner`)
5. Copy the client ID → `EXPO_PUBLIC_GOOGLE_EXPO_CLIENT_ID`

### 3. Create the iOS Client
1. Click **Create Credentials → OAuth 2.0 Client ID**
2. Application type: **iOS**
3. Bundle ID: `com.gianiji.app` (see `app.json` `ios.bundleIdentifier`)
4. Copy the client ID → `EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID`
5. Also paste it into `app.json` under `ios.config.googleSignIn.reservedClientId`
   - Format: `com.googleusercontent.apps.YOUR_IOS_CLIENT_ID` (reversed domain)

### 4. Create the Android Client
1. Click **Create Credentials → OAuth 2.0 Client ID**
2. Application type: **Android**
3. Package name: `com.gianiji.app`
4. SHA-1 fingerprint: run `cd android && ./gradlew signingReport` (or use Expo's debug keystore SHA-1: `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android`)
5. Copy the client ID → `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID`

### 5. Use the existing Web Client
Your web app already has a Web OAuth client ID. Copy it to `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`.

---

## Fonts

Gurmukhi text requires `NotoSansGurmukhi` font files in `assets/fonts/`:

```
assets/fonts/
  NotoSansGurmukhi-Regular.ttf
  NotoSansGurmukhi-Bold.ttf
```

Download from: [Google Fonts — Noto Sans Gurmukhi](https://fonts.google.com/noto/specimen/Noto+Sans+Gurmukhi)

---

## Push Notifications

Push notifications use Expo's push service. No backend changes are required for local testing. For production, you'll eventually need to add a `/api/push-token` endpoint to Flask to store tokens and a job to send them.

---

## Building for Devices (No App Store Required)

### Install EAS CLI
```bash
npm install -g eas-cli
eas login
```

### Preview build (installable APK for Android)
```bash
eas build --platform android --profile preview
```
The build link will give you a `.apk` you can install directly on any Android phone.

### Development build (replaces Expo Go, recommended)
```bash
eas build --platform all --profile development
```

---

## Project Structure

```
mobile/
├── app/
│   ├── _layout.tsx           # Root layout, auth gate, font loading
│   ├── (auth)/               # Login, register screens
│   ├── (tabs)/               # Chat, Parmaans, Settings, Admin tabs
│   ├── onboarding.tsx        # Birth year collection
│   └── shared/[shareId].tsx  # Shared chat deep link
├── components/               # Reusable UI components
├── contexts/                 # Auth, Theme, Translation providers
├── lib/                      # API helpers, secure storage, notifications
└── assets/fonts/             # NotoSansGurmukhi font files
```

---

## Production / App Store (EAS)

1. **Google redirect URI** — Add the Expo proxy URL to your Web OAuth client (see [docs/GOOGLE_OAUTH_PRODUCTION.md](./docs/GOOGLE_OAUTH_PRODUCTION.md)).
2. **EAS login** — `npm install -g eas-cli` then `eas login` (or set `EXPO_TOKEN` for CI).
3. **Environment** — `eas.json` production profile sets `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID`. Set `EXPO_PUBLIC_FLASK_INTERNAL_KEY` for production builds via `eas env:create` or the Expo dashboard (see same doc).
4. **Build & submit:**
   ```bash
   cd mobile
   npm run eas:build:ios:production
   npm run eas:submit:ios:latest
   ```

`eas.json` already includes iOS submit metadata (`appleId`, `ascAppId`, `appleTeamId`).

## App Store Submission (Future)

When ready:
1. Create an [Apple Developer account](https://developer.apple.com/) ($99/yr)
2. Create a [Google Play Developer account](https://play.google.com/console) ($25 one-time)
3. Fill in `eas.json` submit section with your Apple ID / Play service account
4. Run `eas submit --platform all --profile production`
