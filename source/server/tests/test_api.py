from django.test import TestCase
from django.core.files.base import ContentFile

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from annotation import models


class test_tl_label(TestCase):
    """end point: /tl_label/"""

    def setUp(self):
        # Model
        self.user = User.objects.create_user(username='test', password='12345')
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0],
            owner=self.user
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
                "color_text": "#ffffff",
                "prefix_key": "",
                "suffix_key": "",
            }
        )
        self.assertEqual(r.status_code, 201)

    def test_create_post_add_shotcut(self):
        r = self.client.post(
            "/api/tl_label/",
            {
                "name": "test",
                "project": self.project.id,
                "color_background": "#209cee",
                "color_text": "#ffffff",
                "prefix_key": "",
                "suffix_key": "",
            }
        )
        self.assertEqual(len(r.json()["suffix_key"]), 1)
        self.assertEqual(r.json()["prefix_key"], "")
        self.assertEqual(r.status_code, 201)

        # double

        r = self.client.post(
            "/api/tl_label/",
            {
                "name": "test1",
                "project": self.project.id,
                "color_background": "#209cee",
                "color_text": "#ffffff",
                "prefix_key": "",
                "suffix_key": "",
            }
        )

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

        # print(payload)


class TestProject(TestCase):
    """end point: /project/N/ds_export"""

    def setUp(self):
        # Models
        self.user = User.objects.create_user(username='test', password='12345')
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0][0],
            owner=self.user
        )
        self.document = models.Documents.objects.create(
            project=self.project, file_name="0001"
        )
        self.document = models.Documents.objects.create(
            project=self.project, file_name="0002", approved=True
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
        # dc
        self.project_dc = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[1][0],
            owner=self.user
        )
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
    
    def test_import(self):
        with open("tests/data/1.conllup", "br") as f:
            body = f.read()

        with self.subTest("1"):
            r = self.client.put(
                "/api/project/{}/ds_import/".format(self.project.id),
                data={
                    "format": "conllup",
                    'files': [
                        ContentFile(content=body, name='file_1.conllup')
                    ]
                },
                format="multipart"
            )
            self.assertEqual(r.status_code, 204)
        
        with open("tests/data/3.zip", "br") as f:
            body = f.read()

        with self.subTest("2"):
            r = self.client.put(
                "/api/project/{}/ds_import/".format(self.project.id),
                data={
                    "format": "conllup",
                    'files': [
                        ContentFile(content=body, name='3.zip')
                    ]
                },
                format="multipart"
            )
            # print(r.content)
            self.assertEqual(r.status_code, 204)

    def test_list(self):
        """Список проектов пользователя"""
        user = User.objects.create_user(username='user1', password='12345')
        project = models.Projects.objects.create(
            name="lion42", description="", type=models.PROJECT_TYPE[0],
            owner=user
        )
        self.client.login(username='test', password='12345')

        with self.subTest("Default"):
            r = self.client.get(
                "/api/project/"
            )
            self.assertEqual(len(r.json()), 2)

        self.client.login(username='user1', password='12345')
        r = self.client.post(
            "/api/project/{}/permission/".format(project.id),
            {
                "username": self.user.username,
                "permission": "view"
            }
        )
        self.client.login(username='test', password='12345')

        with self.subTest("Access"):
            r = self.client.get(
                "/api/project/"
            )
            print(r.content)

    def test_documents_all_is_approved(self):
        r = self.client.get(
            "/api/project/{}/documents_all_is_approved/".format(
                self.project.id
            )
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 1)

    def test_permission_add(self):
        user = User.objects.create_user(username='user1', password='12345')
        self.client.login(username='test', password='12345')

        with self.subTest("Error username"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "user": "t",
                    "role": "view"
                }
            )
            print(r.json())
            self.assertEqual(r.status_code, 400)

        with self.subTest("Error role"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": "t",
                }
            )
            print(r.json())
            self.assertEqual(r.status_code, 400)

        with self.subTest("Error user not found"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": "t",
                    "role": "view"
                }
            )
            print(r.json())
            self.assertEqual(r.status_code, 400)

        with self.subTest("Error user owner"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": self.user.username,
                    "role": "view"
                }
            )
            print(r.json())
            self.assertEqual(r.status_code, 400)

        with self.subTest("Success"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": user.username,
                    "role": "view"
                }
            )
            self.assertEqual(r.status_code, 204)

            a = models.ProjectsPermission.objects.get(user=user)
            self.assertEqual(a.role, "view")

        with self.subTest("Success to change"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": user.username,
                    "role": "change"
                }
            )
            self.assertEqual(r.status_code, 204)

            a = models.ProjectsPermission.objects.get(user=user)
            self.assertEqual(a.role, "change")

        with self.subTest("Success to view"):
            r = self.client.post(
                "/api/project/{}/permission/".format(self.project.id),
                {
                    "username": user.username,
                    "role": "view"
                }
            )
            self.assertEqual(r.status_code, 204)

            a = models.ProjectsPermission.objects.get(user=user)
            self.assertEqual(a.role, "view")

    def test_permission_delete(self):
        user = User.objects.create_user(username='user1', password='12345')
        self.client.login(username='test', password='12345')

        self.client.post(
            "/api/project/{}/permission/".format(self.project.id),
            {
                "username": user.username,
                "role": "view"
            }
        )

        r = self.client.delete(
            "/api/project/{}/permission/".format(self.project.id),
            {
                "username": user.username,
            }
        )
        self.assertEqual(r.status_code, 204)

        self.assertRaises(
            models.ProjectsPermission.DoesNotExist,
            models.ProjectsPermission.objects.get,
            user=user
        )

    def test_permission_list(self):
        """Получить список прав"""
        user = User.objects.create_user(username='user1', password='12345')
        self.client.login(username='test', password='12345')

        with self.subTest("Null"):
            r = self.client.get(
                "/api/project/{}/permission/".format(self.project.id)
            )
            self.assertEqual(len(r.json()), 0)

        self.client.post(
            "/api/project/{}/permission/".format(self.project.id),
            {
                "username": user.username,
                "role": "view"
            }
        )

        with self.subTest("Exists"):
            r = self.client.get(
                "/api/project/{}/permission/".format(self.project.id)
            )
            self.assertEqual(len(r.json()), 1)


