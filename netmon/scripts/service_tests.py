#!/usr/bin/env python3
import subprocess
import requests
import socket
import ssl
import dns.resolver
import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Tuple

class ServiceTester:
    def __init__(self):
        self.results = []
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['172.20.0.10']  # Bind9 server IP

    def log_result(self, service: str, test_name: str, status: bool, message: str) -> None:
        self.results.append({
            'timestamp': datetime.utcnow().isoformat(),
            'service': service,
            'test_name': test_name,
            'status': 'PASS' if status else 'FAIL',
            'message': message
        })

    def test_traefik(self) -> None:
        # Test HTTP to HTTPS redirect
        try:
            response = requests.get('http://www.terrerov.com', allow_redirects=False)
            status = response.status_code == 301 and 'https://' in response.headers.get('Location', '')
            self.log_result('traefik', 'http_redirect', status, 
                           'HTTP to HTTPS redirect working' if status else 'Redirect not configured correctly')
        except Exception as e:
            self.log_result('traefik', 'http_redirect', False, f'Error: {str(e)}')

        # Test HTTPS access
        try:
            response = requests.get('https://www.terrerov.com', verify=True)
            status = response.status_code == 200
            self.log_result('traefik', 'https_access', status,
                           'HTTPS access working' if status else 'HTTPS access failed')
        except Exception as e:
            self.log_result('traefik', 'https_access', False, f'Error: {str(e)}')

        # Test Traefik Dashboard auth
        try:
            response = requests.get('https://traefik.terrerov.com', auth=('admin', 'your_password'))
            status = response.status_code == 200
            self.log_result('traefik', 'dashboard_auth', status,
                           'Dashboard authentication working' if status else 'Dashboard auth failed')
        except Exception as e:
            self.log_result('traefik', 'dashboard_auth', False, f'Error: {str(e)}')

        # Test SSL certificate
        try:
            context = ssl.create_default_context()
            with socket.create_connection(('www.terrerov.com', 443)) as sock:
                with context.wrap_socket(sock, server_hostname='www.terrerov.com') as ssock:
                    cert = ssock.getpeercert()
                    status = cert and datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z') > datetime.now()
                    self.log_result('traefik', 'ssl_cert', status,
                                   'SSL certificate valid' if status else 'SSL certificate invalid or expired')
        except Exception as e:
            self.log_result('traefik', 'ssl_cert', False, f'Error: {str(e)}')

    def test_bind9(self) -> None:
        # Test internal DNS resolution
        try:
            answers = self.resolver.resolve('traefik.terrerov.com', 'A')
            status = len(answers) > 0 and str(answers[0]).startswith('172.20.')
            self.log_result('bind9', 'internal_resolution', status,
                           'Internal DNS resolution working' if status else 'Internal DNS resolution failed')
        except Exception as e:
            self.log_result('bind9', 'internal_resolution', False, f'Error: {str(e)}')

        # Test reverse DNS
        try:
            ip = '172.20.0.10'
            result = subprocess.run(['dig', '-x', ip, '@172.20.0.10'], capture_output=True, text=True)
            status = 'terrerov.com' in result.stdout
            self.log_result('bind9', 'reverse_dns', status,
                           'Reverse DNS working' if status else 'Reverse DNS failed')
        except Exception as e:
            self.log_result('bind9', 'reverse_dns', False, f'Error: {str(e)}')

    def test_nginx(self) -> None:
        # Test internal Nginx access
        try:
            response = requests.get('http://nginx.terrerov.com:8080')
            status = response.status_code == 200
            self.log_result('nginx', 'internal_access', status,
                           'Internal Nginx access working' if status else 'Internal Nginx access failed')
        except Exception as e:
            self.log_result('nginx', 'internal_access', False, f'Error: {str(e)}')

    def test_pihole(self) -> None:
        # Test external DNS resolution through Pihole
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['172.20.0.20']  # Pihole IP
            answers = resolver.resolve('google.com', 'A')
            status = len(answers) > 0
            self.log_result('pihole', 'external_resolution', status,
                           'External DNS resolution working' if status else 'External DNS resolution failed')
        except Exception as e:
            self.log_result('pihole', 'external_resolution', False, f'Error: {str(e)}')

        # Test Pihole admin interface
        try:
            response = requests.get('http://172.20.0.20/admin/')
            status = response.status_code == 200
            self.log_result('pihole', 'admin_interface', status,
                           'Admin interface accessible' if status else 'Admin interface not accessible')
        except Exception as e:
            self.log_result('pihole', 'admin_interface', False, f'Error: {str(e)}')

    def test_postgresql(self) -> None:
        # Test PostgreSQL connection
        try:
            conn = psycopg2.connect(
                host='db.terrerov.com',
                database='postgres',
                user='postgres',
                password='your_password'
            )
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                status = cur.fetchone()[0] == 1
            conn.close()
            self.log_result('postgresql', 'connection', status,
                           'Database connection working' if status else 'Database connection failed')
        except Exception as e:
            self.log_result('postgresql', 'connection', False, f'Error: {str(e)}')

    def run_all_tests(self) -> List[Dict]:
        self.test_traefik()
        self.test_bind9()
        self.test_nginx()
        self.test_pihole()
        self.test_postgresql()
        return self.results

def main():
    tester = ServiceTester()
    results = tester.run_all_tests()
    print(json.dumps(results, indent=2))

    # Count failures
    failures = sum(1 for r in results if r['status'] == 'FAIL')
    if failures > 0:
        print(f'\n{failures} tests failed!')
        exit(1)
    else:
        print('\nAll tests passed!')
        exit(0)

if __name__ == '__main__':
    main()