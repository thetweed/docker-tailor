"""
Web Scraper Service - Job posting scraping with fallback
"""
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from flask import current_app


class ScraperService:
    """Service for scraping job postings from URLs"""
    
    @staticmethod
    def scrape_job_url(url):
        """
        Scrape a job posting URL, trying Playwright first, then requests
        
        Args:
            url: Job posting URL to scrape
            
        Returns:
            Tuple of (html_content, text_content)
        """
        # Try Playwright first (better for JS-heavy sites)
        try:
            return ScraperService._scrape_with_playwright(url)
        except Exception as e:
            current_app.logger.warning(f"Playwright failed, trying simple scraping: {e}")
            # Fallback to simple requests
            try:
                return ScraperService._scrape_with_requests(url)
            except Exception as e2:
                current_app.logger.error(f"Both scraping methods failed: {e2}")
                raise Exception(
                    "Could not scrape this job posting. The site may be blocking automated access. "
                    "Please use 'Add Manually' to enter the job details."
                )
    
    @staticmethod
    def _scrape_with_playwright(url):
        """Scrape using Playwright (for JS-heavy sites)"""
        timeout = current_app.config.get('SCRAPE_TIMEOUT', 60000)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            page.wait_for_timeout(2000)
            
            html_content = page.content()
            text_content = page.evaluate("() => document.body.innerText")
            
            return html_content, text_content
    
    @staticmethod
    def _scrape_with_requests(url):
        """Scrape using requests (simpler, for static sites)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text(separator='\n', strip=True)
        html_content = str(soup)
        
        return html_content, text_content