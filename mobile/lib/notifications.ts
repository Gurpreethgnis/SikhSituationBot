import * as Device from 'expo-device';
import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { apiBase, authHeaders } from './api';

// Helper function to check if running in Expo Go
function isRunningInExpoGo(): boolean {
  // Check multiple ways to detect Expo Go
  const ownership = Constants.appOwnership;
  return ownership === 'expo' || ownership === undefined;
}

// ---------------------------------------------------------------------------
// Global notification handler (call once at app startup)
// ---------------------------------------------------------------------------
export async function configureNotifications() {
  // Skip all notification setup in Expo Go to avoid auto-registration errors
  if (isRunningInExpoGo()) {
    console.log('Notifications disabled in Expo Go - use a development build for full functionality');
    return;
  }
  
  try {
    const Notifications = await import('expo-notifications');
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
        shouldShowBanner: true,
        shouldShowList: true,
      }),
    });
  } catch (error) {
    console.warn('Failed to configure notifications:', error);
  }
}

// ---------------------------------------------------------------------------
// Register for push notifications + sync token to backend
// ---------------------------------------------------------------------------
export async function registerForPushNotifications(token: string | null): Promise<string | null> {
  // Push notifications don't work in Expo Go (SDK 53+)
  if (isRunningInExpoGo()) {
    console.log('Push notifications skipped in Expo Go');
    return null;
  }

  if (!Device.isDevice) {
    return null;
  }

  try {
    const Notifications = await import('expo-notifications');
    
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      return null;
    }

    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    if (!projectId) {
      console.warn('No EAS projectId found - push notifications will not work');
      return null;
    }
    
    const pushToken = (await Notifications.getExpoPushTokenAsync({ projectId })).data;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'Giani Ji',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#9b5de5',
      });
    }

    if (token && pushToken) {
      try {
        const base = apiBase();
        await fetch(`${base}/api/push-token`, {
          method: 'POST',
          headers: authHeaders(token),
          body: JSON.stringify({ push_token: pushToken, platform: Platform.OS }),
        });
      } catch {
        // Non-fatal
      }
    }

    return pushToken;
  } catch (error) {
    console.warn('Push notification registration failed:', error);
    return null;
  }
}

// ---------------------------------------------------------------------------
// Schedule a local "Daily Gurbani" reminder
// ---------------------------------------------------------------------------
export async function scheduleDailyGurbaniReminder(hour = 7, minute = 0) {
  if (isRunningInExpoGo()) {
    console.log('Local notifications limited in Expo Go');
    return;
  }
  
  try {
    const Notifications = await import('expo-notifications');
    await Notifications.cancelAllScheduledNotificationsAsync();
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '☬ Daily Gurbani',
        body: 'Open Giani Ji for your morning reflection',
        sound: true,
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DAILY,
        hour,
        minute,
      },
    });
  } catch (error) {
    console.warn('Failed to schedule notification:', error);
  }
}
