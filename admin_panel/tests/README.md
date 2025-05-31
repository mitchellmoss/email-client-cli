# Admin Panel Test Suite

Comprehensive test suite for the Email Order Admin Panel covering backend API, frontend UI, integration, and performance testing.

## Test Structure

```
tests/
├── backend/tests/          # Backend unit tests
│   ├── conftest.py        # Pytest fixtures
│   ├── test_auth.py       # Authentication tests
│   ├── test_orders.py     # Order management tests
│   ├── test_products.py   # Product mapping tests
│   └── test_settings.py   # Settings endpoint tests
├── frontend/tests/         # Frontend component tests
│   ├── setup.ts           # Test setup and mocks
│   ├── Dashboard.test.tsx # Dashboard tests
│   ├── Orders.test.tsx    # Orders page tests
│   ├── ProductMatching.test.tsx # Product matching tests
│   └── Settings.test.tsx  # Settings page tests
└── tests/                  # Integration & system tests
    ├── test_integration.py # End-to-end tests
    ├── test_database.py   # Database operation tests
    ├── test_email_processor_integration.py # Email processor integration
    └── test_performance.py # Performance/load tests
```

## Running Tests

### Quick Start

Run all tests:
```bash
./run_tests.sh all
```

### Backend Tests Only
```bash
./run_tests.sh backend
```

Or manually:
```bash
cd admin_panel/backend
source venv/bin/activate
pytest tests/ -v --cov=. --cov-report=html
```

### Frontend Tests Only
```bash
./run_tests.sh frontend
```

Or manually:
```bash
cd admin_panel/frontend
npm test
npm run test:coverage  # With coverage
npm run test:ui        # With UI
```

### Integration Tests
```bash
cd admin_panel/backend
pytest ../tests/test_integration.py -v
```

### Performance Tests
```bash
cd admin_panel/backend
locust -f ../tests/test_performance.py --host http://localhost:8000
```
Then open http://localhost:8089 to configure and run tests.

### Code Quality Checks
```bash
./run_tests.sh quality
```

## Test Categories

### Unit Tests
- **Authentication**: Login, token management, user operations
- **Orders**: CRUD operations, status updates, exports
- **Products**: Mapping management, SKU validation, suggestions
- **Settings**: Configuration management, system info

### Integration Tests
- End-to-end workflows
- Database operations
- Email processor integration
- Permission enforcement
- Concurrent operations

### Performance Tests
- Load testing with Locust
- Concurrent user simulation
- Stress testing specific endpoints
- Throughput measurements

## Coverage Reports

After running tests with coverage:
- Backend: `admin_panel/backend/htmlcov/index.html`
- Frontend: `admin_panel/frontend/coverage/index.html`

## Test Configuration

### Backend (pytest.ini)
```ini
[tool:pytest]
testpaths = tests ../tests
python_files = test_*.py
addopts = -v --strict-markers --tb=short
```

### Frontend (vitest.config.ts)
```typescript
test: {
  globals: true,
  environment: 'jsdom',
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json', 'html']
  }
}
```

## Writing New Tests

### Backend Test Example
```python
def test_create_order(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/orders",
        json={"order_id": "12345", ...},
        headers=auth_headers
    )
    assert response.status_code == 201
```

### Frontend Test Example
```typescript
it('displays order details', async () => {
  render(<Orders />);
  await waitFor(() => {
    expect(screen.getByText('Order #12345')).toBeInTheDocument();
  });
});
```

## Continuous Integration

Tests can be integrated into CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Backend Tests
  run: |
    cd admin_panel/backend
    pip install -r requirements.txt
    pytest tests/ --cov

- name: Run Frontend Tests
  run: |
    cd admin_panel/frontend
    npm install
    npm run test:coverage
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure virtual environment is activated
2. **Database errors**: Check test database permissions
3. **Frontend test failures**: Clear node_modules and reinstall
4. **Performance test connection**: Ensure backend is running

### Debug Mode

Run tests with more verbose output:
```bash
pytest -vvs tests/test_auth.py::TestAuthentication::test_login_success
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use pytest fixtures for common setup
3. **Mocking**: Mock external dependencies
4. **Coverage**: Aim for >80% code coverage
5. **Performance**: Mark slow tests with `@pytest.mark.slow`

## Test Data

Test fixtures provide consistent data:
- Users: `test@example.com` / `testpassword123`
- Admin: `admin@example.com` / `adminpass123`
- Sample orders: See `conftest.py`

## Contributing

1. Write tests for new features
2. Ensure all tests pass before PR
3. Maintain or improve coverage
4. Follow existing test patterns
5. Document complex test scenarios