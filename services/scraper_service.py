"""
Web Scraper Service - Job posting scraping with fallback
"""
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout, Error as PlaywrightError
from urllib.parse import urljoin
from flask import current_app
from utils.security import is_safe_url

_MAX_REDIRECTS = 10
_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5MB — job postings should never be this large
_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


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
        except (PlaywrightError, OSError, ValueError) as e:
            current_app.logger.warning(f"Playwright failed, trying simple scraping: {e}")
            # Fallback to simple requests
            try:
                return ScraperService._scrape_with_requests(url)
            except (requests.RequestException, OSError, ValueError) as e2:
                current_app.logger.error(f"Both scraping methods failed: {e2}")
                raise RuntimeError(
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
            context = None
            page = None
            try:
                context = browser.new_context(
                    user_agent=_USER_AGENT
                )
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                # Validate final URL after redirects (SSRF: redirect bypass protection)
                if not is_safe_url(page.url):
                    raise ValueError(
                        f"Scraping aborted: redirected to a private address ({page.url})"
                    )
                # Wait for network to settle — catches SPA/JS-rendered pages (e.g. Workday).
                # If networkidle times out, fall back to a fixed wait to give JS time to render.
                try:
                    page.wait_for_load_state('networkidle', timeout=15000)
                except PlaywrightTimeout:
                    page.wait_for_timeout(2000)
                html_content = page.content()
                if len(html_content.encode('utf-8')) > _MAX_RESPONSE_BYTES:
                    raise ValueError(
                        f"Page content exceeds size limit ({_MAX_RESPONSE_BYTES // (1024*1024)}MB)"
                    )
                text_content = page.evaluate("() => document.body.innerText")
                return html_content, text_content
            finally:
                if page is not None:
                    page.close()
                if context is not None:
                    context.close()
                browser.close()
    
    @staticmethod
    def _scrape_with_requests(url):
        """Scrape using requests (simpler, for static sites)"""
        headers = {
            'User-Agent': _USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        # Follow redirects manually so each hop is validated (SSRF protection)
        current_url = url
        for _ in range(_MAX_REDIRECTS):
            response = requests.get(current_url, headers=headers, timeout=30,
                                    allow_redirects=False, stream=True)
            if response.is_redirect:
                location = response.headers.get('Location', '')
                if not location.startswith('http'):
                    location = urljoin(current_url, location)
                if not is_safe_url(location):
                    raise ValueError(
                        f"Scraping aborted: redirect to a private address ({location})"
                    )
                current_url = location
            else:
                response.raise_for_status()
                # Read with size cap before buffering the full response
                chunks = []
                total = 0
                for chunk in response.iter_content(chunk_size=65536):
                    total += len(chunk)
                    if total > _MAX_RESPONSE_BYTES:
                        raise ValueError(
                            f"Page content exceeds size limit "
                            f"({_MAX_RESPONSE_BYTES // (1024 * 1024)}MB)"
                        )
                    chunks.append(chunk)
                raw_html = b''.join(chunks).decode(response.encoding or 'utf-8', errors='replace')
                break
        else:
            raise ValueError("Too many redirects")

        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text(separator='\n', strip=True)
        html_content = str(soup)
        
        return html_content, text_content