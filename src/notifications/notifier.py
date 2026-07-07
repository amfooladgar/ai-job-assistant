import logging
from typing import List
from src.sources.base import JobPosting

logger = logging.getLogger(__name__)

class JobNotifier:
    """Dispatches notifications (e.g. CLI, Email, Slack) for high-match job postings."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def send_notification(self, job: JobPosting, match_score: float) -> bool:
        """Sends a notification about a matching job posting."""
        message = f"🔔 High Match Job Found: {job.title} at {job.company} (Match Score: {match_score:.2f}) - {job.url}"
        logger.info(f"Notification Sent: {message}")
        return True
        
    def summarize_matches(self, matched_jobs: List[JobPosting]) -> str:
        """Returns a readable text summary of matched jobs."""
        if not matched_jobs:
            return "No matched jobs found."
            
        lines = [
            "==================================================",
            "📢 AI JOB SCOUT: NEW MATCHES FOUND!",
            "=================================================="
        ]
        for idx, job in enumerate(matched_jobs, 1):
            score_val = job.match_score if job.match_score is not None else 0.0
            lines.append(
                f"{idx}. {job.title} at {job.company}\n"
                f"   📍 Location: {job.location}\n"
                f"   📊 Match Score: {score_val:.2f}\n"
                f"   🔗 Link: {job.url}"
            )
            
            fit_analysis = job.extracted_metadata.get("fit_analysis") if job.extracted_metadata else None
            if fit_analysis:
                strengths_val = fit_analysis.get('strengths', [])
                strengths_str = ", ".join(strengths_val) if isinstance(strengths_val, list) else str(strengths_val)
                
                gaps_val = fit_analysis.get('gaps', [])
                gaps_str = ", ".join(gaps_val) if isinstance(gaps_val, list) else str(gaps_val)
                
                lines.append(
                    f"   🧠 LLM Fit Summary: {fit_analysis.get('fit_summary')}\n"
                    f"   💪 Strengths: {strengths_str}\n"
                    f"   ⚠️ Gaps: {gaps_str}\n"
                    f"   🎯 Apply Recommendation: {fit_analysis.get('apply_recommendation')}\n"
                    f"   ⭐️ Confidence Score: {fit_analysis.get('confidence_score', 0.0):.2f}"
                )
                
            selected_resume = job.extracted_metadata.get("selected_resume") if job.extracted_metadata else None
            if selected_resume:
                lines.append(
                    f"   📄 Selected Resume: {selected_resume.get('filename')}\n"
                    f"   💬 Selection Reason: {selected_resume.get('selection_reasoning')}"
                )
                
            ats_tailor = job.extracted_metadata.get("ats_tailor") if job.extracted_metadata else None
            if ats_tailor:
                matched_kws = ", ".join(ats_tailor.get("matched_keywords", []))
                missing_kws = ", ".join(ats_tailor.get("missing_keywords", []))
                lines.append(
                    f"   📈 ATS Matched Keywords: {matched_kws}\n"
                    f"   📉 ATS Missing Keywords: {missing_kws}\n"
                    f"   📝 Suggested Summary:\n       {ats_tailor.get('suggested_summary')}\n"
                    f"   🔧 Bullet Point Improvements:"
                )
                for imp in ats_tailor.get("bullet_point_improvements", []):
                    lines.append(
                        f"       • Original: \"{imp.get('original')}\"\n"
                        f"         Suggested: \"{imp.get('suggested')}\"\n"
                        f"         Rationale: {imp.get('rationale')}"
                    )
                lines.append("   📋 General Recommendations:")
                for rec in ats_tailor.get("general_recommendations", []):
                    lines.append(f"       • {rec}")
            lines.append("")
        lines.append("==================================================")
        return "\n".join(lines)

