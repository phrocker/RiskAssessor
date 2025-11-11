"""Complexity analyzer for code changes."""

from typing import List, Dict, Any
from pathlib import Path
import re


class ComplexityAnalyzer:
    """Analyzes the complexity of code changes."""
    
    # File type weights - riskier file types get higher weights
    FILE_TYPE_WEIGHTS = {
        '.py': 1.0,
        '.js': 1.0,
        '.ts': 1.0,
        '.java': 1.0,
        '.go': 1.0,
        '.rb': 1.0,
        '.php': 1.0,
        '.c': 1.2,
        '.cpp': 1.2,
        '.h': 1.2,
        '.sql': 1.5,
        '.yaml': 1.3,
        '.yml': 1.3,
        '.json': 1.1,
        '.xml': 1.1,
        '.sh': 1.4,
        '.bash': 1.4,
        '.dockerfile': 1.5,
        'dockerfile': 1.5,
        '.md': 0.5,
        '.txt': 0.3,
        '.rst': 0.5,
    }
    
    # Critical file patterns
    CRITICAL_PATTERNS = [
        r'.*config.*',
        r'.*settings.*',
        r'.*env.*',
        r'.*deploy.*',
        r'.*migration.*',
        r'.*schema.*',
        r'.*security.*',
        r'.*auth.*',
        r'.*database.*',
        r'.*db.*',
        r'.*api.*',
    ]
    
    def __init__(self):
        """Initialize complexity analyzer."""
        self.critical_regex = [re.compile(pattern, re.IGNORECASE) 
                              for pattern in self.CRITICAL_PATTERNS]
    
    def analyze_changes(
        self,
        files_changed: List[str],
        additions: int,
        deletions: int,
        commits: int
    ) -> Dict[str, Any]:
        """
        Analyze the complexity of changes.
        
        Args:
            files_changed: List of changed file paths
            additions: Total lines added
            deletions: Total lines deleted
            commits: Number of commits
        
        Returns:
            Dictionary containing complexity metrics
        """
        total_changes = additions + deletions
        
        # Calculate file type distribution
        file_types = self._analyze_file_types(files_changed)
        
        # Check for critical files
        critical_files = self._identify_critical_files(files_changed)
        
        # Calculate weighted complexity score
        complexity_score = self._calculate_complexity_score(
            files_changed=len(files_changed),
            total_changes=total_changes,
            commits=commits,
            file_types=file_types,
            critical_files=len(critical_files)
        )
        
        return {
            'files_changed': len(files_changed),
            'additions': additions,
            'deletions': deletions,
            'total_changes': total_changes,
            'commits': commits,
            'file_types': file_types,
            'critical_files': critical_files,
            'complexity_score': complexity_score,
            'risk_level': self._get_risk_level(complexity_score)
        }
    
    def _analyze_file_types(self, files: List[str]) -> Dict[str, int]:
        """Analyze distribution of file types."""
        file_types = {}
        
        for file in files:
            ext = Path(file).suffix.lower()
            if not ext:
                # Check for special files without extension
                name = Path(file).name.lower()
                if 'dockerfile' in name:
                    ext = 'dockerfile'
                else:
                    ext = 'no_extension'
            
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return file_types
    
    def _identify_critical_files(self, files: List[str]) -> List[str]:
        """Identify critical files that are higher risk."""
        critical = []
        
        for file in files:
            file_lower = file.lower()
            for pattern in self.critical_regex:
                if pattern.search(file_lower):
                    critical.append(file)
                    break
        
        return critical
    
    def _calculate_complexity_score(
        self,
        files_changed: int,
        total_changes: int,
        commits: int,
        file_types: Dict[str, int],
        critical_files: int
    ) -> float:
        """
        Calculate overall complexity score (0-1).
        
        Higher scores indicate higher complexity and risk.
        """
        # Base score from change volume
        volume_score = min(1.0, (files_changed / 50.0) + (total_changes / 1000.0))
        
        # Score from file types
        type_score = 0.0
        total_files = sum(file_types.values())
        for ext, count in file_types.items():
            weight = self.FILE_TYPE_WEIGHTS.get(ext, 1.0)
            type_score += (count / total_files) * weight
        type_score = min(1.0, type_score / 1.5)  # Normalize
        
        # Score from critical files
        critical_score = min(1.0, critical_files / 10.0)
        
        # Score from commit fragmentation
        # Many small commits or few large commits both indicate complexity
        if commits > 0:
            changes_per_commit = total_changes / commits
            if changes_per_commit < 10:
                commit_score = 0.3  # Many small commits
            elif changes_per_commit > 200:
                commit_score = 0.8  # Few large commits
            else:
                commit_score = 0.5  # Normal
        else:
            commit_score = 0.0
        
        # Weighted combination
        complexity = (
            volume_score * 0.3 +
            type_score * 0.2 +
            critical_score * 0.3 +
            commit_score * 0.2
        )
        
        return min(1.0, complexity)
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level."""
        if score < 0.3:
            return "low"
        elif score < 0.6:
            return "medium"
        elif score < 0.8:
            return "high"
        else:
            return "critical"
