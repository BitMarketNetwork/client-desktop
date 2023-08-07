from shutil import rmtree
from unittest import TestCase

from bmnclient.config import Config
from bmnclient.version import ProductPaths
from tests.helpers import TestApplication


class TestConfig(TestCase):
    def setUp(self) -> None:
        self._application = TestApplication()

    def tearDown(self) -> None:
        self._application.setExitEvent()

    def test(self) -> None:
        configs_path = self._application.tempPath / "configs15"
        if configs_path.exists():
            rmtree(configs_path)
        self.assertFalse(configs_path.exists())
        configs_path.mkdir()

        for i in range(0, 1000):
            config = Config.create(configs_path, "test")
            self.assertIsInstance(config, Config)
            self.assertTrue(config.filePath.exists())
            if i > 0:
                self.assertEqual(
                    config.filePath,
                    configs_path
                    / (
                        ProductPaths.WALLET_DUPLICATE_FORMAT.format(
                            name="test", index=i
                        )
                        + ProductPaths.WALLET_SUFFIX
                    ),
                )
            else:
                self.assertEqual(
                    config.filePath,
                    configs_path / ("test" + ProductPaths.WALLET_SUFFIX),
                )
