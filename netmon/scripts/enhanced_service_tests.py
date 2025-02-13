#!/usr/bin/env python3
import subprocess
import requests
import socket
import ssl
import dns.resolver
import psycopg2
import json
import logging
import docker
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log'),
        logging.StreamHandler()
    ]
)

class ErrorSeverity(Enum):
    LOW = "low"
    MODERATE = "moderate"
    CRITICAL = "critical"

class TestError:
    def __init__(self, service: str, error_type: str, message: str, severity: ErrorSeverity):
        self.service = service
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.timestamp = datetime.utcnow()

class AutoResolver:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.resolution_attempts = {}

    def can_auto_resolve(self, error: TestError) -> bool:
        # Define which errors can be auto-resolved
        auto_resolvable = {
            'connection_error': [ErrorSeverity.MODERATE],
            'timeout_error': [ErrorSeverity.MODERATE],
            'service_unavailable': [ErrorSeverity.MODERATE],
        }
        return error.error_type in auto_resolvable and error.severity in auto_resolvable[error.error_type]

    def restart_container(self, service_name: str) -> bool:
        try:
            container = self.docker_client.containers.get(f'terrerov_net_{service_name}_1')
            container.restart()
            logging.info(f"Successfully restarted container for service: {service_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to restart container {service_name}: {str(e)}")
            return False

    def restart_dependent_services(self, service_name: str) -> bool:
        # Define service dependencies
        dependencies = {
            'traefik': ['nginx'],
            'bind9': ['pihole'],
            'postgresql': []
        }
        
        success = True
        if service_name in dependencies:
            for dep in dependencies[service_name]:
                if not self.restart_container(dep):
                    success = False
        return success

    def resolve(self, error: TestError) -> bool:
        if not self.can_auto_resolve(error):
            return False

        service_key = f"{error.service}_{error.error_type}"
        attempt_count = self.resolution_attempts.get(service_key, 0)
        
        if attempt_count >= 3:  # Limit resolution attempts
            logging.warning(f"Maximum auto-resolution attempts reached for {error.service}")
            return False

        self.resolution_attempts[service_key] = attempt_count + 1
        
        # Try to restart the affected service
        if self.restart_container(error.service):
            if error.severity == ErrorSeverity.CRITICAL:
                # For critical errors, also restart dependent services
                self.restart_dependent_services(error.service)
            return True
        return False

