from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class GradeResult:
    student_name: str
    folder_and_files: str = "0/0"
    scores: Dict[str, int] = field(default_factory=dict)
    final_score: int = 0
    feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Converts the result object to a flat dictionary for Pandas export."""
        flat_dict = {
            "Folder & Files": self.folder_and_files,
            "Final Score": self.final_score,
            "AI Feedback": self.feedback
        }
        for criterion, score in self.scores.items():
            flat_dict[criterion] = score
            
        return flat_dict