"""
ResQ.AI Backend Test Suite
Tests all API endpoints and core logic functions without requiring
transformers/torch installed (those require heavy downloads on first run).
"""
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

# ─── Mock heavy dependencies before importing app ───────────────────────────
sys.modules['transformers'] = MagicMock()
mock_pipeline = MagicMock(return_value=lambda text: [{'label': 'NEGATIVE', 'score': 0.92}])
sys.modules['transformers'].pipeline = mock_pipeline

mock_genai = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai

# Now import the app
import os
os.environ['GEMINI_API_KEY'] = ''  # disable Gemini for tests

from app import app, classify_by_keywords, detect_severity, get_offline_guidance


class TestKeywordClassifier(unittest.TestCase):
    """Test the keyword-based emergency classification logic."""

    def test_medical_keywords(self):
        em_type, conf = classify_by_keywords("I am bleeding heavily from my wound")
        self.assertEqual(em_type, "Medical")
        self.assertGreater(conf, 0.6)

    def test_fire_keywords(self):
        em_type, conf = classify_by_keywords("There is a fire and smoke everywhere")
        self.assertEqual(em_type, "Fire")
        self.assertGreater(conf, 0.6)

    def test_crime_keywords(self):
        em_type, conf = classify_by_keywords("A robbery is happening at the shop")
        self.assertEqual(em_type, "Crime")
        self.assertGreater(conf, 0.6)

    def test_accident_keywords(self):
        em_type, conf = classify_by_keywords("There was a car crash on the highway")
        self.assertEqual(em_type, "Accident")
        self.assertGreater(conf, 0.6)

    def test_disaster_keywords(self):
        em_type, conf = classify_by_keywords("Earthquake just hit the city, tsunami warning issued")
        self.assertEqual(em_type, "Disaster")
        self.assertGreater(conf, 0.6)

    def test_women_safety_keywords(self):
        em_type, conf = classify_by_keywords("A women is being harassed and abused")
        self.assertEqual(em_type, "Women Safety")
        self.assertGreater(conf, 0.6)

    def test_child_emergency_keywords(self):
        em_type, conf = classify_by_keywords("A child is missing and we cannot find the baby")
        self.assertEqual(em_type, "Child Emergency")
        self.assertGreater(conf, 0.6)

    def test_unknown_input_returns_none(self):
        em_type, conf = classify_by_keywords("The weather is very nice today")
        self.assertIsNone(em_type)
        self.assertEqual(conf, 0.0)

    def test_empty_input_returns_none(self):
        em_type, conf = classify_by_keywords("")
        self.assertIsNone(em_type)


class TestSeverityDetection(unittest.TestCase):
    """Test severity classification logic."""

    def test_critical_words(self):
        sev = detect_severity("patient is unconscious and not breathing", 0.80)
        self.assertEqual(sev, "Critical")

    def test_high_confidence_is_critical(self):
        sev = detect_severity("some text", 0.95)
        self.assertEqual(sev, "Critical")

    def test_high_keywords(self):
        sev = detect_severity("urgent help needed immediately", 0.70)
        self.assertEqual(sev, "High")

    def test_high_confidence_is_high(self):
        sev = detect_severity("accident on road", 0.78)
        self.assertEqual(sev, "High")

    def test_medium_confidence(self):
        sev = detect_severity("someone is hurt", 0.65)
        self.assertEqual(sev, "Medium")

    def test_low_confidence(self):
        sev = detect_severity("maybe there is a problem", 0.40)
        self.assertEqual(sev, "Low")


class TestOfflineGuidance(unittest.TestCase):
    """Test offline guidance fallbacks."""

    def test_all_emergency_types_have_guidance(self):
        types = ['Medical', 'Fire', 'Crime', 'Accident', 'Disaster', 'Women Safety', 'Child Emergency']
        for t in types:
            guidance = get_offline_guidance(t)
            self.assertIsInstance(guidance, str)
            self.assertGreater(len(guidance), 50, f"Guidance too short for {t}")
            self.assertIn("112", guidance, f"Guidance for {t} should mention 112")

    def test_unknown_type_falls_back_to_medical(self):
        guidance = get_offline_guidance("Unknown Type")
        self.assertIsNotNone(guidance)
        self.assertIn("112", guidance)


