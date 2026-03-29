/**
 * Reads birth year from Google People API when the account has
 * user.birthday.read scope. Returns null if unavailable or denied.
 */
export async function fetchGoogleBirthYear(accessToken) {
  if (!accessToken || typeof accessToken !== 'string') return null
  try {
    const url =
      'https://people.googleapis.com/v1/people/me?personFields=birthdays'
    const r = await fetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!r.ok) return null
    const data = await r.json()
    const birthdays = data.birthdays || []
    for (const b of birthdays) {
      const y = b.date?.year
      if (typeof y === 'number' && y >= 1900 && y <= new Date().getFullYear()) {
        return y
      }
    }
    return null
  } catch {
    return null
  }
}
