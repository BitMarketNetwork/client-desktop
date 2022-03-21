from random import shuffle

from bmnclient.language import Language
from tests.helpers import TestCaseApplication


class TestLanguage(TestCaseApplication):
    def test(self) -> None:
        translation_list = list(Language.translationList())
        shuffle(translation_list)

        self.assertLessEqual(2, len(translation_list))
        for translation in translation_list:
            language = Language(translation["name"])
            if language.name == language.primaryName:
                self.assertEqual(0, len(language.translatorList))
                self.assertFalse(language.install())
                language.uninstall()
            else:
                self.assertLessEqual(1, len(language.translatorList))
                self.assertTrue(language.install())
                language.uninstall()
