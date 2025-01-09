#!/usr/bin/env python3
"""
Health check script for Cloud Optimizer Platform.
Tests all major integration points and services.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

# Service endpoints (configurable via environment variables)
SERVICES = {
    "api-gateway": "http://localhost:8080",
    "cost-normalizer": "http://localhost:8000",
    "network-manager": "http://localhost:8001",
    "cost-optimizer": "http://localhost:8002",
    "resource-inventory": "http://localhost:8003",
    "budget-manager": "http://localhost:8004",
    "prometheus": "http://localhost:9090",
    "grafana": "http://localhost:3001",
    "redis": "http://localhost:6379",
    "cost-storage": "http://localhost:5432",
}

async def check_service_health(session: aiohttp.ClientSession, name: str, url: str) -> Dict:
    """Check health of a service endpoint."""
    try:
        async with session.get(f"{url}/health") as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": name,
                    "status": "UP",
                    "latency": response.elapsed.total_seconds(),
                    "details": data
                }
            return {
                "name": name,
                "status": "DOWN",
                "error": f"HTTP {response.status}"
            }
    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "error": str(e)
        }

async def check_integration(session: aiohttp.ClientSession, name: str, url: str) -> Dict:
    """Test specific integration points."""
    try:
        # Different checks based on integration type
        if name == "aws-cost-explorer":
            endpoint = f"{url}/api/v1/costs/aws"
        elif name == "azure-cost-management":
            endpoint = f"{url}/api/v1/costs/azure"
        elif name == "gcp-billing":
            endpoint = f"{url}/api/v1/costs/gcp"
        elif name == "cross-cloud-vpn":
            endpoint = f"{url}/api/v1/network/vpn/status"
        else:
            endpoint = f"{url}/api/v1/status"

        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "name": name,
                    "status": "OK",
                    "latency": response.elapsed.total_seconds(),
                    "details": data
                }
            return {
                "name": name,
                "status": "FAILED",
                "error": f"HTTP {response.status}"
            }
    except Exception as e:
        return {
            "name": name,
            "status": "ERROR",
            "error": str(e)
        }

def print_results(results: List[Dict]) -> None:
    """Print results in a formatted table."""
    table = Table(title="Cloud Optimizer Platform Health Check")
    table.add_column("Service/Integration", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Latency", style="yellow")
    table.add_column("Details", style="white")

    for result in results:
        status_style = {
            "UP": "green",
            "DOWN": "red",
            "OK": "green",
            "FAILED": "red",
            "ERROR": "red"
        }.get(result["status"], "yellow")

        latency = f"{result.get('latency', 'N/A')}s" if result.get('latency') else "N/A"
        details = str(result.get('details', result.get('error', 'N/A')))

        table.add_row(
            result["name"],
            result["status"],
            latency,
            details[:50] + "..." if len(details) > 50 else details
        )

    console.print(table)

async def run_checks() -> List[Dict]:
    """Run all health checks."""
    async with aiohttp.ClientSession() as session:
        # Check core services
        service_checks = [
            check_service_health(session, name, url)
            for name, url in SERVICES.items()
        ]
        
        # Check integrations
        integration_checks = [
            check_integration(session, "aws-cost-explorer", SERVICES["api-gateway"]),
            check_integration(session, "azure-cost-management", SERVICES["api-gateway"]),
            check_integration(session, "gcp-billing", SERVICES["api-gateway"]),
            check_integration(session, "cross-cloud-vpn", SERVICES["network-manager"]),
            check_integration(session, "cost-optimization", SERVICES["cost-optimizer"]),
            check_integration(session, "resource-inventory", SERVICES["resource-inventory"]),
        ]
        
        all_results = await asyncio.gather(
            *service_checks,
            *integration_checks,
            return_exceptions=True
        )
        
        return [
            result if isinstance(result, dict) else 
            {"name": "unknown", "status": "ERROR", "error": str(result)}
            for result in all_results
        ]

@app.command()
def check(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
) -> None:
    """Run health checks on all Cloud Optimizer Platform services and integrations."""
    try:
        results = asyncio.run(run_checks())
        
        # Print results
        print_results(results)
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
                console.print(f"\nResults saved to {output}")
        
        # Determine exit code
        has_errors = any(r["status"] in ["DOWN", "ERROR", "FAILED"] for r in results)
        sys.exit(1 if has_errors else 0)
        
    except Exception as e:
        console.print(f"[red]Error running health checks: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    app()
