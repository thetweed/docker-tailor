"""
AI Service - All Claude API interactions
"""
import json
import re
import anthropic
from anthropic import Anthropic
from flask import current_app, g
from utils.prompts import Prompts


class AIService:
    """Service for interacting with Claude API"""
    
    def __init__(self):
        api_key = current_app.config.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = Anthropic(api_key=api_key, timeout=current_app.config.get('AI_TIMEOUT', 120))
    
    def _call_claude(self, prompt, model=None, max_tokens=4096):
        """Internal method to call Claude API"""
        if model is None:
            model = current_app.config['SONNET_MODEL']
        
        try:
            message = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            if not message.content:
                raise ValueError("Claude API returned an empty response")
            return message.content[0].text
        except anthropic.APITimeoutError:
            current_app.logger.error("Claude API request timed out")
            raise
        except anthropic.RateLimitError:
            current_app.logger.error("Claude API rate limit exceeded")
            raise
        except anthropic.AuthenticationError:
            current_app.logger.error("Claude API authentication failed — check ANTHROPIC_API_KEY")
            raise
        except anthropic.APIConnectionError as e:
            current_app.logger.error("Claude API connection error: %s", e)
            raise
        except anthropic.APIStatusError as e:
            current_app.logger.error("Claude API error %s: %s", e.status_code, e.message)
            raise
    
    def _parse_json_response(self, response_text):
        """Parse JSON from Claude's response, handling markdown code blocks"""
        cleaned = response_text.strip()

        # Try to extract from a fenced code block first
        fence_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)```', cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        # Fall back to finding the outermost JSON object or array
        if not cleaned.startswith(('{', '[')):
            obj_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
            if obj_match:
                cleaned = obj_match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            current_app.logger.error(
                f"Failed to parse AI response as JSON: {e}\n"
                f"Response snippet: {response_text[:200]}"
            )
            raise ValueError("The AI returned a response that couldn't be parsed. Please try again.") from e
    
    def extract_job_details(self, text_content):
        """Extract job details from scraped text.

        Intentionally returns defaults on parse failure (graceful degradation) — the job
        can still be saved with "Not specified" fields rather than failing the whole import.
        This is different from other AI methods that raise on failure.
        """
        defaults = {
            'company_name': 'Not specified',
            'job_title': 'Not specified',
            'location': 'Not specified',
            'compensation': 'Not specified',
            'date_posted': 'Not specified',
            'requirements': 'Not specified'
        }

        prompt = Prompts.job_extraction(text_content)
        response = self._call_claude(
            prompt,
            model=current_app.config['HAIKU_MODEL'],
            max_tokens=1024
        )

        try:
            job_data = self._parse_json_response(response)
            for key, default in defaults.items():
                if not job_data.get(key):
                    job_data[key] = default
            return job_data
        except ValueError:
            current_app.logger.warning("Job extraction fell back to defaults due to unparseable AI response")
            return defaults
    
    def parse_resume(self, resume_text):
        """Parse resume text into structured components"""
        prompt = Prompts.resume_parsing(resume_text)
        response = self._call_claude(prompt, max_tokens=8000)
        result = self._parse_json_response(response)
        return result
    
    def get_resume_suggestions(self, parsed_data):
        """Get AI suggestions for improving resume components"""
        data_json = json.dumps(parsed_data, indent=2)
        prompt = Prompts.resume_enhancement(data_json)
        response = self._call_claude(prompt, max_tokens=4000)
        result = self._parse_json_response(response)
        return result
    
    def match_job_to_resume(self, job, experiences, bullets, skills, education):
        """Analyze which resume components match a job posting.

        Returns a parsed dict with structured analysis data.
        """
        resume_summary = Prompts.build_resume_summary(
            experiences, bullets, skills, education
        )
        prompt = Prompts.job_matching(job, resume_summary)
        response = self._call_claude(prompt)
        current_app.logger.debug("Raw tailor analysis response: %s", response)
        result = self._parse_json_response(response)
        return result
    
    def analyze_question_answer(self, question_text, answer):
        """Analyze answer to clarifying question and suggest components"""
        prompt = Prompts.question_analysis(question_text, answer)
        response = self._call_claude(prompt, max_tokens=2000)
        result = self._parse_json_response(response)
        return result

    def cleanup_skill_categories(self, skills):
        """Analyze skills and suggest category consolidation"""
        # Build skills data string
        skills_by_category = {}
        for skill in skills:
            cat = skill['category'] or 'Uncategorized'
            if cat not in skills_by_category:
                skills_by_category[cat] = []
            skills_by_category[cat].append(skill['skill_name'])

        skills_data = ""
        for category, skill_list in skills_by_category.items():
            skills_data += f"\n{category}:\n"
            for skill_name in skill_list:
                skills_data += f"  - {skill_name}\n"

        prompt = Prompts.skill_category_cleanup(skills_data)
        response = self._call_claude(prompt, max_tokens=2000)
        result = self._parse_json_response(response)
        return result


def get_ai_service():
    """Get or create an AIService instance scoped to the current request."""
    if 'ai_service' not in g:
        g.ai_service = AIService()
    return g.ai_service