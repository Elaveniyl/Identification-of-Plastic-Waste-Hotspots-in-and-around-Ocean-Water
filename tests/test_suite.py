"""
Comprehensive Test Suite for Modernized Plastic Waste Hotspot Prototype
Verifies Database, Routes, GIS Prioritisation, FLA Automaton, and Image Preprocessing.
"""

import io
import os
import base64
import unittest
from pathlib import Path
from PIL import Image

import main
from hotspot_service import hotspot_service, HotspotService
from observation_fsm import WasteObservationFSM, InvalidTransitionError
from prediction_service import prediction_service
from util import base64_to_pil, pil_to_jpeg_bytes


class TestPlasticWastePrototype(unittest.TestCase):

    def setUp(self):
        self.app = main.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    # =========================================================================
    # 1. Database and Web Route Tests
    # =========================================================================

    def test_web_routes_return_ok(self):
        """Verify all standard GET pages return HTTP 200 OK."""
        routes = [
            "/", "/mission", "/team", "/object", "/hotspot",
            "/contact", "/automata", "/visualizations", "/about"
        ]
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with {res.status_code}")

    def test_contact_form_sqlite_persistence(self):
        """Verify contact form stores entries in SQLite database."""
        test_payload = {
            "name": "Unit Tester",
            "email": "test@marine-hotspots.org",
            "phone": "+1-555-0199",
            "msg": "Automated verification test message."
        }
        res = self.client.post("/contact", data=test_payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            saved = main.Contact.query.filter_by(Email="test@marine-hotspots.org").first()
            self.assertIsNotNone(saved)
            self.assertEqual(saved.Name, "Unit Tester")
            self.assertEqual(saved.Phone, "+1-555-0199")

    # =========================================================================
    # 2. GIS Dataset and Hotspot Prioritisation Tests
    # =========================================================================

    def test_gis_dataset_integrity(self):
        """Verify full parsing of all 3,532 genuine oceanographic observations."""
        stats = hotspot_service.get_summary_stats()
        self.assertEqual(stats["total_observations"], 3532)
        self.assertEqual(stats["inside_gpgp_count"], 509)
        self.assertGreater(stats["critical_hotspots"], 0)
        self.assertAlmostEqual(stats["max_mass_concentration"], 43478.82, places=1)

    def test_gis_api_endpoints(self):
        """Verify GIS API outputs conform to JSON schema."""
        # Stats endpoint
        res = self.client.get("/api/hotspots/stats")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_observations", res.get_json())

        # List endpoint with filter
        res_crit = self.client.get("/api/hotspots?tier=Critical&limit=10")
        self.assertEqual(res_crit.status_code, 200)
        data = res_crit.get_json()
        self.assertGreaterEqual(data["count"], 1)
        for h in data["hotspots"]:
            self.assertIn("Critical", h["priority_tier"])
            self.assertGreaterEqual(h["priority_score"], 70.0)

        # Macro clusters endpoint
        res_clust = self.client.get("/api/hotspots/clusters?grid_size=5.0")
        self.assertEqual(res_clust.status_code, 200)
        clust_data = res_clust.get_json()
        self.assertGreater(clust_data["count"], 0)

    # =========================================================================
    # 3. FLA Automaton Tests (Formal Languages & Theory)
    # =========================================================================

    def test_fsm_valid_lifecycle(self):
        """Verify full acceptance path w in L(M) through DFA."""
        fsm = WasteObservationFSM()
        self.assertEqual(fsm.current_state, "DRAFT")
        self.assertFalse(fsm.is_accepted())

        # Step 1: DRAFT -> GEO_TAGGED
        self.assertEqual(fsm.transition("add_coords"), "GEO_TAGGED")

        # Step 2: GEO_TAGGED -> HOTSPOT_FLAGGED
        self.assertEqual(fsm.transition("flag_hotspot"), "HOTSPOT_FLAGGED")

        # Step 3: HOTSPOT_FLAGGED -> VERIFIED
        self.assertEqual(fsm.transition("operator_verify"), "VERIFIED")

        # Step 4: VERIFIED -> DISPATCHED
        self.assertEqual(fsm.transition("dispatch_cleanup"), "DISPATCHED")

        # Step 5: DISPATCHED -> ARCHIVED (Accepting state)
        self.assertEqual(fsm.transition("complete_archive"), "ARCHIVED")
        self.assertTrue(fsm.is_accepted())

    def test_fsm_invalid_transitions(self):
        """Verify undefined transitions delta(q, sigma) raise formal errors."""
        fsm = WasteObservationFSM()
        with self.assertRaises(InvalidTransitionError):
            fsm.transition("dispatch_cleanup")  # Cannot dispatch from DRAFT

        with self.assertRaises(InvalidTransitionError):
            fsm.transition("unknown_symbol")

    def test_fsm_api_transition(self):
        """Verify FSM HTTP endpoint executes state transitions."""
        res = self.client.post("/api/fsm/transition", json={
            "current_state": "DRAFT",
            "symbol": "add_coords"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["next_state"], "GEO_TAGGED")

    # =========================================================================
    # 4. Image Preprocessing and Prediction Endpoint Tests
    # =========================================================================

    def test_image_preprocessing_rgba_and_dimensions(self):
        """Verify RGBA images are converted to RGB and resized to 299x299."""
        # Create transparent RGBA image
        img = Image.new("RGBA", (120, 80), color=(255, 100, 50, 180))
        tensor = prediction_service.preprocess_image(img)
        self.assertEqual(tensor.shape, (1, 299, 299, 3))
        self.assertGreaterEqual(tensor.min(), -1.0)
        self.assertLessEqual(tensor.max(), 1.0)

    def test_predict_endpoint_valid_image(self):
        """Verify /predict processes valid image without 500 error."""
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(0, 200, 100)).save(buf, format="JPEG")
        b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

        res = self.client.post("/predict", json=b64)
        # Should return 200 if model executed, or 503 with exact diagnosis if unavailable
        self.assertIn(res.status_code, (200, 503))
        data = res.get_json()
        self.assertIn(data["status"], ("success", "unavailable"))
        if data["status"] == "unavailable":
            self.assertIn("Inference", data["result"])
            self.assertIn("labels", data)

    def test_predict_endpoint_invalid_payloads(self):
        """Verify corrupt data returns clean HTTP 400."""
        # Corrupt base64 string
        res = self.client.post("/predict", json="data:image/png;base64,not_real_image_bytes")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["status"], "error")

        # Empty body
        res_empty = self.client.post("/predict", json="")
        self.assertEqual(res_empty.status_code, 400)

    # =========================================================================
    # 5. Frontend Resource and DOM Integrity Tests
    # =========================================================================

    def test_object_page_frontend_and_assets(self):
        """Verify /object renders clean semantic HTML with zero broken local assets."""
        from html.parser import HTMLParser

        class TagCollector(HTMLParser):
            def __init__(self):
                super().__init__()
                self.local_assets = []
                self.ids = []
                self.headers = 0

            def handle_starttag(self, tag, attrs):
                attr_dict = dict(attrs)
                if "id" in attr_dict:
                    self.ids.append(attr_dict["id"])
                if tag == "header":
                    self.headers += 1
                for key in ("href", "src"):
                    if key in attr_dict and attr_dict[key].startswith("/static/"):
                        self.local_assets.append(attr_dict[key])

        res = self.client.get("/object")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")

        parser = TagCollector()
        parser.feed(html)

        # 1. Verify every local asset returns 200
        for asset in parser.local_assets:
            static_res = self.client.get(asset)
            self.assertEqual(
                static_res.status_code, 200,
                f"Asset {asset} failed to load (HTTP {static_res.status_code})"
            )

        # 2. Verify all required functional IDs are present
        required_ids = [
            "file-upload", "file-drag", "upload-caption",
            "image-box", "image-display", "pred-result",
            "loader", "timepass", "mainNav", "navbarResponsive"
        ]
        for elem_id in required_ids:
            self.assertIn(elem_id, parser.ids, f"Required element #{elem_id} missing")

        # 3. Verify no duplicate IDs exist
        duplicates = [x for x in parser.ids if parser.ids.count(x) > 1]
        self.assertEqual(len(duplicates), 0, f"Duplicate IDs detected: {set(duplicates)}")

        # 4. Verify single header structure
        self.assertEqual(parser.headers, 1, f"Expected 1 header, found {parser.headers}")


if __name__ == "__main__":
    unittest.main()
