import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_safe_url(url: str) -> Tuple[bool, str]:
    """
    Validates if an outbound URL is safe against SSRF attacks.
    Blocks private IPs, loopback, cloud metadata IPs, and non-HTTP protocols.
    """
    if not url:
        return False, "URL cannot be empty"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL structure: {e}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme: {parsed.scheme}. Only http/https are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL missing hostname"

    # Check for localhost literal
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        return False, f"Access to localhost/internal host '{hostname}' is blocked."

    try:
        # Resolve hostname to IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_reserved:
                return False, f"Host resolves to unsafe/private IP: {ip_str}"

            for blocked_range in BLOCKED_IP_RANGES:
                if ip_obj in blocked_range:
                    return False, f"Host resolves to blocked IP range: {ip_str}"

        return True, "Safe"
    except socket.gaierror:
        # Host could not be resolved
        return False, f"Could not resolve hostname: {hostname}"
    except Exception as e:
        return False, f"SSRF check error: {e}"
