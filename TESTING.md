# MADERA MCP - TESTING GUIDE

Comprehensive testing guide for MADERA MCP server.

---

## 📦 TEST STRUCTURE

```
tests/
├── conftest.py                 # Shared fixtures (PDFs, images, mocks)
├── test_hints_tools.py         # Unit tests for all 7 HINTS tools
├── test_mcp_server.py          # Integration tests for MCP server
└── __init__.py
```

**Test Coverage:**
- ✅ Unit tests for all 7 HINTS tools
- ✅ Integration tests for MCP server
- ✅ Performance benchmarks
- ✅ Error handling tests
- ✅ Parallel execution tests
- ✅ Confidence scoring tests

---

## 🚀 RUNNING TESTS

### Quick Start

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=madera --cov-report=html

# Run specific test file
pytest tests/test_hints_tools.py

# Run specific test class
pytest tests/test_hints_tools.py::TestBlankPageDetector

# Run specific test
pytest tests/test_hints_tools.py::TestBlankPageDetector::test_detect_no_blank_pages
```

### Run by Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only performance tests
pytest -m performance

# Skip slow tests
pytest -m "not slow"
```

### Docker Environment

```bash
# Run tests in Docker
docker-compose exec madera-mcp pytest

# Run with coverage
docker-compose exec madera-mcp pytest --cov=madera

# Run specific test
docker-compose exec madera-mcp pytest tests/test_hints_tools.py -v
```

---

## 🧪 TEST TYPES

### 1. Unit Tests (test_hints_tools.py)

Tests individual tools in isolation.

**What's tested:**
- ✅ Blank page detection (pixel variance, text density)
- ✅ ID card detection (aspect ratio, corners, barcode, hologram)
- ✅ CRA document identification (OCR patterns, issuer detection)
- ✅ Tax form detection (T4, T5, T1, RL-1, etc.)
- ✅ Document boundary detection (layout changes, page numbering)
- ✅ Fiscal year extraction (date patterns, year validation)
- ✅ Image quality assessment (DPI, blur, brightness, skew)

**Example:**
```bash
pytest tests/test_hints_tools.py::TestBlankPageDetector -v
```

### 2. Integration Tests (test_mcp_server.py)

Tests MCP server and tool registration.

**What's tested:**
- ✅ Server initialization
- ✅ Tool registration (all 7 tools)
- ✅ Tool execution through MCP
- ✅ Error handling
- ✅ Return format validation

**Example:**
```bash
pytest tests/test_mcp_server.py -v
```

### 3. Performance Tests

Benchmarks execution time for each tool.

**Speed Requirements:**
- `detect_blank_pages`: ~50ms per page
- `detect_id_card_sides`: ~50ms per page
- `identify_cra_document_type`: ~200ms per page
- `detect_tax_form_type`: ~100ms per page
- `detect_document_boundaries`: ~150ms total
- `detect_fiscal_year`: ~80ms per page
- `assess_image_quality`: ~100ms per page

**Example:**
```bash
pytest tests/test_hints_tools.py::TestPerformance -v
```

### 4. Error Handling Tests

Tests graceful failure for edge cases.

**What's tested:**
- ✅ Invalid PDF URLs
- ✅ Corrupted PDFs
- ✅ Empty PDFs
- ✅ Missing files
- ✅ Network errors

**Example:**
```bash
pytest tests/test_hints_tools.py::TestErrorHandling -v
```

---

## 📊 TEST FIXTURES

### Available Fixtures (conftest.py)

#### PDF Creation Fixtures

```python
# Create test PDF with multiple pages
def test_example(create_test_pdf, temp_dir):
    pages = ["Page 1", "Page 2", "blank"]
    pdf_path = create_test_pdf(pages, temp_dir / "test.pdf")
```

#### Pre-made Sample PDFs

```python
# 3-page PDF with text
def test_example(sample_pdf_3_pages):
    pass

# PDF with blank page
def test_example(sample_pdf_with_blank):
    pass

# PDF with ID cards
def test_example(sample_pdf_id_cards):
    pass

# PDF with tax forms
def test_example(sample_pdf_tax_forms):
    pass
```

#### Image Creation Fixtures

