"""
Advanced Nginx Configuration Generator
=====================================

This module generates optimized Nginx configurations for production deployment
with load balancing, caching, security, and performance optimizations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class UpstreamServer:
    """Upstream server configuration."""
    host: str
    port: int
    weight: int = 1
    max_fails: int = 3
    fail_timeout: str = "30s"
    backup: bool = False

@dataclass
class NginxConfig:
    """Complete Nginx configuration."""
    server_name: str
    listen_port: int
    ssl_enabled: bool
    upstream_servers: List[UpstreamServer]
    static_files_path: Optional[str]
    max_body_size: str
    worker_processes: int
    worker_connections: int
    keepalive_timeout: int
    gzip_enabled: bool
    rate_limiting: Dict[str, Any]
    security_headers: Dict[str, str]
    caching: Dict[str, Any]

class NginxConfigGenerator:
    """Generates optimized Nginx configurations for production."""
    
    def __init__(self):
        self.config: Optional[NginxConfig] = None
    
    def generate_config(self,
                       server_name: str = "_",
                       workers: int = 1,
                       app_port: int = 8000,
                       ssl_enabled: bool = False) -> NginxConfig:
        """
        Generate optimized Nginx configuration.
        
        Args:
            server_name: Server name or domain
            workers: Number of application workers
            app_port: Application port
            ssl_enabled: Whether SSL is enabled
            
        Returns:
            NginxConfig: Complete Nginx configuration
        """
        # Calculate optimal Nginx worker settings
        cpu_cores = os.cpu_count() or 1
        worker_processes = min(cpu_cores, 4)  # Cap at 4 for most use cases
        worker_connections = 1024  # Standard value
        
        # Create upstream servers (one per application worker)
        upstream_servers = []
        for i in range(workers):
            # For single server deployment, all workers use same port
            # In multi-server setup, this would be different IPs/ports
            upstream_servers.append(UpstreamServer(
                host="127.0.0.1",
                port=app_port,
                weight=1,
                max_fails=3,
                fail_timeout="30s"
            ))
        
        # Security headers
        security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if ssl_enabled else None
        }
        
        # Remove None values
        security_headers = {k: v for k, v in security_headers.items() if v is not None}
        
        # Rate limiting configuration
        rate_limiting = {
            "zone_name": "api",
            "zone_size": "10m",
            "rate": "10r/s",
            "burst": 20,
            "nodelay": True,
            "status_code": 429
        }
        
        # Caching configuration
        caching = {
            "static_cache_time": "1y",
            "api_cache_time": "5m",
            "proxy_cache_path": "/var/cache/nginx/lawvriksh",
            "proxy_cache_levels": "1:2",
            "proxy_cache_keys_zone": "lawvriksh_cache:10m",
            "proxy_cache_max_size": "1g",
            "proxy_cache_inactive": "60m"
        }
        
        self.config = NginxConfig(
            server_name=server_name,
            listen_port=443 if ssl_enabled else 80,
            ssl_enabled=ssl_enabled,
            upstream_servers=upstream_servers,
            static_files_path="/opt/lawvriksh/app/static",
            max_body_size="16M",
            worker_processes=worker_processes,
            worker_connections=worker_connections,
            keepalive_timeout=65,
            gzip_enabled=True,
            rate_limiting=rate_limiting,
            security_headers=security_headers,
            caching=caching
        )
        
        return self.config
    
    def generate_nginx_conf(self, config: NginxConfig) -> str:
        """Generate main nginx.conf file."""
        return f"""# Nginx Configuration for LawVriksh Production
# Generated automatically - Optimized for performance and security

user www-data;
worker_processes {config.worker_processes};
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

# Worker settings
events {{
    worker_connections {config.worker_connections};
    use epoll;
    multi_accept on;
}}

