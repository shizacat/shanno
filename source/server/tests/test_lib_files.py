from django.test import TestCase

from libs.files import FilesBase, CSVLabel, ConllupNER


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


class TestConllupNER(TestCase):
    def setUp(self):
        with open("tests/data/1.conllup", "rb") as f:
            file_obj = f.read()
        self.obj = ConllupNER(file_obj, mode="import")
    
    def test__eod_ch_cross(self):
        with self.subTest("one.1"):
            """Задевает хвостом"""
            rword = (0, 10)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, True)

        with self.subTest("one.2"):
            """Задевает хвостом"""
            rword = (0, 8)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, False)

        with self.subTest("two.1"):
            """Входит целиком """
            rword = (10, 15)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, True)

        with self.subTest("two.2"):
            """Входит целиком """
            rword = (8, 15)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, True)

        with self.subTest("tree.1"):
            """Задевает хвостом"""
            rword = (19, 25)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, True)

        with self.subTest("tree.2"):
            """Задевает хвостом"""
            rword = (20, 25)
            rbase = (8, 20)
            r = self.obj._eod_ch_cross(rword, rbase)
            self.assertEqual(r, False)
    
    def test__eod_process_seq(self):
        text = "Мама мыла раму где на балконе."
        labels = [("BIG", 0, 4)]
        r = self.obj._eod_process_seq(text, labels)
        self.assertEqual(type(r), list)
        self.assertEqual(
            r, [
                ('Мама', 'BIG'),
                ('мыла', None),
                ('раму', None),
                ('где', None),
                ('на', None),
                ('балконе.', None)
            ]
        )
    
    def test_export(self):
        def handler():
            data = [
                (
                    0,
                    "Мама мыла раму где на балконе.",
                    [("BIG", 0, 4)]
                )
            ]
            yield data, {}, "test", []
        
        r = self.obj.export_ds(handler)  # zip file
        self.assertTrue(r is not None)
