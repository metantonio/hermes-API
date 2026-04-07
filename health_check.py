#!/usr/bin/env python3
"""
Hermes Web Data API - Health Check
==================================
Quick health check for production monitoring.
"""

import sys
import os
import json
from datetime import datetime, timezone

# Add API directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from config import get_settings

# ============================================================================
# Health Check Classes
# ============================================================================

class HealthCheck:
    """Perform health checks on the API"""
    
    def __init__(self):
        self.results = []
        self.is_healthy = True
        self.errors = []
    
    def check_version(self) -> tuple:
        """Check API version"""
        try:
            from main import app
            version = app.version
            status = "OK" if version else "WARNING"
            self.results.append({
                "name": "Version",
                "status": status,
                "value": version,
            })
            return True
        except Exception as e:
            self.errors.append(f"Version check failed: {e}")
            return False
    
    def check_database(self) -> tuple:
        """Check database connection"""
        try:
            from models import create_database_engine
            
            settings = get_settings()
            db_url = os.getenv("DB_URL", "")
            
            if not db_url:
                self.results.append({
                    "name": "Database URL",
                    "status": "SKIPPED",
                    "value": "Not configured",
                })
                return True
            
            # Try to connect
            engine = create_database_engine(url=db_url)
            
            self.results.append({
                "name": "Database",
                "status": "OK",
                "value": db_url[:50],
            })
            return True
        except Exception as e:
            self.results.append({
                "name": "Database",
                "status": "ERROR",
                "value": str(e)[:200],
            })
            self.is_healthy = False
            return False
    
    def check_memory(self) -> tuple:
        """Check memory usage"""
        try:
            import resource
            
            mem_used = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB
            status = "OK" if mem_used < 512 else "WARNING"
            
            self.results.append({
                "name": "Memory",
                "status": status,
                "value": f"{mem_used:.1f} MB",
            })
            return True
        except Exception as e:
            self.errors.append(f"Memory check failed: {e}")
            return False
    
    def check_disk(self) -> tuple:
        """Check disk space"""
        try:
            import os
            
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = total - free
            percent = (used / total) * 100
            
            status = "OK" if percent < 90 else "WARNING"
            
            self.results.append({
                "name": "Disk",
                "status": status,
                "value": f"{percent:.1f}% used ({free / 1024 / 1024:.0f} MB free)",
            })
            return True
        except Exception as e:
            self.errors.append(f"Disk check failed: {e}")
            return False
    
    def check_endpoints(self) -> tuple:
        """Check API endpoints"""
        try:
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # Check health endpoint
            response = client.get("/health")
            health_ok = response.status_code == 200
            
            self.results.append({
                "name": "Health Endpoint",
                "status": "OK" if health_ok else "ERROR",
                "value": f"{response.status_code}",
            })
            
            # Check docs endpoint
            response = client.get("/docs")
            docs_ok = response.status_code == 200
            
            self.results.append({
                "name": "Docs Endpoint",
                "status": "OK" if docs_ok else "ERROR",
                "value": f"{response.status_code}",
            })
            
            return health_ok and docs_ok
        except Exception as e:
            self.errors.append(f"Endpoint check failed: {e}")
            return False
    
    def check_security(self) -> tuple:
        """Check security configuration"""
        try:
            from security_filter import SecurityFilter
            
            # Check if security filter is properly configured
            filter = SecurityFilter(strict_mode=True)
            
            # Test filtering
            test_input = "sk_live_abc123"
            filtered, alerts = filter.filter_content(test_input, "test")
            
            security_ok = "REDACTED" in filtered
            
            self.results.append({
                "name": "Security Filter",
                "status": "OK" if security_ok else "ERROR",
                "value": f"Redacted: {security_ok}",
            })
            
            return security_ok
        except Exception as e:
            self.errors.append(f"Security check failed: {e}")
            return False
    
    def run_all_checks(self) -> dict:
        """Run all health checks"""
        print("Running Hermes Web Data API Health Checks...")
        print("=" * 60)
        
        checks = [
            ("Version", self.check_version),
            ("Database", self.check_database),
            ("Memory", self.check_memory),
            ("Disk", self.check_disk),
            ("Endpoints", self.check_endpoints),
            ("Security", self.check_security),
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for name, check_func in checks:
            print(f"\nChecking {name}...", end=" ")
            
            if check_func():
                passed += 1
                print("✓")
            else:
                failed += 1
                print("✗")
        
        # Add skipped checks
        if not os.getenv("DB_URL"):
            skipped += 1
            print("\nDatabase URL not configured (skipped)")
        
        # Summary
        print("\n" + "=" * 60)
        print("HEALTH CHECK SUMMARY")
        print("=" * 60)
        
        status = "HEALTHY" if failed == 0 else "UNHEALTHY"
        
        print(f"  Status: {status}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Skipped: {skipped}")
        print("=" * 60)
        
        # Return results
        return {
            "status": status,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "checks": self.results,
            "errors": self.errors,
        }
    
    def print_detailed(self, results: dict) -> None:
        """Print detailed results"""
        print("\nDetailed Results:")
        print("-" * 60)
        
        for check in results.get("checks", []):
            status_icon = "✓" if check["status"] == "OK" else "✗"
            print(f"  {status_icon} {check['name']:20} {check['value']}")
        
        if results.get("errors"):
            print("\nErrors:")
            print("-" * 60)
            for error in results["errors"]:
                print(f"  ✗ {error}")
        
        # JSON output for monitoring systems
        print("\n" + "=" * 60)
        print("JSON OUTPUT (for monitoring):")
        print("-" * 60)
        
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": results["status"],
            "checks": results.get("checks", []),
        }
        
        print(json.dumps(output, indent=2))


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hermes Web Data API Health Check"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON for monitoring systems"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Run health checks
    health_check = HealthCheck()
    results = health_check.run_all_checks()
    
    # Print results
    if args.json:
        health_check.print_detailed(results)
    else:
        health_check.print_detailed(results)
        
        # Exit with appropriate code
        if results["status"] == "HEALTHY":
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()