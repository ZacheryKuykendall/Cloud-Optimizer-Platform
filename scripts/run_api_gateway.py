import os
import sys
import subprocess
import argparse

def main():
    """
    Run the API Gateway service with simulation mode enabled by default.
    This ensures the service can run without requiring actual cloud credentials.
    """
    parser = argparse.ArgumentParser(description="Run the Cloud Optimizer API Gateway")
    parser.add_argument("--simulation", "-s", action="store_true", default=True,
                        help="Enable simulation mode (default: True)")
    parser.add_argument("--no-simulation", dest="simulation", action="store_false",
                        help="Disable simulation mode and use actual cloud credentials")
    parser.add_argument("--port", "-p", type=int, default=8000,
                        help="Port to run the API Gateway on (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="Host to bind the server to (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    # Set simulation mode environment variable
    if args.simulation:
        os.environ["CLOUD_OPTIMIZER_SIMULATION"] = "true"
        print("=== Running in SIMULATION MODE ===")
        print("Using simulated cloud provider data instead of actual API calls")
    else:
        os.environ["CLOUD_OPTIMIZER_SIMULATION"] = "false"
        print("=== Running with ACTUAL CREDENTIALS ===")
        print("Make sure your cloud provider credentials are properly configured")
    
    # Change to the API Gateway directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    api_gateway_dir = os.path.join(os.path.dirname(script_dir), "api-gateway")
    
    if not os.path.exists(api_gateway_dir):
        print(f"Error: API Gateway directory not found at {api_gateway_dir}")
        return 1
    
    # Change to the API Gateway directory
    os.chdir(api_gateway_dir)
    
    # Run the API Gateway with uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", args.host,
        "--port", str(args.port),
        "--reload"
    ]
    
    print(f"Starting API Gateway at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")
    
    try:
        # Run the uvicorn server
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nAPI Gateway stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 