http {{
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout {config.keepalive_timeout};
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size {config.max_body_size};
    
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                   '$status $body_bytes_sent "$http_referer" '
                   '"$http_user_agent" "$http_x_forwarded_for" '
                   'rt=$request_time uct="$upstream_connect_time" '
                   'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip {str(config.gzip_enabled).lower()};
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone={config.rate_limiting['zone_name']}:{config.rate_limiting['zone_size']} rate={config.rate_limiting['rate']};
    limit_req_status {config.rate_limiting['status_code']};
    
    # Proxy cache
    proxy_cache_path {config.caching['proxy_cache_path']} levels={config.caching['proxy_cache_levels']} keys_zone={config.caching['proxy_cache_keys_zone']} max_size={config.caching['proxy_cache_max_size']} inactive={config.caching['proxy_cache_inactive']};
    proxy_temp_path /var/cache/nginx/temp;
    
    # Include server configurations
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}}
"""
    
    def generate_site_config(self, config: NginxConfig) -> str:
        """Generate site-specific configuration."""
        # Generate upstream block
        upstream_block = "upstream lawvriksh_backend {\n"
        upstream_block += "    least_conn;\n"  # Load balancing method
        upstream_block += "    keepalive 32;\n"
        
        for server in config.upstream_servers:
            server_line = f"    server {server.host}:{server.port}"
            if server.weight != 1:
                server_line += f" weight={server.weight}"
            if server.max_fails != 3:
                server_line += f" max_fails={server.max_fails}"
            if server.fail_timeout != "30s":
                server_line += f" fail_timeout={server.fail_timeout}"
            if server.backup:
                server_line += " backup"
            server_line += ";\n"
            upstream_block += server_line
        
        upstream_block += "}\n\n"
        
        # Generate security headers
        security_headers_block = ""
        for header, value in config.security_headers.items():
            security_headers_block += f"    add_header {header} \"{value}\" always;\n"
        
        # SSL configuration
        ssl_config = ""
        if config.ssl_enabled:
            ssl_config = f"""
    # SSL Configuration
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    
    ssl_certificate /etc/ssl/certs/lawvriksh.crt;
    ssl_certificate_key /etc/ssl/private/lawvriksh.key;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
"""
        else:
            ssl_config = f"""
    listen {config.listen_port};
    listen [::]:{config.listen_port};
"""
        
        # HTTP to HTTPS redirect
        http_redirect = ""
        if config.ssl_enabled:
            http_redirect = """
# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://$host$request_uri;
}

"""
        
        site_config = f"""{http_redirect}{upstream_block}# Main server block
server {{
    server_name {config.server_name};
{ssl_config}
    
    # Security headers
{security_headers_block}
    
    # Rate limiting
    limit_req zone={config.rate_limiting['zone_name']} burst={config.rate_limiting['burst']}{"" if not config.rate_limiting['nodelay'] else " nodelay"};
    
    # Main application proxy
    location / {{
        proxy_pass http://lawvriksh_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Caching for API responses
        proxy_cache lawvriksh_cache;
        proxy_cache_valid 200 302 {config.caching['api_cache_time']};
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_lock on;
        
        # Add cache status header
        add_header X-Cache-Status $upstream_cache_status;
    }}
    
    # Health check endpoint (no rate limiting)
    location /health {{
        proxy_pass http://lawvriksh_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
        
        # No caching for health checks
        proxy_cache off;
    }}
    
    # API documentation (cached)
    location ~ ^/(docs|redoc|openapi.json) {{
        proxy_pass http://lawvriksh_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Cache API docs
        proxy_cache lawvriksh_cache;
        proxy_cache_valid 200 1h;
        add_header X-Cache-Status $upstream_cache_status;
    }}
    
    # Static files (if they exist)
    location /static/ {{
        alias {config.static_files_path}/;
        expires {config.caching['static_cache_time']};
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        
        # Gzip static files
        gzip_static on;
        
        # Security for static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
            expires {config.caching['static_cache_time']};
            add_header Cache-Control "public, immutable";
        }}
    }}
    
    # Deny access to sensitive files
    location ~ /\. {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    location ~ ~$ {{
        deny all;
        access_log off;
        log_not_found off;
    }}
    
    # Custom error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    location = /404.html {{
        root /var/www/html;
        internal;
    }}
    
    location = /50x.html {{
        root /var/www/html;
        internal;
    }}
}}
"""
        
        return site_config
    
    def save_configs(self, config: NginxConfig, output_dir: str = "production/nginx"):
        """Save Nginx configuration files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate and save main nginx.conf
        nginx_conf = self.generate_nginx_conf(config)
        with open(output_path / "nginx.conf", 'w') as f:
            f.write(nginx_conf)
        
        # Generate and save site configuration
        site_config = self.generate_site_config(config)
        with open(output_path / "lawvriksh.conf", 'w') as f:
            f.write(site_config)
        
        # Create SSL certificate placeholder
        if config.ssl_enabled:
            ssl_info = """# SSL Certificate Setup Instructions
# =====================================

# 1. Obtain SSL certificate (Let's Encrypt recommended):
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 2. Or use self-signed certificate for testing:
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\
    -keyout /etc/ssl/private/lawvriksh.key \\
    -out /etc/ssl/certs/lawvriksh.crt

# 3. Set proper permissions:
sudo chmod 600 /etc/ssl/private/lawvriksh.key
sudo chmod 644 /etc/ssl/certs/lawvriksh.crt
"""
            with open(output_path / "ssl_setup.txt", 'w') as f:
                f.write(ssl_info)
        
        logger.info(f"Nginx configuration files saved to {output_path}")
        
        return {
            "nginx_conf": str(output_path / "nginx.conf"),
            "site_conf": str(output_path / "lawvriksh.conf"),
            "ssl_setup": str(output_path / "ssl_setup.txt") if config.ssl_enabled else None
        }

# Global configuration generator
nginx_generator = NginxConfigGenerator()
