# Web Server Hardening

Outdated Apache httpd and nginx releases carry known critical flaws, including
CVE-2021-41773 (Apache path traversal / RCE) and CVE-2017-7679 (nginx HTTP/2).
Upgrade web servers to supported versions, disable unused modules, and place
them behind a reverse proxy with TLS.
