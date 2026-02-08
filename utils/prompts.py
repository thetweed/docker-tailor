"""
AI Prompt Templates
Centralized location for all Claude API prompts
"""


class Prompts:
    """Collection of prompt templates for Claude API"""
    
    @staticmethod
    def job_extraction(text_content):
        """Prompt for extracting job details from scraped content"""
        return f"""You are analyzing a job posting. Extract the following information and return it in EXACTLY this format (keep the labels exactly as shown):

Company: [extract company name]
Title: [extract job title]
Location: [extract location]
Compensation: [extract salary/compensation if mentioned, otherwise write "Not specified"]
Date Posted: [extract posting date if mentioned, otherwise write "Not specified"]
Requirements: [list the key requirements]

Job Posting Text:
{text_content[:10000]}

Return ONLY the formatted information above, nothing else."""
    
    @staticmethod
    def resume_parsing(resume_text):
        """Prompt for parsing resume into structured components"""
        return f"""Analyze this resume and extract all work experiences, bullet points, skills, and education into a structured format.

RESUME TEXT:
{resume_text[:10000]}

Extract the following and return ONLY valid JSON (no markdown, no code blocks):

{{
  "experiences": [
    {{
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "Jan 2020",
      "end_date": "Dec 2022",
      "location": "City, State",
      "description": "Brief description if any"
    }}
  ],
  "bullets": [
    {{
      "text": "Full bullet point text",
      "experience_company": "Company Name (to link it)",
      "category": "technical/leadership/etc",
      "tags": "tag1, tag2, tag3"
    }}
  ],
  "skills": [
    {{
      "name": "Skill name",
      "category": "programming/tools/soft-skills/etc"
    }}
  ],
  "education": [
    {{
      "school": "School Name",
      "degree": "Degree Type",
      "field": "Field of Study",
      "graduation_year": "2020",
      "location": "City, State"
    }}
  ]
}}

Be thorough. Extract all experiences, every bullet point, all skills mentioned. Return ONLY the JSON, nothing else."""
    
    @staticmethod
    def resume_enhancement(parsed_data_json):
        """Prompt for getting AI suggestions on parsed resume"""
        return f"""You are a resume consultant. I've extracted these components from a resume. Provide suggestions and ask clarifying questions to help improve and complete the resume.

EXTRACTED COMPONENTS:
{parsed_data_json}

Provide suggestions in this JSON format (no markdown):

{{
  "experience_suggestions": [
    {{
      "company": "Company Name",
      "current_title": "Current Title",
      "alternate_titles": ["Alternative Title 1", "Alternative Title 2"],
      "questions": ["Was this role remote?", "What specific technologies?"]
    }}
  ],
  "bullet_suggestions": [
    {{
      "original": "Original bullet text",
      "improved": "Suggested improved version (more action-oriented, quantified)",
      "reason": "Why this is better. IMPORTANT: If you add metrics/numbers, mark them as [EXAMPLE: actual number needed] or [estimate - verify actual number]" while still including the suggested metric or number in the bullet.
    }}
  ],
  "skill_suggestions": [
    "Additional skill that seems relevant based on experience"
  ],
  "clarifying_questions": [
    "What certifications do you have?",
    "Any volunteer or side project experience?"
  ]
}}

CRITICAL: When suggesting improved bullets, if you add specific numbers or metrics that weren't in the original, clearly mark the them as an examples that need to be verified. Use placeholders like [X clients], [Y%], [Z team members] or note "verify actual number" in the reasoning.

Focus on:
1. Alternate job titles that would appeal to different roles
2. Improving bullet points with stronger action verbs and quantification
3. Identifying skills that are implied but not explicitly listed
4. Asking questions that would help complete the profile

Return ONLY valid JSON."""
    
    @staticmethod
    def job_matching(job, resume_summary):
        """Prompt for matching resume components to a job"""
        return f"""You are a professional resume consultant. Analyze this job posting and the candidate's resume components, then recommend which components to include and how to position them.

JOB POSTING:
Company: {job['company_name']}
Title: {job['job_title']}
Location: {job['location']}
Requirements:
{job['requirements']}

{resume_summary}

TASK:
Analyze which resume components are most relevant for this job. For each category, provide specific recommendations.

FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS:

EXPERIENCES:
[For each recommended experience, write:]
- Experience ID: [number]
- Recommended Title: [which title variant to use]
- Relevance Score: [1-100]
- Reasoning: [why this experience is relevant]

BULLETS:
[For each recommended bullet, write:]
- Bullet ID: [number]
- Relevance Score: [1-100]
- Reasoning: [why this bullet is relevant]

SKILLS:
[List the most relevant skills from the candidate's skill list]
- [skill name]: [why it's relevant]

OVERALL STRATEGY:
[2-3 sentences on how to position this candidate for this role]

Only recommend components that are genuinely relevant. Be selective - quality over quantity."""
    
    @staticmethod
    def question_analysis(question_text, answer):
        """Prompt for analyzing an answer to a clarifying question"""
        return f"""A user was asked this clarifying question about their resume: "{question_text}"

Their answer: "{answer}"

Based on this answer, suggest specific, concrete resume components to add. Return ONLY valid JSON (no markdown):

{{
  "skills_to_add": [
    {{"name": "Skill name", "category": "Category"}}
  ],
  "bullets_to_add": [
    {{"text": "Bullet point text", "category": "Category"}}
  ],
  "notes": "Brief explanation of what was suggested"
}}

Only suggest items that are clearly supported by their answer. If the answer doesn't suggest any new components, return empty arrays."""
    
    @staticmethod
    def build_resume_summary(experiences, bullets, skills, education):
        """Build a text summary of resume components for job matching"""
        summary = "RESUME COMPONENTS:\n\n"
        
        # Experiences
        summary += "=== EXPERIENCES ===\n"
        for exp in experiences:
            summary += f"\nID: {exp['id']}\n"
            summary += f"Company: {exp['company_name']}\n"
            summary += f"Primary Title: {exp['job_title']}\n"
            if exp['alternate_titles']:
                summary += f"Alternate Titles: {exp['alternate_titles']}\n"
            summary += f"Dates: {exp['start_date']} - {exp['end_date']}\n"
            if exp['description']:
                summary += f"Description: {exp['description']}\n"
        
        # Bullets
        summary += "\n=== BULLET POINTS ===\n"
        for bullet in bullets:
            summary += f"\nID: {bullet['id']}\n"
            summary += f"Bullet: {bullet['bullet_text']}\n"
            if bullet['experience_id']:
                summary += f"Linked to Experience ID: {bullet['experience_id']}\n"
            summary += f"Category: {bullet['category']}\n"
            summary += f"Tags: {bullet['tags']}\n"
        
        # Skills
        summary += "\n=== SKILLS ===\n"
        for skill in skills:
            summary += f"- {skill['skill_name']} ({skill['category']})\n"
        
        # Education
        if education:
            summary += "\n=== EDUCATION ===\n"
            for edu in education:
                summary += f"- {edu['degree']} in {edu['field_of_study']}, {edu['school_name']} ({edu['graduation_year']})\n"
        
        return summary
