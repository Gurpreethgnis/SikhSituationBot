#!/usr/bin/env node
/**
 * CLI checks for Google OAuth on Android (no secrets printed in full).
 * Run: cd mobile && node ./scripts/verify-google-android-oauth.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const mobileRoot = path.join(__dirname, '..');

function readEnvFile(relPath) {
  const p = path.join(mobileRoot, relPath);
  if (!fs.existsSync(p)) return {};
  const out = {};
  for (const line of fs.readFileSync(p, 'utf8').split('\n')) {
    const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
    if (!m) continue;
    let v = m[2].trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'")))
      v = v.slice(1, -1);
    out[m[1]] = v;
  }
  return out;
}

function maskId(id) {
  if (!id) return '(unset)';
  if (id.length < 24) return '(set, too short?)';
  return `${id.slice(0, 12)}…${id.slice(-8)}`;
}

function main() {
  const appJson = JSON.parse(fs.readFileSync(path.join(mobileRoot, 'app.json'), 'utf8'));
  const pkg = appJson?.expo?.android?.package ?? 'com.gianiji.app';
  const env = { ...readEnvFile('.env'), ...readEnvFile('.env.local') };

  const androidCid = env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID || '';
  const webCid = env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || '';

  console.log('--- Google Android OAuth sanity ---');
  console.log('app.json android.package:', pkg);
  console.log('EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID:', maskId(androidCid));
  console.log('EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID:', maskId(webCid));
  console.log('');
  console.log('Expected Android redirect_uri (installed client / Google native-app doc):');
  console.log(`  ${pkg}:/oauth2redirect`);
  console.log('');
  console.log('expo-auth-session default (often rejected as Error 400 invalid_request):');
  console.log(`  ${pkg}:/oauthredirect`);
  console.log('');
  if (!androidCid) {
    console.log('Issue: EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID is missing for native Android.');
  } else if (!androidCid.endsWith('.apps.googleusercontent.com')) {
    console.log('Warning: Android client id should end with .apps.googleusercontent.com');
  } else {
    console.log('Android client id suffix looks OK.');
  }
  console.log('');
  console.log(
    'SHA-1: run from repo: cd mobile/android && ./gradlew signingReport (use Variant: debug for local emulator).'
  );
  console.log('GCP Android OAuth client must list this package and the same SHA-1.');
}

main();
