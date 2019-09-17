from django.test import TestCase

from rest_framework.test import APIClient

from annotation import models


class test_tl_label(TestCase):
    """end point: /tl_label/"""

    def setUp(self):
        # Model
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0]
        )
        self.tl_label = models.TlLabels.objects.create(
            project=self.project, name="tltest"
        )

        self.client = APIClient()

    def test_create_post(self):
        r = self.client.post(
            "/api/tl_label/",
            {
                "name": "test",
                "project": self.project.id,
                "color_background": "#209cee",
                "color_text": "#ffffff"
            }
        )
        self.assertEqual(r.status_code, 201)

    def test_create_post_error(self):
        with self.subTest("1"):
            r = self.client.post(
                "/api/tl_label/",
                {
                    "name": "test",
                }
            )
            self.assertEqual(r.status_code, 400)

        with self.subTest("2"):
            r = self.client.post(
                "/api/tl_label/",
                {
                    "project": self.project.id,
                }
            )
            self.assertEqual(r.status_code, 400)

        with self.subTest("3"):
            r = self.client.post(
                "/api/tl_label/",
                body=""
            )
            self.assertEqual(r.status_code, 400)

    def test_get(self):
        r = self.client.get("/api/tl_label/{}/".format(self.tl_label.id))
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertEqual(payload["id"], self.project.id)
        self.assertEqual(payload["name"], self.tl_label.name)
        self.assertTrue("color_background" in payload)
        self.assertTrue("color_text" in payload)


class TestProject(TestCase):
    """end point: /project/N/ds_export"""

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
        #
        self.client = APIClient()

    def test_export(self):

        with self.subTest("error 1"):
            r = self.client.get(
                "/api/project/{}/ds_export/".format(self.project.id),
                {
                    "format": "json",
                    "exformat": "test"
                }
            )
            self.assertEqual(r.status_code, 400)

        r = self.client.get(
            "/api/project/{}/ds_export/".format(self.project.id),
            {
                # "format": "json",
                "exformat": "conllup"
            }
        )


class TestDocuments(TestCase):

    def setUp(self):
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0]
        )
        self.document = models.Documents.objects.create(
            project=self.project, file_name="0001"
        )

    def test_approved(self):
        r = self.client.post(
            "/api/document/{}/approved/".format(self.document.id),
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            "/api/document/{}/".format(self.document.id),
        )
        self.assertEqual(r.json()["approved"], True)

        r = self.client.post(
            "/api/document/{}/unapproved/".format(self.document.id),
        )
        self.assertEqual(r.status_code, 204)
        r = self.client.get(
            "/api/document/{}/".format(self.document.id),
        )
        self.assertEqual(r.json()["approved"], False)


        # print(r.request)
        # print(r)
        # print(r.status_code)
        # print(r.content)
        # print(r.json())
