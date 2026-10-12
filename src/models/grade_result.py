from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class GradeResult:
    student_name: str
    matched_folder: str
    file_count: int
    scores: Dict[str, int] = field(default_factory=dict)
    final_score: int = 0
    feedback: str = ""
    status: str = "Success"  # Success, Missing, Empty Folder, or Error

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result object to a flat dictionary for Pandas export."""
        flat_dict = {
            "Matched Folder": self.matched_folder,
            "File Count": self.file_count,
            "Final Score": self.final_score,
            "AI Feedback": self.feedback
        }
        # Unpack individual criterion scores into separate dictionary keys
        for criterion, score in self.scores.items():
            flat_dict[criterion] = score
            
        return flat_dict