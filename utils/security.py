"""
Security utilities - shared helpers for input validation and SSRF protection
"""
import ipaddress
import socket
from urllib.parse import urlparse


def is_safe_url(url):
    """Return False if the URL resolves to a private/internal address (SSRF protection).

    Checks all resolved addresses via getaddrinfo() to cover IPv6. Used both
    before scraping (routes/jobs.py) and after navigation to catch redirect-based
    SSRF bypass attempts (services/scraper_service.py).
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
