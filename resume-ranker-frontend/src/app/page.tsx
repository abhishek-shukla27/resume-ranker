import { Header } from "@/components/Header";
import { LoginButton } from "@/components/LoginButton";

const features = [
  {
    icon: "📄",
    title: "Smart Resume Parsing",
    body: "Upload your PDF resume and let our parser extract your details cleanly for analysis.",
  },
  {
    icon: "📊",
    title: "ATS Match Score",
    body: "Get a detailed ATS score to understand how well your resume fits the job description.",
  },
  {
    icon: "🤖",
    title: "AI-Powered Suggestions",
    body: "Receive instant feedback on strengths and gaps to tailor your resume for each role.",
  },
  {
    icon: "🚀",
    title: "ATS-Friendly Rewrite",
    body: "Transform your resume into a clean, ATS-optimized template and download it as .docx.",
  },
];

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />

      <main className="flex-1">
        <section className="px-[5%] py-16 text-center">
          <div className="mx-auto max-w-3xl">
            <p className="mb-4 inline-block rounded-full border border-white/15 px-4 py-1 text-xs uppercase tracking-widest text-brand">
              AI Resume Optimization
            </p>
            <h1 className="text-4xl font-extrabold leading-tight sm:text-6xl">
              Boost Your Resume <span className="text-gradient">Instantly</span>
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg text-slate-300">
              Upload your resume, paste the job description, and let AI enhance your
              job-match potential.
            </p>
            <div className="mt-10">
              <LoginButton />
            </div>
          </div>
        </section>

        <section
          id="features"
          className="grid gap-6 px-[5%] py-16 sm:grid-cols-2 lg:grid-cols-4"
        >
          {features.map((f) => (
            <div
              key={f.title}
              className="glass-card p-7 text-center transition hover:-translate-y-1"
            >
              <div className="mb-3 text-3xl">{f.icon}</div>
              <h3 className="mb-2 text-lg font-semibold text-brand">{f.title}</h3>
              <p className="text-sm text-slate-300">{f.body}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-white/10 px-[5%] py-6 text-center text-sm text-slate-400">
        Built with ❤️ | © Resume-Ranker. All rights reserved.
      </footer>
    </div>
  );
}
