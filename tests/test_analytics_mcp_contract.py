import inspect
from pathlib import Path
from unittest import TestCase

from apps.api.backend_api.main import app
from apps.api.backend_api import editorial_schemas as schemas
from apps.mcp import server


class AnalyticsMcpContractTests(TestCase):
    def test_http_mcp_and_documented_tools_share_response_models(self):
        pairs=(
            ("get_analytics_coverage","/integrations/editorial/analytics/coverage",schemas.AnalyticsCoverageResponse),
            ("get_platform_analytics","/integrations/editorial/analytics/overview",schemas.AnalyticsOverviewResponse),
            ("get_analytics_series","/integrations/editorial/analytics/series",schemas.AnalyticsSeriesResponse),
            ("compare_analytics_periods","/integrations/editorial/analytics/compare",schemas.AnalyticsCompareResponse),
            ("get_analytics_retention","/integrations/editorial/analytics/retention",schemas.AnalyticsRetentionResponse),
            ("list_market_analytics","/integrations/editorial/analytics/markets",schemas.AnalyticsMarketsResponse),
            ("get_market_analytics","/integrations/editorial/analytics/markets/{market_id}",schemas.AnalyticsMarketResponse),
            ("compare_editorial_analytics","/integrations/editorial/analytics/editorial",schemas.EditorialAnalyticsResponse),
        )
        spec=app.openapi()
        docs=(Path(__file__).resolve().parents[1]/"docs/specs/contracts/mcp-analytics.md").read_text()
        for tool,path,model in pairs:
            with self.subTest(tool=tool):
                self.assertEqual(inspect.signature(getattr(server,tool)).return_annotation,model)
                self.assertEqual(server.TOOL_SCOPES[tool],"analytics:read")
                self.assertEqual(spec["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1],model.__name__)
                self.assertIn(f"`{tool}`",docs)
