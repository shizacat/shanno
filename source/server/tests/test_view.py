from django.test import TestCase

from annotation.views import ProjectViewSet
from annotation import models


class TestPViewExport(TestCase):

    def setUp(self):
        # Models
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0]
        )
        self.document = models.Documents.objects.create(
            project=self.project, file_name="0001"
        )
        self.seq1 = models.Sequence.objects.create(
            document=self.document, text="Мама мыла раму где на балконе.",
            order=1
        )
        self.seq2 = models.Sequence.objects.create(
            document=self.document, text="Пожар в лесу горел все сильнее.",
            order=1
        )
        self.label1 = models.TlLabels.objects.create(
            project=self.project, name="BIG"
        )
        self.seq1_label = models.TlSeqLabel.objects.create(
            sequence=self.seq1, label=self.label1,
            offset_start=0, offset_stop=4
        )
        # Object
        self.obj = ProjectViewSet()

    def test__eod_process_seq(self):
        r = self.obj._eod_process_seq(
            self.seq1.text,
            models.TlSeqLabel.objects.filter(
                sequence=self.seq1).order_by("offset_start")
        )
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

    def test__export_one_doc(self):
        r = self.obj._export_one_doc(self.document)
        self.assertEqual(type(r), list)
        self.assertEqual(len(r), 2)
