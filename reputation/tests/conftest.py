def pytest_collection_modifyitems(config, items):
    for item in items:
        item.add_marker("django_db")
