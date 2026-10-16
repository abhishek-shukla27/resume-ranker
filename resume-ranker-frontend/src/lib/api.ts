import { getIdToken } from "./firebase";
import type { AnalysisResult, ParsedResume } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);

async function authHeader(): Promise<Record<string, string>> {
  const token = await getIdToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail))
      return data.detail.map((d: { msg?: string }) => d.msg).join(", ");
    return JSON.stringify(data);
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function analyzeResume(
  file: File,
  jobDescription: string,
): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("job_description", jobDescription);

  const res = await fetch(`${API_URL}/api/analyze`, {
    method: "POST",
    headers: { ...(await authHeader()) },
    body: form,
  });

  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as AnalysisResult;
}

export async function transformResume(
  parsedResume: ParsedResume,
  jobDescription: string,
): Promise<Blob> {
  const res = await fetch(`${API_URL}/api/transform`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeader()),
    },
    body: JSON.stringify({
      parsed_resume: parsedResume,
      job_description: jobDescription,
    }),
  });

  if (!res.ok) throw new Error(await parseError(res));
  return await res.blob();
}

export async function submitFeedback(
  rating: string,
  comments: string,
): Promise<void> {
  const res = await fetch(`${API_URL}/api/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeader()),
    },
    body: JSON.stringify({ rating, comments }),
  });

  if (!res.ok) throw new Error(await parseError(res));
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
