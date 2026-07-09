// Anonymous per-browser identity used ONLY to keep each person's interview
// history private to their own browser (no login system exists, so this is
// the lightweight alternative). Generated once, then reused forever from
// localStorage. Not real authentication - see the note in app/history.py.
const STORAGE_KEY = "interview_coach_client_id";

export function getClientId() {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}