```python
# Create blank image
def test_example(create_blank_image):
    img = create_blank_image(width=850, height=1100)

# Create image with text
def test_example(create_text_image):
    img = create_text_image("Test Content")

# Create ID card image
def test_example(create_id_card_image):
    recto = create_id_card_image('recto')
    verso = create_id_card_image('verso')

# Create tax form image
def test_example(create_tax_form_image):
    t4 = create_tax_form_image('T4', 2024)

# Create CRA document image
def test_example(create_cra_document_image):
    noa = create_cra_document_image('notice_of_assessment', 2024)
```

---

## 🐛 DEBUGGING TESTS

### Verbose Output

```bash
# Show print statements
pytest -s

# Show full traceback
pytest --tb=long

# Show locals in traceback
pytest --showlocals

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

### Logging

```bash
# Show logs during tests
pytest --log-cli-level=DEBUG

# Show only failed test logs
pytest --log-cli-level=INFO
```

### Specific Tests

```bash
# Run tests matching pattern
pytest -k "blank_page"

# Run tests NOT matching pattern
pytest -k "not slow"

# Run failed tests from last run
pytest --lf

# Run failed tests first
pytest --ff
```

---

## 📈 TEST COVERAGE

### Generate Coverage Report

```bash
# HTML report (opens in browser)
pytest --cov=madera --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=madera --cov-report=term

# Both
pytest --cov=madera --cov-report=html --cov-report=term
```

### Coverage Goals

- **Overall**: > 80%
- **HINTS tools**: > 90% (critical path)
- **MCP server**: > 85%
- **Utils**: > 75%

---

## ✅ CONTINUOUS INTEGRATION

### Pre-commit Checks

```bash
# Run all tests before commit
pytest

# Run quick tests only
pytest -m "not slow"

# Run with coverage
pytest --cov=madera --cov-fail-under=80
```

### GitHub Actions (Example)

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=madera --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## 🔧 WRITING NEW TESTS

### Test Template

```python
import pytest
from madera.mcp.tools.hints.your_tool import YourTool

@pytest.mark.asyncio
class TestYourTool:
    """Test suite for your_tool"""

    async def test_basic_functionality(self, sample_pdf_3_pages):
        """Test basic functionality"""
        tool = YourTool()
        result = await tool.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        assert result.success is True
        assert result.data is not None
        assert result.confidence > 0.5

    async def test_error_handling(self):
        """Test error handling"""
        tool = YourTool()
        result = await tool.execute(presigned_url="file:///invalid.pdf")

        assert result.success is False
        assert result.error is not None

    async def test_performance(self, sample_pdf_3_pages):
        """Test performance"""
        tool = YourTool()
        result = await tool.execute(presigned_url=f"file://{sample_pdf_3_pages}")

        # Adjust expected time based on your tool
        assert result.execution_time_ms < 500
```

### Best Practices

1. **Use descriptive test names**: `test_detect_blank_page_in_middle`
2. **Test one thing per test**: Don't test multiple scenarios in one test
3. **Use fixtures**: Reuse setup code via fixtures
4. **Test edge cases**: Empty inputs, malformed data, etc.
5. **Test error paths**: Don't just test happy path
6. **Check confidence scores**: Ensure confidence makes sense
7. **Benchmark performance**: Use `execution_time_ms`

---

## 📝 TEST CHECKLIST

For each new tool, ensure:

- [ ] Unit tests for core functionality
- [ ] Edge case tests (empty, invalid, corrupted)
- [ ] Error handling tests
- [ ] Performance benchmarks
- [ ] Integration test in MCP server
- [ ] Confidence scoring tests
- [ ] Parallel execution tests
- [ ] Return format validation

---

## 🚨 TROUBLESHOOTING

### Common Issues

**Issue: Tests fail with "No module named 'madera'"**
```bash
# Solution: Install package in editable mode
pip install -e .
```

**Issue: Async tests don't run**
```bash
# Solution: Install pytest-asyncio
pip install pytest-asyncio
```

**Issue: Image creation fails**
```bash
# Solution: Install required dependencies
apt-get install -y tesseract-ocr poppler-utils libgl1-mesa-glx libglib2.0-0
```

**Issue: Tests are too slow**
```bash
# Solution: Run in parallel
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
```

---

## 📞 SUPPORT

For test failures or questions:
1. Check logs: `pytest -v --log-cli-level=DEBUG`
2. Run single test: `pytest path/to/test.py::test_name -v`
3. Check fixtures: `pytest --fixtures`
4. Check coverage: `pytest --cov=madera --cov-report=term-missing`

---

**Happy Testing! 🧪**
