"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import { Header } from "@/components/Header";
import { LoginButton } from "@/components/LoginButton";
import { ScoreRing } from "@/components/ScoreRing";
import { useAuth } from "@/components/AuthProvider";
import {
  analyzeResume,
  downloadBlob,
  submitFeedback,
  transformResume,
} from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

export function Dashboard() {
  const { user, loading } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const [jobDesc, setJobDesc] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [transforming, setTransforming] = useState(false);
  const [transformed, setTransformed] = useState(false);

  const [rating, setRating] = useState("⭐⭐⭐⭐⭐");
  const [comments, setComments] = useState("");
  const [feedbackSent, setFeedbackSent] = useState(false);

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    setFile(e.target.files?.[0] ?? null);
    setResult(null);
    setTransformed(false);
    setError(null);
  }

  async function handleAnalyze() {
    if (!file) {
      setError("Please upload your resume (PDF or DOCX).");
      return;
    }
    if (!jobDesc.trim()) {
      setError("Please paste the job description.");
      return;
    }
    setAnalyzing(true);
    setError(null);
    setResult(null);
    setTransformed(false);
    try {
      const res = await analyzeResume(file, jobDesc);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleTransform() {
    if (!result) return;
    setTransforming(true);
    setError(null);
    try {
      const blob = await transformResume(result.parsed_resume, jobDesc);
      downloadBlob(blob, "updated_resume.docx");
      setTransformed(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Transformation failed.");
    } finally {
      setTransforming(false);
    }
  }

  async function handleFeedback(e: FormEvent) {
    e.preventDefault();
    try {
      await submitFeedback(rating, comments);
      setFeedbackSent(true);
      setComments("");
    } catch {
      setFeedbackSent(true);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex flex-1 items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-white/20 border-t-brand" />
        </main>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex flex-1 items-center justify-center px-4">
          <div className="glass-card max-w-md p-10 text-center">
            <h2 className="mb-3 text-2xl font-bold">Sign in to continue</h2>
            <p className="mb-8 text-slate-300">
              Please log in to use Resume Ranker and track your resume analysis.
            </p>
            <div className="flex justify-center">
              <LoginButton />
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6">
        <h1 className="mb-2 text-3xl font-bold">
          📄 <span className="text-gradient">Resume Ranker</span>
        </h1>
        <p className="mb-8 text-slate-300">
          Upload your resume and paste the job description to get an instant ATS
          score and AI suggestions.
        </p>

        <div className="glass-card mb-6 p-6 sm:p-8">
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-200">
                📄 Upload Your Resume (PDF or DOCX)
              </label>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={onFileChange}
                className="block w-full cursor-pointer rounded-xl border border-white/15 bg-white/5 p-3 text-sm text-slate-200 file:mr-4 file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950 hover:border-brand"
              />
              {file && (
                <p className="mt-2 truncate text-xs text-slate-400">
                  Selected: {file.name}
                </p>
              )}
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-slate-200">
                🧾 Paste Job Description
              </label>
              <textarea
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
                rows={6}
                placeholder="Paste the job description here..."
                className="w-full resize-y rounded-xl border border-white/15 bg-white/5 p-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand focus:outline-none"
              />
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="inline-flex items-center gap-2 rounded-xl bg-brand px-6 py-3 font-semibold text-slate-950 transition hover:bg-brand-dark disabled:opacity-60"
            >
              {analyzing ? "Analyzing..." : "🔍 Get AI Suggestions"}
            </button>
            {result && (
              <button
                onClick={handleTransform}
                disabled={transforming}
                className="inline-flex items-center gap-2 rounded-xl border border-brand/60 bg-brand/10 px-6 py-3 font-semibold text-brand transition hover:bg-brand/20 disabled:opacity-60"
              >
                {transforming ? "Transforming..." : "🚀 Transform My Resume"}
              </button>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}
          {transformed && (
            <div className="mt-4 rounded-xl border border-brand/40 bg-brand/10 px-4 py-3 text-sm text-brand">
              ✅ Resume transformed. Your download should begin automatically.
            </div>
          )}
        </div>

        {result && (
          <div className="space-y-6">
            <div className="glass-card p-6 sm:p-8">
              <h2 className="mb-6 text-xl font-semibold">📊 Analysis Results</h2>
              <div className="flex flex-wrap items-center justify-around gap-8">
                <ScoreRing value={result.ats_score} label="ATS Score" />
                <ScoreRing
                  value={result.match_score}
                  max={10}
                  label="Match Score"
                />
              </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <div className="glass-card p-6">
                <h3 className="mb-3 text-lg font-semibold text-emerald-400">
                  ✅ Strengths
                </h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {result.strengths.length ? (
                    result.strengths.map((s, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-emerald-400">•</span>
                        <span>{s}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">None reported.</li>
                  )}
                </ul>
              </div>

              <div className="glass-card p-6">
                <h3 className="mb-3 text-lg font-semibold text-amber-400">
                  🛠️ Areas to Improve
                </h3>
                <ul className="space-y-2 text-sm text-slate-300">
                  {result.improvements.length ? (
                    result.improvements.map((s, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-amber-400">•</span>
                        <span>{s}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">None reported.</li>
                  )}
                </ul>
              </div>
            </div>

            {result.overall && (
              <div className="glass-card p-6">
                <h3 className="mb-3 text-lg font-semibold">📢 Overall Suggestion</h3>
                <p className="text-sm leading-relaxed text-slate-300">
                  {result.overall}
                </p>
              </div>
            )}
          </div>
        )}

        <div className="mt-8 rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
          ⚠️ <b>Important Notice:</b> These resumes are <b>AI-generated</b> and may
          sometimes contain errors or missing info. Please verify all details before
          using them for job applications.
        </div>

        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold">💬 Share Your Feedback</h2>
          <form onSubmit={handleFeedback} className="glass-card space-y-4 p-6">
            <div>
              <label className="mb-2 block text-sm text-slate-200">
                How helpful was Resume Ranker?
              </label>
              <div className="flex flex-wrap gap-2">
                {["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"].map((r) => (
                  <button
                    type="button"
                    key={r}
                    onClick={() => setRating(r)}
                    className={`rounded-lg border px-3 py-2 text-sm transition ${
                      rating === r
                        ? "border-brand bg-brand/15"
                        : "border-white/15 hover:border-brand/60"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>
            <textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              rows={3}
              placeholder="Tell us what we can improve..."
              className="w-full resize-y rounded-xl border border-white/15 bg-white/5 p-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-brand focus:outline-none"
            />
            <div className="flex items-center gap-4">
              <button
                type="submit"
                className="rounded-xl bg-brand px-6 py-2.5 font-semibold text-slate-950 transition hover:bg-brand-dark"
              >
                Submit Feedback
              </button>
              {feedbackSent && (
                <span className="text-sm text-brand">
                  ✅ Thanks for your feedback!
                </span>
              )}
            </div>
          </form>
        </section>
      </main>

      <footer className="border-t border-white/10 px-[5%] py-6 text-center text-sm text-slate-400">
        Built with ❤️ | © Resume-Ranker. All rights reserved.
      </footer>
    </div>
  );
}
