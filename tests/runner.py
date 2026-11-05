"""Close application pools before Django removes its isolated test database."""

from django.test.runner import DiscoverRunner

from tests.test_cases import drain_technical_logs


class ResilienceTestRunner(DiscoverRunner):
    def teardown_databases(self, old_config, **kwargs):
        drain_technical_logs()
        return super().teardown_databases(old_config, **kwargs)
