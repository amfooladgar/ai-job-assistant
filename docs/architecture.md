# 🏗️ Architecture Design - AI Job Scout Agent

This document explains the architecture, modular layout, local-first design considerations, and planned future integrations for the AI Job Scout Agent.

---

## 🔄 Agent Pipeline

The execution flow of the agent is modeled as an automated, linear pipeline. Running the orchestrator invokes these 5 distinct stages sequentially:

```
[Start]
   │
   ▼
[1. Fetch Listings] ────────► Queries local or remote sources (scrapers, APIs)
   │                          to obtain raw job postings.
   ▼
[2. Extract Metadata] ──────► Uses Gemini to extract structured fields
   │                          (e.g., specific skills, remote status) from descriptions.
   ▼
[3. Match & Rank] ──────────► Scores job postings based on candidate's user profile
   │                          using keyword and semantic similarity heuristics.
   ▼
[4. Persist Results] ───────► Writes newly matched postings to SQLite, preventing duplicates
   │                          by checking the UNIQUE URL key constraint.
   ▼
[5. Alert / Dispatch] ──────► Generates formatted outputs and dispatches notifications
   │                          (e.g., console log, email, Slack).
   ▼
 [End]
```

---

## 📂 Modules & System Layout

The codebase uses a clean, object-oriented design patterns within a modular directory structure:

### 1. Main Orchestrator (`src/agent/scout.py`)
The `JobScoutAgent` class represents the brain of the project. It handles:
*   Resolving environment configuration settings.
*   Loading the candidate's YAML user profile.
*   Iterating through the pipeline stages.

### 2. User Profile Model (`src/config/profile.py`)
Defines the `UserProfile` Pydantic schema which parses and validates `config/user_profile.yaml` at startup. It ensures field types are correct and filters out garbage configuration values.

### 3. Job Matcher Heuristics (`src/ranking/matcher.py`)
The `JobMatcher` handles scoring. The match score ($S_{match}$) is defined as:
\[S_{match} = 0.3 \cdot S_{role} + 0.4 \cdot S_{skills} + 0.3 \cdot S_{keywords} - P_{avoid}\]
*   **$S_{role}$ (Role Score)**: Degree of overlap between the job title and user's target roles.
*   **$S_{skills}$ (Skills Score)**: Overlap between the job's required skills and user's profile programming languages, frameworks, and ML concepts.
*   **$S_{keywords}$ (Keywords Score)**: Overlap of user's required and nice-to-have keywords with the job description.
*   **$P_{avoid}$ (Avoid Stack Penalty)**: Penalty subtracted if keywords from user's `avoid_keywords` list (e.g. Java, PHP, Frontend) are present.

### 4. Storage Engine (`src/storage/db.py`)
Manages SQLite operations. The `JobDatabase` initializes the table and manages persistence. Column definitions include serializing lists to JSON strings to maintain relational simplicity in a single file.

### 5. Notification Dispatcher (`src/notifications/notifier.py`)
Formats alert outputs and manages notification payloads. Generates CLI printouts and handles future integrations with Slack or SMTP mail.

---

## 🤖 Multi-Agent Scaffold Design

To prepare for future Gemini-powered reasoning and autonomous decision making, the single orchestrator pipeline is decoupled into a collaborative **multi-agent team** under `src/agents/`:

```
           [OrchestratorAgent]
             /      |      \
            /       |       \
           ▼        ▼        ▼
    [SearchAgent] [ProfileAgent] [RankingAgent]
                            \
                             ▼
                     [NotificationAgent]
```

Each agent has a dedicated cognitive boundary and execution scope:
*   **`SearchAgent`**: Manages the ingestion logic. Interacts with the active scraper sources and fetches listings.
*   **`ProfileAgent`**: Loads, validates, and builds semantic embeddings or summaries of user preferences.
*   **`RankingAgent`**: Connects to matching heuristics or LLMs to rank jobs by relevance score.
*   **`NotificationAgent`**: Generates notification text templates and controls delivery triggers.
*   **`OrchestratorAgent`**: The central coordinator that feeds outputs between sub-agents and schedules execution loops.

This multi-agent team has been refactored to support **Google's Agent Development Kit (ADK)** under `src/adk/`. A unified `RootAgent` (an ADK `SequentialAgent`) orchestrates ADK wrappers (`ProfileAdkAgent`, `SearchAdkAgent`, `RankingAdkAgent`, `NotificationAdkAgent`) completely offline. In future iterations, they will be connected to the Google GenAI SDK (`google-genai`) to replace keyword heuristics with Gemini-powered agentic reasoning.

---

## 🔒 Local-First Design

To align with a **local-first capstone philosophy**, the project implements the following principles:
*   **Zero External Run-Dependencies**: All mock objects and mock schemas are packaged directly within the project. It executes out-of-the-box using python virtual environments.
*   **File-Based SQLite Storage**: No external database instances (like Postgres or MySQL) are required. Data is maintained in `data/job_scout.db`, keeping everything sandboxed.
*   **Decoupled Configuration**: Matching criteria is separated into `config/user_profile.yaml` so the candidate doesn't need to rebuild or touch code to adjust target profiles.

---

## 📡 Future Real Job-Source Integrations

In Phase 2, the static `SampleJobSource` will be augmented with active crawlers:
1.  **LinkedIn Search Scraper**: Authenticated HTTP client using BeautifulSoup to parse public LinkedIn jobs.
2.  **Indeed API / Scraper**: Requests to scrape job cards matching target location search criteria.
3.  **Google Search API / custom search engine**: Search queries for remote AI roles matching `target_roles` and returning parsed text.
4.  **Gemini Extraction Model**: Feeding scraped HTML payloads directly into a Gemini model using the Google GenAI SDK (`google-genai`) with structured schema matching (`response_schema=JobPosting`) to guarantee structured outputs.