class TestAPIEndpoints(unittest.TestCase):
    """Test Flask API endpoints."""

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

    # ── /api/health ──────────────────────────────────────────────────────────
    def test_health_endpoint_returns_200(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)

    def test_health_endpoint_returns_json(self):
        resp = self.client.get('/api/health')
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('version', data)
        self.assertIn('gemini', data)

    # ── /api/classify ─────────────────────────────────────────────────────────
    def test_classify_medical_emergency(self):
        resp = self.client.post('/api/classify',
            json={'text': 'Someone is having a heart attack and bleeding badly', 'location': None})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('emergencyType', data)
        self.assertIn('confidence', data)
        self.assertIn('severity', data)
        self.assertIn('guidance', data)
        self.assertIn('locationReceived', data)
        self.assertEqual(data['locationReceived'], False)
        self.assertEqual(data['emergencyType'], 'Medical')

    def test_classify_fire_emergency(self):
        resp = self.client.post('/api/classify',
            json={'text': 'Fire and smoke is everywhere, building is burning'})
        data = json.loads(resp.data)
        self.assertEqual(data['emergencyType'], 'Fire')
        self.assertGreaterEqual(data['confidence'], 60.0)

    def test_classify_with_location(self):
        resp = self.client.post('/api/classify',
            json={'text': 'I need help', 'location': {'lat': 28.6139, 'lon': 77.2090}})
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(data['locationReceived'])

    def test_classify_empty_text_returns_400(self):
        resp = self.client.post('/api/classify', json={'text': ''})
        self.assertEqual(resp.status_code, 400)

    def test_classify_whitespace_text_returns_400(self):
        resp = self.client.post('/api/classify', json={'text': '   '})
        self.assertEqual(resp.status_code, 400)

    def test_classify_missing_text_returns_400(self):
        resp = self.client.post('/api/classify', json={})
        self.assertEqual(resp.status_code, 400)

    def test_classify_too_long_text_returns_400(self):
        resp = self.client.post('/api/classify', json={'text': 'a' * 2001})
        self.assertEqual(resp.status_code, 400)

    def test_classify_invalid_json_returns_400(self):
        resp = self.client.post('/api/classify',
            data='not json', content_type='text/plain')
        self.assertEqual(resp.status_code, 400)

    def test_classify_crime_emergency(self):
        resp = self.client.post('/api/classify',
            json={'text': 'robbery and theft happening right now, police needed'})
        data = json.loads(resp.data)
        self.assertEqual(data['emergencyType'], 'Crime')

    def test_classify_accident_emergency(self):
        resp = self.client.post('/api/classify',
            json={'text': 'car crash and accident on main road highway'})
        data = json.loads(resp.data)
        self.assertEqual(data['emergencyType'], 'Accident')

    def test_classify_disaster_emergency(self):
        resp = self.client.post('/api/classify',
            json={'text': 'earthquake flood disaster happening now people trapped'})
        data = json.loads(resp.data)
        self.assertEqual(data['emergencyType'], 'Disaster')

    def test_classify_severity_field_present(self):
        resp = self.client.post('/api/classify',
            json={'text': 'critically injured patient unconscious not breathing'})
        data = json.loads(resp.data)
        self.assertIn(data['severity'], ['Critical', 'High', 'Medium', 'Low'])

    def test_classify_confidence_is_percentage(self):
        resp = self.client.post('/api/classify',
            json={'text': 'Someone is bleeding and needs medical help urgently'})
        data = json.loads(resp.data)
        self.assertGreaterEqual(data['confidence'], 0)
        self.assertLessEqual(data['confidence'], 100)

    # ── /api/sos ─────────────────────────────────────────────────────────────
    def test_sos_endpoint_returns_200(self):
        resp = self.client.post('/api/sos',
            json={'location': {'lat': 28.6139, 'lon': 77.2090},
                  'profile': {'bloodGroup': 'O+', 'name': 'Test User'}})
        self.assertEqual(resp.status_code, 200)

    def test_sos_endpoint_returns_received_status(self):
        resp = self.client.post('/api/sos', json={})
        data = json.loads(resp.data)
        self.assertEqual(data['status'], 'received')

    def test_sos_endpoint_with_empty_body(self):
        resp = self.client.post('/api/sos',
            data='', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

    # ── CORS headers ─────────────────────────────────────────────────────────
    def test_cors_header_on_classify(self):
        resp = self.client.post('/api/classify',
            json={'text': 'test emergency'},
            headers={'Origin': 'http://localhost:3000'})
        self.assertIn('Access-Control-Allow-Origin', resp.headers)

    def test_options_preflight(self):
        resp = self.client.options('/api/classify',
            headers={'Origin': 'http://localhost:3000',
                     'Access-Control-Request-Method': 'POST'})
        self.assertIn(resp.status_code, [200, 204])


class TestAPIResponseStructure(unittest.TestCase):
    """Test that API responses have correct structure and types."""

    def setUp(self):
        self.client = app.test_client()

    def test_classify_response_has_all_required_fields(self):
        resp = self.client.post('/api/classify',
            json={'text': 'Someone is seriously hurt, please help'})
        data = json.loads(resp.data)
        required = ['emergencyType', 'confidence', 'severity', 'locationReceived', 'guidance']
        for field in required:
            self.assertIn(field, data, f"Missing field: {field}")

    def test_emergency_type_is_valid_category(self):
        valid = ['Medical', 'Fire', 'Crime', 'Accident', 'Disaster',
                 'Women Safety', 'Child Emergency', 'General Distress']
        resp = self.client.post('/api/classify',
            json={'text': 'I need help urgently'})
        data = json.loads(resp.data)
        self.assertIn(data['emergencyType'], valid)

    def test_guidance_is_non_empty_string(self):
        resp = self.client.post('/api/classify',
            json={'text': 'Medical emergency, someone collapsed'})
        data = json.loads(resp.data)
        self.assertIsInstance(data['guidance'], str)
        self.assertGreater(len(data['guidance']), 20)

    def test_confidence_is_number(self):
        resp = self.client.post('/api/classify',
            json={'text': 'fire in the building'})
        data = json.loads(resp.data)
        self.assertIsInstance(data['confidence'], (int, float))


if __name__ == '__main__':
    print("=" * 60)
    print("  ResQ.AI Backend Test Suite")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestKeywordClassifier,
        TestSeverityDetection,
        TestOfflineGuidance,
        TestAPIEndpoints,
        TestAPIResponseStructure,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed}/{total} tests passed")
    if result.failures:
        print(f"  FAILURES: {len(result.failures)}")
    if result.errors:
        print(f"  ERRORS:   {len(result.errors)}")
    print("=" * 60)
    sys.exit(0 if result.wasSuccessful() else 1)
