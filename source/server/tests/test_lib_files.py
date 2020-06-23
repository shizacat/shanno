from django.test import TestCase

from libs.files import FilesBase


class test_tl_label(TestCase):
    def setUp(self):
        pass

    def test_get_docs(self):
        with self.subTest("1"):
            r = FilesBase.get_docs("text_label", "import")
            self.assertEqual(type(r), list)
        
        with self.subTest("1"):
            r = FilesBase.get_docs("text_label", "export")
            self.assertEqual(type(r), list)
