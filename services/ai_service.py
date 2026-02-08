"""
AI Service - All Claude API interactions
"""
import json
from anthropic import Anthropic
from flask import current_app
from utils.prompts import Prompts


class AIService:
    """Service for interacting with Claude API"""
    
    def __init__(self):
        api_key = current_app.config.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        self.client = Anthropic(api_key=api_key)
    
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
            return message.content[0].text
        except Exception as e:
            current_app.logger.error(f"Claude API error: {e}")
            raise
    
    def _parse_json_response(self, response_text):
        """Parse JSON from Claude's response, handling markdown code blocks"""
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('```')[1]
            if cleaned.startswith('json'):
                cleaned = cleaned[4:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
        
        return json.loads(cleaned.strip())
    
    def extract_job_details(self, text_content):
        """Extract job details from scraped text"""
        prompt = Prompts.job_extraction(text_content)
        response = self._call_claude(
            prompt, 
            model=current_app.config['HAIKU_MODEL'],
            max_tokens=1024
        )
        
        # Parse the structured response
        job_data = {
            'company_name': 'Not specified',
            'job_title': 'Not specified',
            'location': 'Not specified',
            'compensation': 'Not specified',
            'date_posted': 'Not specified',
            'requirements': 'Not specified'
        }
        
        for line in response.split('\n'):
            if line.startswith('Company:'):
                job_data['company_name'] = line.replace('Company:', '').strip()
            elif line.startswith('Title:'):
                job_data['job_title'] = line.replace('Title:', '').strip()
            elif line.startswith('Location:'):
                job_data['location'] = line.replace('Location:', '').strip()
            elif line.startswith('Compensation:'):
                job_data['compensation'] = line.replace('Compensation:', '').strip()
            elif line.startswith('Date Posted:'):
                job_data['date_posted'] = line.replace('Date Posted:', '').strip()
            elif line.startswith('Requirements:'):
                idx = response.find('Requirements:')
                job_data['requirements'] = response[idx+13:].strip()
        
        return job_data
    
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
        """Analyze which resume components match a job posting"""
        resume_summary = Prompts.build_resume_summary(
            experiences, bullets, skills, education
        )
        prompt = Prompts.job_matching(job, resume_summary)
        result = self._call_claude(prompt)
        return result
    
    def analyze_question_answer(self, question_text, answer):
        """Analyze answer to clarifying question and suggest components"""
        prompt = Prompts.question_analysis(question_text, answer)
        response = self._call_claude(prompt, max_tokens=2000)
        result = self._parse_json_response(response)
        return result


# Singleton instance
_ai_service = None

def get_ai_service():
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service