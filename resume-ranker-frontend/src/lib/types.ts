export type ResumeExperience = {
  role: string;
  company: string;
  duration: string;
  details: string[];
};

export type ResumeProject = {
  name: string;
  tech: string;
  details: string[];
};

export type ResumeEducation = {
  degree: string;
  university: string;
  year: string;
};

export type ParsedResume = {
  name: string;
  contact: string;
  summary: string;
  skills: string[];
  experience: ResumeExperience[];
  projects: ResumeProject[];
  education: ResumeEducation[] | string;
  certifications: string[];
};

export type AnalysisResult = {
  ats_score: number | string;
  match_score: number | string;
  strengths: string[];
  improvements: string[];
  overall: string;
  resume_text: string;
  parsed_resume: ParsedResume;
};
