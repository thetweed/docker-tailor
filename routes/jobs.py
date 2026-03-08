"""
Job Routes - Job posting management with caching
"""
import ipaddress
import socket
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from urllib.parse import urlparse
from models import Job
from services import get_ai_service, ScraperService

bp = Blueprint('jobs', __name__, url_prefix='/jobs')


def _is_safe_url(url):
    """Return False if the URL resolves to a private/internal IP (SSRF protection).

    Uses getaddrinfo() to check all resolved addresses including IPv6.
    """
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        for addr_info in socket.getaddrinfo(hostname, None):
            ip = ipaddress.ip_address(addr_info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


@bp.route('/')
def list_jobs():
    """List all jobs with optional search/filter"""
    search = request.args.get('search', '')
    filter_by = request.args.get('filter_by', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20

    jobs, total = Job.get_all(search=search, filter_by=filter_by, page=page, per_page=per_page)
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'jobs.html',
        jobs=jobs,
        search=search,
        filter_by=filter_by,
        page=page,
        total_pages=total_pages,
        total=total
    )


@bp.route('/<int:job_id>')
def view_job(job_id):
    """View job details"""
    job = Job.get_by_id(job_id)
    
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('jobs.list_jobs'))
    
    return render_template('job_detail.html', job=job)


@bp.route('/add', methods=['GET', 'POST'])
def add_job():
    """Add a new job posting"""
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('URL is required', 'error')
            return redirect(url_for('jobs.add_job'))

        if urlparse(url).scheme not in ('http', 'https'):
            flash('Only http:// and https:// URLs are supported', 'error')
            return redirect(url_for('jobs.add_job'))

        if not _is_safe_url(url):
            flash('That URL cannot be used — it resolves to a private or reserved address.', 'error')
            return redirect(url_for('jobs.add_job'))

        # Check if job already exists
        if Job.exists(url):
            flash('This job posting has already been added', 'warning')
            return redirect(url_for('jobs.list_jobs'))
        
        try:
            # Scrape the URL
            scraper = ScraperService()
            html_content, text_content = scraper.scrape_job_url(url)
            
            # Check content length
            if len(text_content) < 100:
                flash(
                    'Warning: Retrieved very little content. Analysis might not be accurate.',
                    'warning'
                )
            
            # Extract job details with AI
            ai = get_ai_service()
            job_data = ai.extract_job_details(text_content)
            
            # Save to database
            job_id = Job.create(
                url=url,
                raw_html=html_content,
                raw_text=text_content,
                company_name=job_data['company_name'],
                job_title=job_data['job_title'],
                location=job_data['location'],
                compensation=job_data['compensation'],
                date_posted=job_data['date_posted'],
                requirements=job_data['requirements']
            )
            
            flash(
                f'Job added: {job_data["job_title"]} at {job_data["company_name"]}',
                'success'
            )
            return redirect(url_for('jobs.view_job', job_id=job_id))
            
        except Exception as e:
            error_msg = str(e)
            if 'Timeout' in error_msg or 'timeout' in error_msg.lower():
                flash(
                    'Timeout error: The page took too long to load. '
                    'This sometimes happens with slow job sites. '
                    'Try again or add the job details manually.',
                    'error'
                )
            else:
                current_app.logger.exception("Error adding job from URL")
                flash('An error occurred while adding the job. Please try again or add it manually.', 'error')
            return redirect(url_for('jobs.add_job'))
    
    return render_template('add_job.html')


@bp.route('/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job and its associated tailor analyses"""
    from models.database import get_db_context
    with get_db_context() as (conn, cursor):
        cursor.execute("DELETE FROM tailor_analyses WHERE job_id = ?", (job_id,))
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        deleted = cursor.rowcount > 0
    if deleted:
        flash('Job deleted successfully', 'success')
    else:
        flash('Job not found', 'error')

    return redirect(url_for('jobs.list_jobs'))

@bp.route('/delete-all', methods=['POST'])
def delete_all_jobs():
    """Delete all jobs"""
    from models.database import get_db_context
    
    try:
        with get_db_context() as (conn, cursor):
            cursor.execute("DELETE FROM jobs")
            count = cursor.rowcount
        
        flash(f'Successfully deleted {count} job(s)', 'success')
    except Exception as e:
        current_app.logger.exception("Error deleting all jobs")
        flash('An error occurred while deleting jobs. Please try again.', 'error')

    return redirect(url_for('jobs.list_jobs'))