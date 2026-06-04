import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_inspirer_agent.models import TokenUsage, ValidationError
from preset_inspirer_agent.pricing import estimate_cost


class PricingTests(unittest.TestCase):
    def test_estimates_gemini_flash_lite_cost(self):
        estimate = estimate_cost(
            "gemini-2.5-flash-lite",
            TokenUsage(input_tokens=1200, output_tokens=700, cached_input_tokens=0),
        )
        self.assertAlmostEqual(estimate.total_cost_usd, 0.0004)

    def test_rejects_unknown_model(self):
        with self.assertRaises(ValidationError):
            estimate_cost("unknown-model", TokenUsage(input_tokens=1, output_tokens=1))


if __name__ == "__main__":
    unittest.main()
