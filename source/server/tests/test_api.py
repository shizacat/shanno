from django.test import TestCase

from rest_framework.test import APIClient

from annotation import models


class test_tl_label(TestCase):
    """end point: tl_label"""

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


        # print(r)
        # print(r.status_code)
        # print(r.content)
        # print(r.json())
