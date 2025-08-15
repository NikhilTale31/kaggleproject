"""Format vulnerabilities for competition submission."""

import json
from datetime import datetime
from typing import Dict, List, Any
import uuid

class FindingsFormatter:
    """Format vulnerability findings for competition submission."""
    
    @staticmethod
    def create_finding(
        issue_title: str,
        topic_area: str,
        overview: str,
        desired_behavior: str,
        observed_behavior: str,
        severity: int,
        breadth: int,
        harmony_response: str,
        steps_to_reproduce: List[str],
        notes: str = ""
    ) -> Dict[str, Any]:
        """Create a competition-ready finding in findings.json format."""
        
        return {
            "schema_version": "1.0.0",
            "issue_title": issue_title,
            "model": {
                "name": "gpt-oss-20b",
                "version": "2025-08-05",
                "provider": "OpenAI",
                "parameters": {
                    "temperature": 1.0,
                    "max_tokens": 1024,
                    "top_p": 1.0
                }
            },
            "environment": {
                "endpoint": "hosted web-ui"
            },
            "issue_summary": {
                "title": issue_title,
                "topic_area": topic_area,
                "overview": overview,
                "desired_behavior": desired_behavior,
                "observed_behavior": observed_behavior,
                "self_assessed_severity": str(severity),
                "self_assessed_severity_justification": f"Based on {topic_area} impact assessment",
                "self_assessed_breadth": str(breadth),
                "self_assessed_breadth_justification": f"Impact assessment for {topic_area}"
            },
            "harmony_response_walkthroughs": [harmony_response],
            "steps_to_reproduce": steps_to_reproduce,
            "notes": notes,
            "timestamp": datetime.utcnow().isoformat(),
            "finding_id": str(uuid.uuid4())
        }
    
    @staticmethod
    def save_finding(finding: Dict[str, Any], filename: str):
        """Save finding to JSON file for submission."""
        with open(filename, 'w') as f:
            json.dump(finding, f, indent=2)
