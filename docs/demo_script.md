# 🎬 Demo Script - AI Job Scout Agent

This script outlines a 2-minute video demonstration highlighting the functionality of the AI Job Scout Agent for the capstone project submission.

---

## ⏱️ Video Breakdown

*   **0:00 - 0:25**: Introduction & Project Goal
*   **0:25 - 0:50**: User Profile & Configuration
*   **0:50 - 1:20**: CLI Execution (Default & Overrides)
*   **1:20 - 1:45**: Database Persistence & Verification
*   **1:45 - 2:00**: Conclusion & Next Steps

---

## 🎙️ Transcript & Visual Actions

### 1. Introduction & Project Goal (0:00 - 0:25)
*   **Visual**: Show `README.md` or the terminal.
*   **Audio**: *"Hello! Today I'm demonstrating the AI Job Scout Agent, a local-first autonomous job-hunting assistant developed for my Kaggle/Google Agentic AI capstone project. The goal is simple: automate the search for AI/ML roles by scraping listings, parsing their contents, ranking them against a personalized candidate profile, and persisting the best matches."*

### 2. User Profile Configuration (0:25 - 0:50)
*   **Visual**: Open `config/user_profile.yaml` in the IDE.
*   **Audio**: *"The agent is driven by a local configuration file, user_profile.yaml. Here, a candidate lists their target roles, programming skills, frameworks, and keywords. I've populated this with a PhD graduate profile seeking AI Research or ML Engineer roles, requiring frameworks like PyTorch and avoiding legacy stacks like Enterprise Java. We also set a minimum match score threshold of 0.75."*

### 3. CLI Execution & Overrides (0:50 - 1:20)
*   **Visual**: Open the terminal and run `python3 main.py`.
*   **Audio**: *"Let's run the agent pipeline. I'll execute `python3 main.py`. The agent starts, reads our YAML, loads 5 sample job listings, scores them, and filters them. Since our threshold is 0.75, only 2 postings clear the bar—Autonomous Systems Corp at 0.78 and DeepMind at 0.76. The console prints this beautiful matched summary."*
*   **Visual**: Run `python3 main.py --min-score 0.65`.
*   **Audio**: *"If we want to broaden our search, we can use the CLI override: `python3 main.py --min-score 0.65`. Now, the threshold is lowered, and the agent matches a third listing: the Applied Scientist Computer Vision role at 0.68. It calculates the scores on-the-fly and processes the new items."*

### 4. Database Persistence & Verification (1:20 - 1:45)
*   **Visual**: Run `pytest` in the terminal.
*   **Audio**: *"Behind the scenes, the agent records the matched jobs in a local SQLite database, data/job_scout.db. It serializes the required skills list and uses the URL as a unique key to prevent duplicate records if we rerun the script. To verify the entire system, I'll run the unit tests. Pytest executes 17 test cases, checking YAML loaders, scoring algorithms, and database duplicate checks. Everything passes in under 0.2 seconds."*

### 5. Conclusion & Next Steps (1:45 - 2:00)
*   **Visual**: Show the Architecture diagram or `README.md` roadmap.
*   **Audio**: *"This establishes a solid, local-first foundation. The next phase will replace the mock data source with active web scrapers and deploy the Google GenAI SDK to use Gemini for semantic matching and description parsing. Thank you for watching!"*
