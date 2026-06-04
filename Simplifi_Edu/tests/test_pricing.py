import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.models import TokenUsage
from preset_question_agent.pricing import estimate_cost


class PricingTests(unittest.TestCase):
    def test_estimates_gemini_lite_cost(self):
        cost = estimate_cost("gemini-2.5-flash-lite", TokenUsage(input_tokens=1200, output_tokens=700))
        self.assertEqual(cost.total_cost_usd, 0.0004)

    def test_estimates_cached_input(self):
        cost = estimate_cost(
            "gpt-5-nano",
            TokenUsage(input_tokens=1000, cached_input_tokens=500, output_tokens=1000),
        )
        self.assertEqual(cost.input_cost_usd, 0.000025)
        self.assertEqual(cost.cached_input_cost_usd, 0.0000025)
        self.assertEqual(cost.output_cost_usd, 0.0004)


if __name__ == "__main__":
    unittest.main()
