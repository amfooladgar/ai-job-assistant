import argparse
import sys
from src.config.settings import Settings
from src.agent.scout import JobScoutAgent

def run_health_check():
    print("==================================================")
    print("🏥 Running AI Job Scout Agent Diagnostics...")
    print("==================================================")
    
    passed = True
    checks = {}
    
    # 1. Check user_profile.yaml
    try:
        from src.config.profile import load_user_profile
        from src.config.settings import Settings
        settings = Settings()
        profile = load_user_profile(settings.user_profile_path)
        checks["User Profile Loaded"] = ("PASS", f"Roles: {', '.join(profile.target_roles)}")
    except Exception as e:
        passed = False
        checks["User Profile Loaded"] = ("FAIL", str(e))
        
    # 2. Check sample_jobs.json
    try:
        from src.sources.sample_source import SampleJobSource
        source = SampleJobSource(settings.sample_jobs_path)
        jobs = source.search_jobs("", limit=10)
        checks["Sample Jobs Loaded"] = ("PASS", f"Loaded {len(jobs)} postings.")
    except Exception as e:
        passed = False
        checks["Sample Jobs Loaded"] = ("FAIL", str(e))
        
    # 3. Check SQLite database initialization
    try:
        from src.storage.db import JobDatabase
        db = JobDatabase(settings.db_path)
        checks["SQLite DB Initialized"] = ("PASS", f"Database path: {settings.db_path}")
    except Exception as e:
        passed = False
        checks["SQLite DB Initialized"] = ("FAIL", str(e))
        
    # 4. Check ranking pipeline run
    try:
        from src.ranking.matcher import JobMatcher
        matcher = JobMatcher(profile)
        ranked = matcher.rank_jobs(jobs)
        checks["Ranking Heuristics Execution"] = ("PASS", f"Ranked {len(ranked)} jobs successfully.")
    except Exception as e:
        passed = False
        checks["Ranking Heuristics Execution"] = ("FAIL", str(e))
        
    # Print summary
    print("\nDiagnostic Results:")
    for name, (status, detail) in checks.items():
        print(f"  [{status}] {name}: {detail}")
    print("==================================================")
    
    if passed:
        print("✅ HEALTH CHECK STATUS: ALL PASSED")
    else:
        print("❌ HEALTH CHECK STATUS: FAILED")
    print("==================================================")
    
    return passed

def main(argv=None):
    parser = argparse.ArgumentParser(description="AI Job Scout Agent CLI")
    parser.add_argument(
        "--source",
        type=str,
        default="sample",
        help="Job search source to run (default: sample)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        help="Override the minimum match score threshold"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run health check and diagnostics on project configurations"
    )
    parser.add_argument(
        "--enable-llm-reasoning",
        action="store_true",
        help="Enable optional Gemini-based job fit reasoning"
    )
    parser.add_argument(
        "--job-url",
        type=str,
        help="Specific job posting URL to fetch, match, and tailor resumes for"
    )
    
    args = parser.parse_args(argv)
    
    if args.health_check:
        success = run_health_check()
        if argv is not None:
            return success
        sys.exit(0 if success else 1)
        
    enable_llm = args.enable_llm_reasoning
    if enable_llm:
        from src.llm.gemini_client import GeminiClient
        client = GeminiClient()
        if not client.is_configured():
            print("⚠️ WARNING: --enable-llm-reasoning is enabled but Gemini API key is not configured.")
            print("Placeholder reasoning will be used instead.")
            enable_llm = False

    print("==================================================")
    print("🤖 Starting AI Job Scout Agent...")
    if args.job_url:
        print(f"📡 Target URL: {args.job_url}")
    else:
        print(f"📡 Selected Source: {args.source}")
    if args.min_score is not None:
        print(f"📊 Override Min Match Score: {args.min_score}")
    print(f"🧠 LLM Reasoning: {'Enabled' if enable_llm else 'Disabled'}")
    print("==================================================")
    
    settings = Settings()
    agent = JobScoutAgent(
        settings,
        enable_llm_reasoning=enable_llm,
        source_name=args.source,
        job_url=args.job_url
    )
    
    # Override match score if specified via CLI
    if args.min_score is not None:
        agent.profile.minimum_match_score = args.min_score
        
    print(f"🎯 Target Roles: {', '.join(agent.profile.target_roles)}")
    if not args.job_url:
        print(f"📊 Minimum Match Score: {agent.profile.minimum_match_score}")

    print("==================================================")
    
    # Run the main agent pipeline loop
    agent.run()
    
    print("==================================================")
    print("🤖 Agent execution finished.")
    print("==================================================")
    
    return agent

if __name__ == "__main__":
    main()
