import yaml

from django.test import SimpleTestCase, override_settings


@override_settings(ALLOWED_HOSTS=['localhost'])
class SwaggerDocumentationTests(SimpleTestCase):
    def test_swagger_ui_loads(self):
        response = self.client.get('/api/docs/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SwaggerUIBundle')

    def test_schema_documents_api_operations_and_request_bodies(self):
        response = self.client.get('/api/schema/', HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        schema = yaml.safe_load(response.content)
        post_paths = {
            '/api/check-group/',
            '/api/check-post/',
            '/api/generate-comment/',
            '/api/incoming-message/',
            '/api/process-notification/',
            '/api/save-group/',
            '/api/update-status/',
        }
        self.assertTrue(post_paths.issubset(schema['paths']))
        for path in post_paths:
            self.assertIn('requestBody', schema['paths'][path]['post'])
        self.assertIn('get', schema['paths']['/api/get-welcome/'])
