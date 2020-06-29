from django.test import TestCase

from libs.files import FilesBase, CSVLabel


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

class TestCSVLabel(TestCase):

    def setUp(self):
        with open("tests/data/dc_sample.csv", "rb") as f:
            file_obj = f.read()
        self.obj = CSVLabel(file_obj, mode="import")

    def test__meta_to_dict(self):
        r = self.obj._meta_to_dict("key = value")
        self.assertEqual(r["key"], "value")
