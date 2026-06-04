import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_inspirer_agent.providers import OPENAI_RESPONSE_SCHEMA


class ProviderSchemaTests(unittest.TestCase):
    def test_openai_response_schema_requires_domains_and_categories(self):
        self.assertEqual(OPENAI_RESPONSE_SCHEMA["type"], "object")
        self.assertEqual(OPENAI_RESPONSE_SCHEMA["required"], ["recommended_career_domains", "categories"])
        self.assertIn("recommended_career_domains", OPENAI_RESPONSE_SCHEMA["properties"])
        domains = OPENAI_RESPONSE_SCHEMA["properties"]["recommended_career_domains"]
        self.assertEqual(domains["minItems"], 1)
        categories = OPENAI_RESPONSE_SCHEMA["properties"]["categories"]
        self.assertEqual(categories["minItems"], 3)
        self.assertEqual(categories["maxItems"], 3)
        category_item = categories["items"]
        self.assertEqual(category_item["required"], ["id", "title", "questions"])
        self.assertEqual(category_item["properties"]["questions"]["maxItems"], 10)


if __name__ == "__main__":
    unittest.main()
