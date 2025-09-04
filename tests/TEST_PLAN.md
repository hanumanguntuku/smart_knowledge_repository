
# 🧪 Smart Knowledge Repository - Test Plan

## 📊 Current Status
- **Total Source Modules**: 24
- **Current Coverage**: ~13% (3 main test files working)
- **Existing Tests**: 23 total (13 unit + 10 integration)
- **Test Infrastructure**: ✅ pytest, coverage, HTML reports

## 🎯 Testing Priorities

### Priority 1: Core Infrastructure (CRITICAL)
These modules are essential for basic system operation:

1. **src/core/config.py** → `test_config.py`
   - Configuration loading and validation
   - Environment variable handling
   - Default value testing

2. **src/core/database.py** → `test_database.py` 
   - SQLite connection management
   - Query execution and error handling
   - Transaction management

3. **src/storage/storage_manager.py** → `test_storage_manager.py`
   - Document storage and retrieval
   - Category management
   - Search functionality

4. **src/search/search_engine.py** → `test_search_engine.py`
   - Search query processing
   - Result ranking and scoring
   - Integration with storage

5. **src/search/embedding_engine.py** → `test_embedding_engine.py`
   - Embedding generation
   - Model loading and fallbacks
   - Performance testing

### Priority 2: AI & API Features (HIGH)
These modules provide core AI functionality:

6. **src/ai/scope_chatbot.py** → `test_scope_chatbot.py`
   - RAG pipeline testing
   - Query processing and response generation
   - Context management

7. **src/ai/conversation_manager.py** → `test_conversation_manager.py`
   - Conversation state management
   - Message history handling

8. **src/crawlers/web_scraper.py** → `test_web_scraper.py` ✅
   - Web content extraction
   - URL validation and processing
   - Rate limiting and error handling

9. **src/api/main.py** → `test_api_main.py`
   - FastAPI endpoint testing
   - Request/response validation
   - Error handling

10. **src/api/models.py** → `test_api_models.py`
    - Pydantic model validation
    - Data serialization/deserialization

### Priority 3: Supporting Services (MEDIUM)
Additional functionality and utilities:

11. **src/services/conversation_export.py** → `test_conversation_export.py`
    - Export functionality
    - Format validation
    - File generation

12. **src/processors/data_validator.py** → `test_data_validator.py`
    - Data validation rules
    - Content quality checks

13. **src/search/chroma_client.py** → `test_chroma_client.py`
    - ChromaDB integration
    - Vector operations
    - Collection management

14. **src/search/knowledge_graph.py** → `test_knowledge_graph.py`
    - Graph construction and queries
    - Relationship mapping

### Priority 4: Setup & Utilities (LOW)
Setup, migration, and utility scripts:

15. **src/setup/setup_installer.py** → `test_setup_installer.py`
16. **src/setup/setup_openai.py** → `test_setup_openai.py`
17. **src/migration/chromadb_migration.py** → `test_chromadb_migration.py`
18. **src/migration/migrate_to_gemini_embeddings.py** → `test_migrate_to_gemini_embeddings.py`
19. **src/scripts/check_chromadb.py** → `test_check_chromadb.py`
20. **src/scripts/regenerate_embeddings.py** → `test_regenerate_embeddings.py`
21. **src/scripts/verify_metadata_fix.py** → `test_verify_metadata_fix.py`

### Priority 5: UI Components (OPTIONAL)
User interface testing:

22. **src/ui/streamlit_app.py** → `test_streamlit_app.py`
    - UI component testing
    - User interaction flows
    - Mock testing for Streamlit components

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution (<1s per test)
- Target: 80%+ line coverage

### Integration Tests (`tests/integration/`)
- Test component interactions
- Use test databases and mock APIs
- Medium execution time (1-10s per test)
- Target: Cover critical user workflows

### End-to-End Tests (Future)
- Test complete user scenarios
- Use real databases (test data)
- Slower execution (10s+ per test)
- Target: Cover main use cases

