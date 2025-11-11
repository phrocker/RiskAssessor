"""LLM-based risk analyzer."""

from typing import Dict, Any, List, Optional
import openai
from openai import OpenAI


class LLMAnalyzer:
    """Uses LLM to analyze deployment risk."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        api_base: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Initialize LLM analyzer.
        
        Args:
            api_key: OpenAI API key or compatible API key
            model: Model name to use
            api_base: Optional custom API base URL
            temperature: Temperature for generation
        """
        self.model = model
        self.temperature = temperature
        
        if api_base:
            self.client = OpenAI(api_key=api_key, base_url=api_base)
        else:
            self.client = OpenAI(api_key=api_key)
    
    def analyze_deployment_risk(
        self,
        changes_summary: Dict[str, Any],
        historical_issues: List[Dict[str, Any]],
        deployment_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze deployment risk using LLM.
        
        Args:
            changes_summary: Summary of code changes
            historical_issues: List of related historical issues
            deployment_context: Optional context about deployment stack/environment
        
        Returns:
            Dictionary containing risk analysis
        """
        prompt = self._build_prompt(changes_summary, historical_issues, deployment_context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert DevOps engineer and site reliability engineer specializing in deployment risk assessment. Analyze the provided information and assess the risk of deployment failures."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the response to extract risk score and insights
            risk_data = self._parse_llm_response(analysis_text)
            
            return {
                'llm_analysis': analysis_text,
                'risk_score': risk_data['risk_score'],
                'key_concerns': risk_data['key_concerns'],
                'recommendations': risk_data['recommendations'],
                'confidence': risk_data['confidence']
            }
        
        except Exception as e:
            # Fallback if LLM fails
            return {
                'llm_analysis': f"LLM analysis failed: {str(e)}",
                'risk_score': 0.5,  # Medium risk by default
                'key_concerns': ["Unable to perform LLM analysis"],
                'recommendations': ["Review changes manually"],
                'confidence': 0.0
            }
    
    def _build_prompt(
        self,
        changes_summary: Dict[str, Any],
        historical_issues: List[Dict[str, Any]],
        deployment_context: Optional[str]
    ) -> str:
        """Build the prompt for the LLM."""
        prompt_parts = [
            "# Deployment Risk Assessment Request\n",
            "Please analyze the following code changes and historical issues to assess deployment risk.\n",
            "\n## Code Changes Summary\n"
        ]
        
        # Add changes summary
        prompt_parts.append(f"- Files changed: {changes_summary.get('files_changed', 0)}\n")
        prompt_parts.append(f"- Lines added: {changes_summary.get('additions', 0)}\n")
        prompt_parts.append(f"- Lines deleted: {changes_summary.get('deletions', 0)}\n")
        prompt_parts.append(f"- Number of commits: {changes_summary.get('commits', 0)}\n")
        
        if 'critical_files' in changes_summary and changes_summary['critical_files']:
            prompt_parts.append(f"\nCritical files modified:\n")
            for file in changes_summary['critical_files'][:10]:  # Limit to 10
                prompt_parts.append(f"  - {file}\n")
        
        if 'file_types' in changes_summary:
            prompt_parts.append(f"\nFile types distribution:\n")
            for ext, count in changes_summary['file_types'].items():
                prompt_parts.append(f"  - {ext}: {count} files\n")
        
        # Add historical issues
        if historical_issues:
            prompt_parts.append("\n## Related Historical Issues\n")
            for i, issue in enumerate(historical_issues[:5], 1):  # Limit to 5 most relevant
                prompt_parts.append(f"\n### Issue {i}\n")
                prompt_parts.append(f"- Source: {issue.get('source', 'unknown')}\n")
                prompt_parts.append(f"- Title: {issue.get('title', 'N/A')}\n")
                prompt_parts.append(f"- Status: {issue.get('status', 'N/A')}\n")
                if issue.get('severity'):
                    prompt_parts.append(f"- Severity: {issue['severity']}\n")
        
        # Add deployment context
        if deployment_context:
            prompt_parts.append(f"\n## Deployment Context\n{deployment_context}\n")
        
        # Add instructions
        prompt_parts.append("\n## Assessment Instructions\n")
        prompt_parts.append("Provide a risk assessment with the following structure:\n\n")
        prompt_parts.append("1. **Risk Score**: Provide a numerical score from 0.0 (no risk) to 1.0 (critical risk)\n")
        prompt_parts.append("2. **Key Concerns**: List 3-5 main concerns that could lead to deployment failures\n")
        prompt_parts.append("3. **Recommendations**: Provide 3-5 specific recommendations to mitigate risks\n")
        prompt_parts.append("4. **Confidence**: Rate your confidence in this assessment (low/medium/high)\n")
        prompt_parts.append("\nFormat your response clearly with these sections.\n")
        
        return ''.join(prompt_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract structured data.
        
        This is a simple parser that looks for patterns in the response.
        """
        import re
        
        # Try to extract risk score
        risk_score = 0.5  # Default
        score_match = re.search(r'(?:risk score|score)[:\s]+([0-9.]+)', response, re.IGNORECASE)
        if score_match:
            try:
                risk_score = float(score_match.group(1))
                risk_score = max(0.0, min(1.0, risk_score))  # Clamp to 0-1
            except ValueError:
                pass
        
        # Extract key concerns
        key_concerns = []
        concerns_section = re.search(
            r'(?:key concerns|concerns)[:\s]*\n(.*?)(?=\n\n|\n#|\nrecommendations|\nconfidence|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        if concerns_section:
            concern_lines = concerns_section.group(1).strip().split('\n')
            for line in concern_lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 
                           line[0].isdigit() and line[1] == '.'):
                    # Remove bullet points and numbering
                    concern = re.sub(r'^[-•\d.)\s]+', '', line).strip()
                    if concern:
                        key_concerns.append(concern)
        
        # Extract recommendations
        recommendations = []
        rec_section = re.search(
            r'(?:recommendations|mitigation)[:\s]*\n(.*?)(?=\n\n|\n#|\nconfidence|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        if rec_section:
            rec_lines = rec_section.group(1).strip().split('\n')
            for line in rec_lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 
                           line[0].isdigit() and line[1] == '.'):
                    rec = re.sub(r'^[-•\d.)\s]+', '', line).strip()
                    if rec:
                        recommendations.append(rec)
        
        # Extract confidence
        confidence_map = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        confidence = 0.6  # Default medium
        conf_match = re.search(r'confidence[:\s]+(low|medium|high)', response, re.IGNORECASE)
        if conf_match:
            confidence = confidence_map.get(conf_match.group(1).lower(), 0.6)
        
        return {
            'risk_score': risk_score,
            'key_concerns': key_concerns if key_concerns else ["No specific concerns identified"],
            'recommendations': recommendations if recommendations else ["Review changes carefully"],
            'confidence': confidence
        }