class ServiceTester:
    def __init__(self):
        self.results = []
        self.errors = []
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['172.20.0.10']  # Bind9 server IP
        self.auto_resolver = AutoResolver()

    def log_error(self, service: str, error_type: str, message: str, severity: ErrorSeverity) -> None:
        error = TestError(service, error_type, message, severity)
        self.errors.append(error)
        logging.error(f"{service} - {error_type}: {message} (Severity: {severity.value})")

    def generate_troubleshooting_guide(self, error: TestError) -> str:
        guides = {
            'traefik': {
                'connection_error': """
                1. Check Traefik container status: docker ps | grep traefik
                2. Verify Traefik configuration:
                   - Check traefik.toml for correct entrypoints
                   - Verify SSL certificate paths
                   - Review routing rules
                3. Check Traefik logs: docker logs terrerov_net_traefik_1
                4. Verify network connectivity:
                   - Test ports 80 and 443: netstat -tuln
                   - Check firewall rules
                5. Verify SSL certificates:
                   - Check certificate validity
                   - Verify Cloudflare API key
                """,
                'ssl_error': """
                1. Verify SSL certificate status:
                   - Check certificate expiration
                   - Verify Cloudflare DNS records
                2. Review Traefik SSL configuration:
                   - Check certResolver settings
                   - Verify ACME challenge configuration
                3. Check Traefik logs for SSL-related errors
                4. Verify Cloudflare API key and permissions
                """
            },
            'bind9': {
                'resolution_error': """
                1. Check Bind9 container status
                2. Verify zone files:
                   - Review db.terrerov.com for correct records
                   - Check db.172.18.in-addr.arpa for reverse lookup
                3. Validate named configuration:
                   - named.conf.local
                   - named.conf.options
                4. Check Bind9 logs for errors
                5. Test DNS resolution manually:
                   - dig @172.20.0.10 www.terrerov.com
                   - dig -x 172.20.0.10 @172.20.0.10
                """
            },
            'nginx': {
                'service_unavailable': """
                1. Check Nginx container status
                2. Verify Nginx configuration:
                   - Review nginx.conf
                   - Check virtual host configurations
                3. Examine Nginx logs
                4. Verify file permissions
                5. Test Nginx internally:
                   - curl -H "Host: nginx.terrerov.com" http://localhost:8080
                """
            },
            'pihole': {
                'dns_error': """
                1. Check Pihole container status
                2. Verify Pihole configuration:
                   - Review upstream DNS settings
                   - Check custom.list entries
                3. Examine Pihole logs
                4. Test DNS resolution:
                   - dig @172.20.0.20 google.com
                5. Check Pihole web interface
                """
            },
            'postgresql': {
                'connection_error': """
                1. Check PostgreSQL container status
                2. Verify database connectivity:
                   - Test with psql
                   - Check port availability
                3. Review PostgreSQL logs
                4. Verify database credentials
                5. Check database permissions
                """
            }
        }

        if error.service in guides and error.error_type in guides[error.service]:
            return guides[error.service][error.error_type]
        return "No specific troubleshooting guide available for this error."

    def handle_test_failure(self, service: str, error_type: str, message: str, severity: ErrorSeverity) -> None:
        self.log_error(service, error_type, message, severity)
        error = TestError(service, error_type, message, severity)

        # Attempt automatic resolution
        if self.auto_resolver.can_auto_resolve(error):
            logging.info(f"Attempting automatic resolution for {service} {error_type}")
            if self.auto_resolver.resolve(error):
                logging.info(f"Automatic resolution successful for {service}")
                # Rerun the test to verify the fix
                return True
            else:
                logging.warning(f"Automatic resolution failed for {service}")

        # Generate troubleshooting guide
        guide = self.generate_troubleshooting_guide(error)
        logging.info(f"Troubleshooting guide for {service} {error_type}:\n{guide}")
        return False

    def test_traefik(self) -> None:
        # Test HTTP to HTTPS redirect
        try:
            response = requests.get('http://www.terrerov.com', allow_redirects=False)
            if not (response.status_code == 301 and 'https://' in response.headers.get('Location', '')):
                self.handle_test_failure('traefik', 'redirect_error', 'HTTP to HTTPS redirect not working', ErrorSeverity.MODERATE)
        except requests.exceptions.ConnectionError as e:
            self.handle_test_failure('traefik', 'connection_error', str(e), ErrorSeverity.CRITICAL)

        # Test HTTPS access and SSL
        try:
            response = requests.get('https://www.terrerov.com', verify=True)
            if response.status_code != 200:
                self.handle_test_failure('traefik', 'https_error', 'HTTPS access failed', ErrorSeverity.CRITICAL)
        except requests.exceptions.SSLError as e:
            self.handle_test_failure('traefik', 'ssl_error', str(e), ErrorSeverity.CRITICAL)
        except requests.exceptions.ConnectionError as e:
            self.handle_test_failure('traefik', 'connection_error', str(e), ErrorSeverity.CRITICAL)

    def test_bind9(self) -> None:
        try:
            answers = self.resolver.resolve('traefik.terrerov.com', 'A')
            if not (len(answers) > 0 and str(answers[0]).startswith('172.20.')):
                self.handle_test_failure('bind9', 'resolution_error', 'Internal DNS resolution failed', ErrorSeverity.CRITICAL)
        except Exception as e:
            self.handle_test_failure('bind9', 'resolution_error', str(e), ErrorSeverity.CRITICAL)

    def test_nginx(self) -> None:
        try:
            response = requests.get('http://nginx.terrerov.com:8080')
            if response.status_code != 200:
                self.handle_test_failure('nginx', 'service_unavailable', 'Nginx service not responding correctly', ErrorSeverity.MODERATE)
        except requests.exceptions.ConnectionError as e:
            self.handle_test_failure('nginx', 'connection_error', str(e), ErrorSeverity.MODERATE)

    def test_pihole(self) -> None:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['172.20.0.20']
            answers = resolver.resolve('google.com', 'A')
            if not len(answers) > 0:
                self.handle_test_failure('pihole', 'dns_error', 'External DNS resolution failed', ErrorSeverity.CRITICAL)
        except Exception as e:
            self.handle_test_failure('pihole', 'dns_error', str(e), ErrorSeverity.CRITICAL)

    def test_postgresql(self) -> None:
        try:
            conn = psycopg2.connect(
                host='db.terrerov.com',
                database='postgres',
                user='postgres',
                password='your_password'
            )
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                if cur.fetchone()[0] != 1:
                    self.handle_test_failure('postgresql', 'query_error', 'Database query failed', ErrorSeverity.MODERATE)
            conn.close()
        except psycopg2.Error as e:
            self.handle_test_failure('postgresql', 'connection_error', str(e), ErrorSeverity.MODERATE)

    def run_all_tests(self) -> Tuple[List[Dict], List[TestError]]:
        self.test_traefik()
        self.test_bind9()
        self.test_nginx()
        self.test_pihole()
        self.test_postgresql()
        return self.results, self.errors

def main():
    tester = ServiceTester()
    results, errors = tester.run_all_tests()

    # Log final results
    logging.info("\nTest Results Summary:")
    logging.info(f"Total Errors: {len(errors)}")
    
    if errors:
        logging.error("\nDetected Errors:")
        for error in errors:
            logging.error(f"{error.service} - {error.error_type} ({error.severity.value}): {error.message}")
        exit(1)
    else:
        logging.info("All tests passed successfully!")
        exit(0)

if __name__ == '__main__':
    main()