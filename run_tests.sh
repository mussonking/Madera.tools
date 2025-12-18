#!/bin/bash
# MADERA MCP - Quick Test Runner Script

set -e

echo "🧪 MADERA MCP - Running Tests"
echo "=============================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# Parse arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest -v
        ;;
    fast)
        echo -e "${YELLOW}Running fast tests only...${NC}"
        pytest -v -m "not slow"
        ;;
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest tests/test_hints_tools.py -v
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest tests/test_mcp_server.py -v
        ;;
    performance)
        echo -e "${YELLOW}Running performance benchmarks...${NC}"
        pytest tests/test_hints_tools.py::TestPerformance -v
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage...${NC}"
        pytest --cov=madera --cov-report=html --cov-report=term
        echo -e "${GREEN}✅ Coverage report generated: htmlcov/index.html${NC}"
        ;;
    single)
        if [ -z "$2" ]; then
            echo -e "${RED}❌ Usage: ./run_tests.sh single <test_name>${NC}"
            exit 1
        fi
        echo -e "${GREEN}Running single test: $2${NC}"
        pytest "$2" -v
        ;;
    watch)
        echo -e "${YELLOW}Running tests in watch mode...${NC}"
        pytest-watch
        ;;
    *)
        echo -e "${RED}❌ Unknown test type: $TEST_TYPE${NC}"
        echo ""
        echo "Usage: ./run_tests.sh [test_type]"
        echo ""
        echo "Test types:"
        echo "  all          - Run all tests (default)"
        echo "  fast         - Run fast tests only"
        echo "  unit         - Run unit tests"
        echo "  integration  - Run integration tests"
        echo "  performance  - Run performance benchmarks"
        echo "  coverage     - Run tests with coverage report"
        echo "  single <test> - Run a single test"
        echo "  watch        - Run tests in watch mode"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh"
        echo "  ./run_tests.sh fast"
        echo "  ./run_tests.sh coverage"
        echo "  ./run_tests.sh single tests/test_hints_tools.py::TestBlankPageDetector"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Tests completed!${NC}"
