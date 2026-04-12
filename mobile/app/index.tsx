import { Redirect } from 'expo-router';

/**
 * Initial route: declarative redirect only. Do not use `router.replace` in
 * `useEffect` here — it runs before the root navigator mounts and triggers
 * "Attempted to navigate before mounting the Root Layout component".
 */
export default function Index() {
  return <Redirect href="/(auth)/login" />;
}
