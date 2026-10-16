# Resume Ranker - AI-Powered Resume Analysis & Optimization Tool

[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-UI-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Resume Ranker** is an AI-driven web application that analyzes resumes against job descriptions and provides actionable feedback to improve your chances of getting noticed by recruiters.

---

## 🔹 Features

- **Resume Scoring:** Get a comprehensive ATS-compatible score for your resume based on the job description.
- **Keyword Matching:** Highlights missing or underrepresented keywords and skills compared to the job description.
- **Content Suggestions:** Recommendations to improve language, structure, and relevance.
- **Section Analysis:** Evaluates experience, education, skills, and certifications for completeness and impact.
- **Secure Login:** Users can sign up and log in securely to track their resume analyses.
- **Premium Features (Upcoming):** Advanced scoring, downloadable reports, and personalized optimization tips.

---

## 🖥️ Demo / Screenshots

### Upload & Analysis
![Login Page](img/screenshot-11.png)
![Upload Resume](img/screenshot-12.png)

### Resume Score & Suggestions
![Resume Score](screenshots/score.png)

> 

---

## ⚙️ Tech Stack

- **Frontend:** Next.js (React + Tailwind CSS)
- **Backend:** FastAPI / Python  
- **AI Models:** Groq API with GPT-OSS / Mixtral for fast NLP processing  
- **Authentication:** Firebase Auth (Web SDK + Admin SDK)  
- **Database:** Firestore  

---

## 🚀 How It Works

1. **Upload Resume & Job Description:** Users upload their resume and the corresponding job description.
2. **Analysis:** The AI model analyzes the resume for keyword alignment, formatting, and content relevance.
3. **Score & Suggestions:** Users receive a score and actionable suggestions to improve their resume.
4. **Transform Your Resume Into AN ATS-Friendly Format:**  Users can transform there resume according to JD into ATS friendly template.

---

## 💻 Setup & Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/your-username/resume-ranker.git
   cd resume-ranker
   ```

2. Backend (FastAPI):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux / Mac
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

3. Frontend (Next.js):
   ```bash
   cd resume-ranker-frontend
   npm install
   # copy .env.example to .env.local and fill in the values
   npm run dev
   ```

   Open http://localhost:3000

> See [MIGRATION.md](MIGRATION.md) for details on the Streamlit → Next.js migration.

---
## 🔮Future Enhancements

-**Add payment gateway for premium features**.

-**Real-time AI suggestions while editing the resume**.

-**Multi-language resume optimization.**

-**LinkedIn integration for automatic suggestions.**

## 🤝 Contributing

-Contributions are welcome! To contribute:

-Fork the repository.

-Create a branch (git checkout -b feature-name).

-Commit your changes (git commit -m 'Add some feature').

-Push to the branch (git push origin feature-name).

-Open a pull request.

## 📄 License

This project is licensed under the MIT License. See LICENSE
for details.

## 📫 Contact

Developer: Abhishek Shukla

-Email:abhishekshukla2711@gmail.com

-LinkedIn:(www.linkedin.com/in/abhishek-shukla-062164299)

## 🌐 Live Demo

[Live Link](https://resume-ranker-auth.web.app/)