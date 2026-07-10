# 🎬 Demo Script - AI Job Scout Agent

This script outlines a 2.5-minute video demonstration highlighting the functionality of the AI Job Scout Agent (including the multi-resume cache selector and ATS tailoring) for the capstone project submission.

---

## ⏱️ Video Breakdown

*   **0:00 - 0:25**: Introduction & Project Goal
*   **0:25 - 0:50**: User Profile & Configuration (Resumes Folder)
*   **0:50 - 1:20**: Direct Ingestion via Job URL
*   **1:20 - 2:00**: Resume Selector Agent & Database Caching
*   **2:00 - 2:30**: Automated Testing & Conclusion

---

## 🎙️ Transcript & Visual Actions

### 1. Introduction & Project Goal (0:00 - 0:25)
*   **Visual**: Show `README.md` or the terminal.
*   **Audio**: *"Hello! Today I'm demonstrating the AI Job Scout Agent, a local-first autonomous job-hunting assistant developed for my Kaggle/Google Agentic AI capstone project. The goal is simple: automate the job hunt by scraping postings, selecting the best resume from a folder of templates, and generating ATS-optimized suggestions without fabricating details."*

### 2. Configuration & Resumes Folder (0:25 - 0:50)
*   **Visual**: Open `config/user_profile.yaml` and the `data/resumes/` folder containing files like `alex_ml_engineer.txt` and `alex_frontend_developer.txt`.
*   **Audio**: *"The agent is driven by a local configuration file, user_profile.yaml. In addition, the user provides a resumes folder supporting txt, markdown, json, pdf, and docx. I have set up two sample resumes here: an ML Engineer resume and a Frontend Developer resume. The agent parses these technical files, extracting candidates' skills, education, and target roles."*

### 3. Direct Job URL Ingestion & Scraping (0:50 - 1:20)
*   **Visual**: Run `.venv/bin/python3 main.py --job-url "https://www.arbeitnow.com"` in the terminal.
*   **Audio**: *"The agent lets you pass a specific job listing URL directly via the CLI: main.py --job-url. The agent scrapes the webpage using httpx, extracts the text using BeautifulSoup, and parses it into a structured JobPosting model. This bypasses minimum score thresholds, so you immediately get details, relevance, and tailoring suggestions for that specific link."*

### 4. Resume Selector, ATS Tailoring & SQLite Caching (1:20 - 2:00)
*   **Visual**: Scroll through the console output showing the Selected Resume (e.g. `alex_ml_engineer.txt`), the Selection Reason, the ATS Matched/Missing keywords, the suggested tailored summary, and the bullet improvements.
*   **Audio**: *"Once the job posting is parsed, the Resume Selector Agent compares its requirements against all parsed resumes to select the best one. To keep this process cost-controlled, the agent hashes the content of each resume. If it matches a record in our resumes database table, it loads the parsed profile directly, saving LLM calls. After selecting the resume, the ATS Optimizer Agent suggests specific, non-fabricated rephrasings and keyword highlights to boost ATS score."*

### 5. Automated Testing & Conclusion (2:00 - 2:30)
*   **Visual**: Run `.venv/bin/pytest` in the terminal showing 47 passing tests.
*   **Audio**: *"To verify correctness, I'll run the unit tests. Pytest executes 47 test cases—validating URL scraping, hash caches, and resume selection. All tests pass in under 2 seconds. The AI Job Scout Agent provides a private, fast, and cost-controlled pipeline for developers to tailor applications dynamically. Thank you for watching!"*
