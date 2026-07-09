import { getClientId } from "../utils/clientId.js";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function throwForResponse(res, fallbackMessage) {
  let detail = fallbackMessage;
  let retryAfterSeconds = null;
  try {
    const body = await res.json();
    if (typeof body.detail === "string") {
      detail = body.detail;
    } else if (body.detail && typeof body.detail === "object") {
      detail = body.detail.message || fallbackMessage;
      retryAfterSeconds = body.detail.retry_after_seconds ?? null;
    }
  } catch {
    // response wasn't JSON - keep the fallback message
  }
  const error = new Error(detail);
  error.retryAfterSeconds = retryAfterSeconds;
  error.status = res.status;
  throw error;
}

export async function startSession({ resumeFile, jdFile, jdText, clientId }) {
  const form = new FormData();
  form.append("resume", resumeFile);
  if (jdFile) form.append("jd", jdFile);
  if (jdText) form.append("jd_text", jdText);
  form.append("client_id", clientId ?? getClientId());

  const res = await fetch(`${BASE_URL}/api/session/start`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) await throwForResponse(res, "Failed to start session");
  return res.json();
}

export async function submitAnswer(sessionId, answer, language = null) {
  const res = await fetch(`${BASE_URL}/api/session/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answer, language }),
  });
  if (!res.ok) await throwForResponse(res, "Failed to submit answer");
  return res.json();
}

export async function getSessionState(sessionId) {
  const res = await fetch(`${BASE_URL}/api/session/${sessionId}/state`);
  if (!res.ok) await throwForResponse(res, "Failed to fetch session state");
  return res.json();
}

export async function submitAnswerAudio(sessionId, audioBlob) {
  const form = new FormData();
  form.append("audio", audioBlob, "answer.webm");

  const res = await fetch(`${BASE_URL}/api/session/${sessionId}/answer-audio`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) await throwForResponse(res, "Failed to submit voice answer");
  return res.json();
}

export async function fetchQuestionAudio(text) {
  const res = await fetch(`${BASE_URL}/api/session/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    // Distinguish "key not configured" from an actual ElevenLabs error
    // (bad key, quota, wrong voice/model ID) - previously both showed
    // identically as "add ELEVENLABS_API_KEY", which was misleading
    // whenever a key WAS present but something else was wrong.
    let reason = "not_configured";
    let message = "Voice reading is off - ELEVENLABS_API_KEY isn't set on the backend.";
    try {
      const body = await res.json();
      if (body.detail?.reason) {
        reason = body.detail.reason;
        message = body.detail.message;
      }
    } catch {
      // non-JSON error body - keep the generic message
    }
    return { url: null, reason, message };
  }
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), reason: null, message: null };
}

export async function fetchHistoryList() {
  const res = await fetch(`${BASE_URL}/api/history`, {
    headers: { "X-Client-Id": getClientId() },
  });
  if (!res.ok) await throwForResponse(res, "Failed to fetch interview history");
  return res.json();
}

export async function fetchHistoryRecord(sessionId) {
  const res = await fetch(`${BASE_URL}/api/history/${sessionId}`, {
    headers: { "X-Client-Id": getClientId() },
  });
  if (!res.ok) await throwForResponse(res, "Failed to fetch interview record");
  return res.json();
}