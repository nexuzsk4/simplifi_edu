import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from preset_question_agent.config import default_env_path, load_settings


class ConfigTests(unittest.TestCase):
    def test_default_temperature_is_zero_point_three(self):
        settings = load_settings(environ={}, env_file="missing.env")
        self.assertEqual(settings.temperature, 0.3)

    def test_temperature_can_be_overridden_from_env_file(self):
        env_file = Path(__file__).resolve().parents[2] / ".env.example"
        settings = load_settings(environ={}, env_file=env_file)
        self.assertEqual(settings.temperature, 0.3)

    def test_default_env_path_uses_monorepo_root(self):
        self.assertEqual(default_env_path(), Path(__file__).resolve().parents[2] / ".env")

    def test_uses_shared_env_prefix(self):
        settings = load_settings(
            environ={
                "LLM_PROVIDER": "openai",
                "LLM_MODEL": "gpt-5-nano",
                "LLM_TEMPERATURE": "0.2",
                "OPENAI_API_KEY": "key",
            },
            env_file="missing.env",
        )
        self.assertEqual(settings.provider, "openai")
        self.assertEqual(settings.model, "gpt-5-nano")
        self.assertEqual(settings.temperature, 0.2)
        self.assertEqual(settings.api_key, "key")


if __name__ == "__main__":
    unittest.main()
