import type { Metadata } from "next";
import { Dashboard } from "@/components/Dashboard";

export const metadata: Metadata = {
  title: "Dashboard - Resume Ranker",
  description:
    "Upload your resume, paste a job description, and get ATS scoring plus AI suggestions.",
};

export default function DashboardPage() {
  return <Dashboard />;
}