class TestDocuments(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test', password='12345')
        self.project = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[0],
            owner=self.user
        )
        self.document = models.Documents.objects.create(
            project=self.project, file_name="0001"
        )
        # dc
        self.project_dc = models.Projects.objects.create(
            name="lion", description="", type=models.PROJECT_TYPE[1][0],
            owner=self.user
        )
        self.document_dc = models.Documents.objects.create(
            project=self.project_dc, file_name="0002"
        )
        self.tl_label = models.TlLabels.objects.create(
            project=self.project_dc, name="tltest"
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

    def test_reset(self):
        r = self.client.post(
            "/api/document/{}/approved/".format(self.document.id),
        )
        self.assertEqual(r.status_code, 204)
    
    def test_label_set(self):
        r = self.client.post(
            "/api/document/{}/label_set/".format(self.document_dc.id),
            data={
                "label_id": self.tl_label.id,
                "value": 1
            },
        )
        self.assertEqual(r.status_code, 204)
        # check
        r = models.DCDocLabel.objects.get(
            label=self.tl_label, document=self.document_dc
        )
    
    def test_labels(self):
        with self.subTest("0"):
            r = self.client.get(
                "/api/document/{}/labels/".format(self.document_dc.id),
            )
            r = r.json()
            # [{'id': 1, 'name': 'tltest', 'value': 0}]
            # print(r)
            self.assertEqual(type(r), list)
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0]["value"], 0)
        
        with self.subTest("1"):
            r = self.client.post(
                "/api/document/{}/label_set/".format(self.document_dc.id),
                data={
                    "label_id": self.tl_label.id,
                    "value": 1
                },
            )
            r = self.client.get(
                "/api/document/{}/labels/".format(self.document_dc.id),
            )
            r = r.json()
            self.assertEqual(type(r), list)
            self.assertEqual(len(r), 1)
            self.assertEqual(r[0]["value"], 1)
        
        with self.subTest("unset"):
            r = self.client.post(
                "/api/document/{}/label_set/".format(self.document_dc.id),
                data={
                    "label_id": self.tl_label.id,
                    "value": 0
                },
            )
            r = self.client.get(
                "/api/document/{}/labels/".format(self.document_dc.id),
            )
            r = r.json()
            self.assertEqual(r[0]["value"], 0)
        