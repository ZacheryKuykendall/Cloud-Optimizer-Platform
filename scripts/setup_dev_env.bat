@echo off
setlocal enabledelayedexpansion

:: Colors for output
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

:: Function to print status messages
:print_status
echo %GREEN%[+]%NC% %~1
exit /b 0

:print_warning
echo %YELLOW%[!]%NC% %~1
exit /b 0

:print_error
echo %RED%[-]%NC% %~1
exit /b 0

:: Check system requirements
call :print_status "Checking system requirements..."

set REQUIREMENTS=python3 pip node npm docker docker-compose
set MISSING_REQUIREMENTS=0

for %%c in (%REQUIREMENTS%) do (
    where %%c >nul 2>nul
    if !errorlevel! neq 0 (
        call :print_error "%%c is not installed"
        set /a MISSING_REQUIREMENTS+=1
    ) else (
        for /f "tokens=*" %%p in ('where %%c') do (
            call :print_status "%%c is installed (%%p)"
        )
    )
)

if %MISSING_REQUIREMENTS% neq 0 (
    call :print_error "Please install missing requirements and run this script again"
    exit /b 1
)

:: Create Python virtual environment
call :print_status "Setting up Python virtual environment..."
python -m venv venv
call venv\Scripts\activate.bat

:: Install Python dependencies
call :print_status "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r scripts\requirements.txt

:: Install Node.js dependencies
call :print_status "Installing Node.js dependencies..."
cd ..\cost-dashboard
call npm install
cd ..\scripts

:: Check if .env file exists
if not exist ..\.env (
    call :print_status "Creating .env file from template..."
    copy ..\.env.example ..\.env
    call :print_warning "Please update ..\.env with your credentials"
)

:: Create necessary directories
call :print_status "Creating necessary directories..."
if not exist ..\logs mkdir ..\logs
if not exist ..\data\prometheus mkdir ..\data\prometheus
if not exist ..\data\grafana mkdir ..\data\grafana

:: Verify Docker configuration
call :print_status "Verifying Docker configuration..."
docker info >nul 2>nul
if !errorlevel! neq 0 (
    call :print_error "Docker daemon is not running"
    exit /b 1
)

:: Pull required Docker images
call :print_status "Pulling Docker images..."
docker-compose -f ..\docker-compose.yml pull

:: Build local images
call :print_status "Building local images..."
docker-compose -f ..\docker-compose.yml build

:: Run health check
call :print_status "Running initial health check..."
python health_check.py --verbose

:: Final instructions
echo.
call :print_status "Development environment setup complete!"
echo.
echo Next steps:
echo 1. Update the .env file with your cloud provider credentials
echo 2. Start the services with: docker-compose up -d
echo 3. Access the dashboard at: http://localhost:3000
echo 4. Monitor the system at: http://localhost:9090 (Prometheus)
echo                          http://localhost:3001 (Grafana)
echo.
call :print_warning "Remember to never commit the .env file to version control"

:: Keep the virtual environment active
call venv\Scripts\activate.bat

endlocal
