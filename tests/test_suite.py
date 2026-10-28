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
        """Verify all active standard GET pages return HTTP 200 OK, and removed routes redirect."""
        routes = [
            "/", "/mission", "/team", "/object", "/hotspot",
            "/automata", "/visualizations"
        ]
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with {res.status_code}")

        for r in ["/about", "/contact"]:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 302, f"Route {r} should redirect (302)")

    def test_contact_form_route_redirect_and_db_model(self):
        """Verify /contact route redirects safely and Contact model persists."""
        res = self.client.post("/contact", data={"name": "test"}, follow_redirects=False)
        self.assertEqual(res.status_code, 302)

        with self.app.app_context():
            entry = main.Contact(
                Name="Unit Tester",
                Email="test@marine-hotspots.org",
                Phone="+1-555-0199",
                Message="Automated verification test message."
            )
            main.db.session.add(entry)
            main.db.session.commit()
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

    # =========================================================================
    # 6. Advanced Formal Languages and Automata (FLA) Tests
    # =========================================================================

    def test_fsm_formal_specification(self):
        """Verify dynamic generation of formal 5-tuple M = (Q, Sigma, delta, q0, F)."""
        spec = WasteObservationFSM.get_formal_definition()
        self.assertEqual(len(spec["states"]), 8)
        self.assertEqual(len(spec["alphabet"]), 7)
        self.assertEqual(spec["initial_state"], "DRAFT")
        self.assertEqual(set(spec["accepting_states"]), {"ARCHIVED", "REJECTED"})
        self.assertEqual(len(spec["transitions"]), 18)
        self.assertFalse(spec["is_total"])

        # Check /api/fsm/spec route
        res = self.client.get("/api/fsm/spec")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["initial_state"], "DRAFT")

    def test_fsm_completed_dfa_with_trap(self):
        """Verify total transition function delta_complete with explicit TRAP state."""
        comp = WasteObservationFSM.get_completed_dfa()
        self.assertEqual(len(comp["states"]), 9)  # 8 original + TRAP
        self.assertIn("TRAP", comp["states"])
        self.assertTrue(comp["is_total"])

        # Total transitions must be exactly |Q_complete| * |Sigma| = 9 * 7 = 63
        self.assertEqual(len(comp["transitions"]), 63)

        # Verify TRAP self-loops on all symbols
        trap_transitions = [t for t in comp["transitions"] if t["from"] == "TRAP"]
        self.assertEqual(len(trap_transitions), 7)
        for t in trap_transitions:
            self.assertEqual(t["to"], "TRAP")

        # Test route with completed=true
        res = self.client.get("/api/fsm/spec?completed=true")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["is_total"])

    def test_fsm_accepts_word_logic(self):
        """Verify language acceptance, state paths, and rejection failure positions."""
        # Accepted word 1 (happy path cleanup):
        word_valid = ["add_coords", "classify_image", "operator_verify", "dispatch_cleanup", "complete_archive"]
        res_valid = WasteObservationFSM.accepts_word(word_valid)
        self.assertTrue(res_valid["accepted"])
        self.assertEqual(res_valid["final_state"], "ARCHIVED")
        self.assertIsNone(res_valid["failing_position"])
        self.assertEqual(
            res_valid["state_path"],
            ["DRAFT", "GEO_TAGGED", "HOTSPOT_FLAGGED", "VERIFIED", "DISPATCHED", "ARCHIVED"]
        )

        # Accepted word 2 (immediate rejection from DRAFT):
        res_reject = WasteObservationFSM.accepts_word(["invalidate"])
        self.assertTrue(res_reject["accepted"])
        self.assertEqual(res_reject["final_state"], "REJECTED")

        # Rejected word (undefined transition routing to TRAP):
        word_invalid = ["add_coords", "dispatch_cleanup"]
        res_invalid = WasteObservationFSM.accepts_word(word_invalid)
        self.assertFalse(res_invalid["accepted"])
        self.assertEqual(res_invalid["final_state"], "TRAP")
        self.assertEqual(res_invalid["failing_position"], 1)
        self.assertEqual(res_invalid["failing_symbol"], "dispatch_cleanup")

        # Rejected word (symbol not in Sigma):
        word_bad_sym = ["add_coords", "teleport"]
        res_bad_sym = WasteObservationFSM.accepts_word(word_bad_sym)
        self.assertFalse(res_bad_sym["accepted"])
        self.assertEqual(res_bad_sym["failing_position"], 1)

    def test_fsm_api_accepts_endpoint(self):
        """Verify POST /api/fsm/accepts endpoint behavior."""
        # Valid word
        res = self.client.post("/api/fsm/accepts", json={
            "symbols": ["classify_image", "operator_verify", "complete_archive"]
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["accepted"])
        self.assertEqual(data["status"], "success")

        # Invalid word
        res_rej = self.client.post("/api/fsm/accepts", json={
            "word": "add_coords, complete_archive"
        })
        self.assertEqual(res_rej.status_code, 200)
        data_rej = res_rej.get_json()
        self.assertFalse(data_rej["accepted"])
        self.assertEqual(data_rej["status"], "rejected")

        # Missing payload
        res_empty = self.client.post("/api/fsm/accepts", json={})
        self.assertEqual(res_empty.status_code, 400)

    def test_data_url_regular_language_cases(self):
        """Verify the 5 accepted and 5 rejected RFC 2397 Data URL strings documented in util.py."""
        from util import DATA_URL_REGEX

        accepted_cases = [
            "data:image/png;base64,",
            "data:image/jpeg;base64,",
            "data:image/svg+xml;base64,",
            "data:image/webp;base64,",
            "data:image/vnd.microsoft.icon;base64,"
        ]
        for s in accepted_cases:
            self.assertIsNotNone(
                DATA_URL_REGEX.match(s),
                f"Accepted case failed to match regex: {s}"
            )

        rejected_cases = [
            "data:text/plain;base64,",
            "data:image/png;charset=utf-8,",
            "http://example.com/ocean.jpg",
            "data:image/;base64,",
            "image/png;base64,"
        ]
        for s in rejected_cases:
            self.assertIsNone(
                DATA_URL_REGEX.match(s),
                f"Rejected case erroneously matched regex: {s}"
            )

    def test_predict_endpoint_real_inference(self):
        """Verify /predict returns live HTTP 200 with all 6 classification classes."""
        img = Image.open("static/img/ocean.jpg")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

        res = self.client.post("/predict", json=b64)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("plastic", data["result"])
        self.assertIn("predictions", data)
        expected_classes = {"paper", "metal", "cardboard", "trash", "glass", "plastic"}
        self.assertEqual(set(data["predictions"].keys()), expected_classes)


if __name__ == "__main__":
    unittest.main()