## 📋 Test Implementation Strategy

### Phase 1: Fix Existing Tests (Week 1)
- ✅ Fix import errors in existing tests
- ✅ Update config references 
- ✅ Ensure all existing tests pass
- ✅ Set up coverage reporting

### Phase 2: Core Infrastructure (Week 2)
- ✅ Implement Priority 1 tests (5 modules)
- Target: 50%+ coverage of core modules
- Set up CI/CD pipeline

### Phase 3: AI & API Features (Week 3)
- Implement Priority 2 tests (5 modules)
- Target: 60%+ overall coverage
- Add performance benchmarks

### Phase 4: Supporting Services (Week 4)
- Implement Priority 3 tests (4 modules)
- Target: 70%+ overall coverage
- Add integration test scenarios

### Phase 5: Complete Coverage (Week 5+)
- Implement remaining tests
- Target: 80%+ overall coverage
- Add end-to-end test scenarios

## 🛠️ Test Infrastructure

### Testing Tools
- **pytest**: Main testing framework
- **pytest-cov**: Coverage reporting
- **pytest-html**: HTML test reports
- **pytest-mock**: Mocking utilities
- **unittest.mock**: Python mocking

### Mock Strategy
- Mock external APIs (OpenAI, Gemini)
- Mock file system operations
- Mock database connections for unit tests
- Use test databases for integration tests

### Test Data Management
- Create `tests/data/` for test datasets
- Use temporary files/databases for isolation
- Mock API responses for consistency

### Coverage Targets
- **Unit Tests**: 80%+ line coverage per module
- **Integration Tests**: 70%+ workflow coverage
- **Overall**: 75%+ project coverage

## 🚀 Running Tests

### Basic Commands
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run with detailed output
pytest -v --tb=long

# Run specific test file
pytest tests/unit/test_config.py -v
```

### Coverage Analysis
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html:tests/coverage_html

# View coverage in terminal
pytest --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=src --cov-fail-under=70
```

### CI/CD Integration
```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src --cov-fail-under=70
```

## 📈 Success Metrics

### Week 1 Goals
- ✅ All existing tests pass
- ✅ Coverage reporting working
- ✅ Test infrastructure complete

### Week 2 Goals
- 5 new test modules (Priority 1)
- 50%+ coverage on core modules
- Automated test running

### Month 1 Goals
- 15+ test modules implemented
- 70%+ overall coverage
- CI/CD pipeline active

### Final Goals
- 80%+ test coverage
- All critical paths tested
- Performance benchmarks established
- Documentation complete

## 🔧 Test Quality Standards

### Unit Test Standards
- Each test should test one specific behavior
- Tests should be independent and repeatable
- Use descriptive test names and docstrings
- Mock external dependencies
- Test both success and failure cases

### Integration Test Standards
- Test realistic user scenarios
- Use test data that mirrors production
- Clean up resources after tests
- Test error handling and edge cases

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to test classes and methods
- Keep tests simple and readable

## 📝 Test Documentation

Each test module should include:
- Module docstring explaining what's being tested
- Test class docstrings describing the test scope
- Individual test docstrings explaining the specific behavior
- Setup/teardown documentation for complex tests

## 🚨 Critical Test Cases

### Must-Have Tests
1. **Data integrity**: No data loss during operations
2. **Security**: Input validation and sanitization
3. **Performance**: Response times within acceptable limits
4. **Error handling**: Graceful failure modes
5. **API compatibility**: Backward compatibility maintenance

### Risk Areas
1. **Database operations**: Transaction safety
2. **AI model integration**: Fallback mechanisms
3. **Web scraping**: Rate limiting and robots.txt compliance
4. **File operations**: Permission and disk space handling
5. **Configuration**: Environment variable validation

This comprehensive test plan ensures systematic coverage of the Smart Knowledge Repository
while prioritizing critical functionality and maintaining code quality standards.
