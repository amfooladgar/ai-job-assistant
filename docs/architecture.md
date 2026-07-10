# 🏗️ Architecture Design - AI Job Scout Agent

This document explains the architecture, modular layout, local-first design considerations, and planned future integrations for the AI Job Scout Agent.

---

## 🔄 Agent Pipeline

The execution flow of the agent is modeled as an automated, linear pipeline. Running the orchestrator invokes these 7 distinct stages sequentially:

```
[Start]
   │
   ▼
[1. Fetch Listings] ────────► Queries local sources, APIs, or a specific user-provided 
   │                          URL (via `UrlJobSource` utilizing BeautifulSoup & Gemini).
   ▼
[2. Extract Metadata] ──────► Uses Gemini to extract structured fields (e.g., job title,
   │                          company name, location, description, required skills).
   ▼
[3. Match & Rank] ──────────► Scores job postings based on candidate's user profile
   │                          using keyword and semantic similarity heuristics.
   ▼
[4. Profile Resumes] ───────► Scans the resumes folder, computes a SHA-256 content hash, 
   │                          and checks cache. Uses LLM to extract resume details 
   │                          and caches them in SQLite if new/changed.
   ▼
[5. Select Best Resume] ────► Automatically evaluates cached/parsed resume profiles
   │                          and selects the best resume for the posting.
   ▼
[6. ATS Tailoring] ─────────► Compares chosen resume with the job post to suggest
   │                          non-fabricated keyword updates and bullet improvements.
   ▼
[7. Persist & Notify] ──────► Writes matched postings, selected resume references, 
   │                          and ATS recommendations to SQLite and logs CLI summary.
   ▼
 [End]
```

---

## 📂 Modules & System Layout

The codebase uses clean, object-oriented design patterns within a modular directory structure:

### 1. Main Orchestrator (`src/agent/scout.py`)
The `JobScoutAgent` class represents the brain of the project. It handles:
*   Resolving environment configuration settings.
*   Loading the candidate's YAML user profile.
*   Integrating the `UrlJobSource` to fetch specific links.
*   Coordinating `ResumeSelectorAgent` and `AtsTailorAgent` workflows.

### 2. User Profile Model (`src/config/profile.py`)
Defines the `UserProfile` Pydantic schema which parses and validates `config/user_profile.yaml` at startup.

### 3. Job Matcher Heuristics (`src/ranking/matcher.py`)
The `JobMatcher` handles scoring. The match score ($S_{match}$) is defined as:
\[S_{match} = 0.3 \cdot S_{role} + 0.4 \cdot S_{skills} + 0.3 \cdot S_{keywords} - P_{avoid}\]

### 4. Storage & Caching Engine (`src/storage/db.py`)
Manages SQLite operations. In addition to persisting matched job postings in the `jobs` table, the `JobDatabase` now maintains a `resumes` caching table to save extracted resume profiles mapped by filename and SHA-256 content hash.

### 5. Multi-Format Source Ingestion (`src/sources/url_source.py`)
Fetches raw HTML pages using `httpx`, strips script/style tags with `BeautifulSoup`, and extracts structured fields via Gemini into a Pydantic `JobPosting` model.

### 6. Resume Selector Agent (`src/agents/resume_selector_agent.py`)
Scans the resumes folder (reading `.txt`, `.md`, `.json`, `.pdf`, `.docx` files), computes content hashes, checks the DB cache, extracts profiles using Gemini when cache misses, and matches the target job with the optimal candidate profile.

### 7. ATS Tailoring Agent (`src/agents/ats_tailor_agent.py`)
Compares the chosen resume with the job requirements. Suggests customized bullet point rephrasings, matched/missing keywords, and a tailored professional summary **without fabricating any experience**.

---

## 🤖 Multi-Agent Scaffold Design

To prepare for Gemini-powered reasoning and autonomous decision making, the single orchestrator pipeline is decoupled into a collaborative **multi-agent team** under `src/agents/`:

```
                 [OrchestratorAgent]
                /   /      |      \   \
               /   /       |       \   \
              ▼   ▼        ▼        ▼   ▼
     [SearchAgent]   [RankingAgent]  [ResumeSelectorAgent]
           |               |                 |
     [ProfileAgent]  [NotificationAgent] [AtsTailorAgent]
```

Each agent has a dedicated cognitive boundary and execution scope:
*   **`SearchAgent`**: Manages active crawler/source listings collection.
*   **`ProfileAgent`**: Parses YAML configuration parameters.
*   **`RankingAgent`**: Scores job postings relevance.
*   **`ResumeSelectorAgent`**: Computes hashes, verifies database caches, profiles new documents, and selects the best matching resume file.
*   **`AtsTailorAgent`**: Evaluates alignment and generates ATS improvement suggestions without fabrication.
*   **`NotificationAgent`**: Formats console logs and outputs.
*   **`OrchestratorAgent`**: Coordinates multi-agent workflows and variables passing.

This multi-agent team supports the Google Agent Development Kit (ADK) under `src/adk/`. A unified `RootAgent` (an ADK `SequentialAgent`) orchestrates ADK wrappers completely offline.

---

## 🔒 Local-First Design & Cache Control

To align with a **local-first capstone philosophy**, the project implements:
*   **Zero External Run-Dependencies**: All mock objects and mock schemas are packaged directly. PDF/DOCX dependencies (`pypdf`, `python-docx`) are installed in the local virtual environment.
*   **Persistent Resume Profiling Cache**: Resume files are indexed using content hashes. Parsed profiles are stored in SQLite so the LLM is only called if file content changes, controlling token consumption.
*   **File-Based SQLite Storage**: sandboxed database in `data/job_scout.db`.

---

## 📡 Future Real Job-Source Integrations

In Phase 2, the search agents will be augmented with:
1.  **LinkedIn Search Scraper**: Authenticated HTTP client using BeautifulSoup to parse public LinkedIn jobs.
2.  **Indeed API / Scraper**: Requests to scrape job cards matching target location search criteria.
3.  **Google Search API / custom search engine**: Search queries for remote AI roles matching `target_roles` and returning parsed text.
4.  **Gemini Extraction Model**: Feeding scraped HTML payloads directly into a Gemini model using the Google GenAI SDK (`google-genai`) with structured schema matching (`response_schema=JobPosting`) to guarantee structured outputs.
