#!/bin/bash

# Admin Panel Test Runner Script
# This script runs all tests for the admin panel (backend and frontend)

set -e  # Exit on error

echo "======================================"
echo "Admin Panel Test Suite"
echo "======================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run backend tests
run_backend_tests() {
    echo -e "${YELLOW}Running Backend Tests...${NC}"
    echo "======================================"
    
    cd admin_panel/backend
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    
    # Run pytest with coverage
    echo -e "${GREEN}Running unit tests...${NC}"
    pytest tests/ -v --cov=. --cov-report=html --cov-report=term
    
    # Run integration tests
    echo -e "${GREEN}Running integration tests...${NC}"
    pytest ../tests/test_integration.py -v
    
    # Run database tests
    echo -e "${GREEN}Running database tests...${NC}"
    pytest ../tests/test_database.py -v
    
    # Run email processor integration tests
    echo -e "${GREEN}Running email processor integration tests...${NC}"
    pytest ../tests/test_email_processor_integration.py -v
    
    deactivate
    cd ../..
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${YELLOW}Running Frontend Tests...${NC}"
    echo "======================================"
    
    cd admin_panel/frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    # Run vitest
    echo -e "${GREEN}Running component tests...${NC}"
    npm run test:coverage
    
    cd ../..
}

# Function to run performance tests
run_performance_tests() {
    echo -e "${YELLOW}Running Performance Tests...${NC}"
    echo "======================================"
    
    cd admin_panel/backend
    source venv/bin/activate
    
    echo -e "${GREEN}Starting performance test server...${NC}"
    echo "Note: Performance tests require manual interaction."
    echo "Run 'locust -f ../tests/test_performance.py --host http://localhost:8000'"
    echo "Then open http://localhost:8089 to run tests"
    
    deactivate
    cd ../..
}

# Function to run linting and type checking
run_code_quality_checks() {
    echo -e "${YELLOW}Running Code Quality Checks...${NC}"
    echo "======================================"
    
    # Backend checks
    echo -e "${GREEN}Backend code quality...${NC}"
    cd admin_panel/backend
    source venv/bin/activate
    
    echo "Running black..."
    black . --check
    
    echo "Running isort..."
    isort . --check-only
    
    echo "Running flake8..."
    flake8 .
    
    echo "Running mypy..."
    mypy .
    
    deactivate
    cd ../..
    
    # Frontend checks
    echo -e "${GREEN}Frontend code quality...${NC}"
    cd admin_panel/frontend
    
    echo "Running ESLint..."
    npm run lint
    
    echo "Running TypeScript check..."
    npx tsc --noEmit
    
    cd ../..
}

# Function to generate test report
generate_report() {
    echo -e "${YELLOW}Generating Test Report...${NC}"
    echo "======================================"
    
    # Create reports directory
    mkdir -p admin_panel/test_reports
    
    # Copy coverage reports
    cp -r admin_panel/backend/htmlcov admin_panel/test_reports/backend_coverage || true
    cp -r admin_panel/frontend/coverage admin_panel/test_reports/frontend_coverage || true
    
    # Create summary report
    cat > admin_panel/test_reports/summary.md << EOF
# Test Report Summary
Generated on: $(date)

## Backend Tests
- Unit Tests: Check backend_coverage/index.html
- Integration Tests: Passed
- Database Tests: Passed
- Email Processor Integration: Passed

## Frontend Tests
- Component Tests: Check frontend_coverage/index.html
- Coverage Report: Available in coverage directory

## Code Quality
- Backend: Black, isort, flake8, mypy checks passed
- Frontend: ESLint and TypeScript checks passed

## Performance Tests
- Run manually using Locust
- Command: locust -f tests/test_performance.py --host http://localhost:8000
EOF
    
    echo -e "${GREEN}Test reports generated in admin_panel/test_reports/${NC}"
}

# Main execution
main() {
    # Parse command line arguments
    case "$1" in
        backend)
            run_backend_tests
            ;;
        frontend)
            run_frontend_tests
            ;;
        performance)
            run_performance_tests
            ;;
        quality)
            run_code_quality_checks
            ;;
        all)
            run_backend_tests
            echo ""
            run_frontend_tests
            echo ""
            run_code_quality_checks
            echo ""
            generate_report
            ;;
        *)
            echo "Usage: $0 {backend|frontend|performance|quality|all}"
            echo ""
            echo "Options:"
            echo "  backend     - Run backend tests only"
            echo "  frontend    - Run frontend tests only"
            echo "  performance - Instructions for performance tests"
            echo "  quality     - Run code quality checks"
            echo "  all         - Run all tests and generate report"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}Tests completed!${NC}"
}

# Run main function
main "$@"