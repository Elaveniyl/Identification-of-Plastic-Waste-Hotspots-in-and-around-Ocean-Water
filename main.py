"""
Main Application: AI-GIS Detection and Prioritisation of Plastic Waste Hotspots
Flask server integrating image classification, GIS hotspot prioritisation, and FLA lifecycle automata.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from util import base64_to_pil
from prediction_service import prediction_service
from hotspot_service import hotspot_service
from observation_fsm import WasteObservationFSM, InvalidTransitionError

PROJECT_ROOT = Path(__file__).parent.resolve()
CONFIG_FILE = PROJECT_ROOT / "config.json"

# Load database configuration safely
params = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as c:
            params = json.load(c).get("params", {})
    except Exception as e:
        print(f"[WARN] Failed to load config.json: {e}")

app = Flask(__name__)

# Configure Database URI with SQLite local fallback
db_uri = os.environ.get("DATABASE_URI") or params.get("db_uri") or f"sqlite:///{PROJECT_ROOT / 'contact.db'}"
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Contact(db.Model):
    """Contact feedback messages table."""
    __tablename__ = "contact"
    SNo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(80), nullable=False)
    Date = db.Column(db.DateTime, default=datetime.utcnow)
    Email = db.Column(db.String(80), nullable=False)
    Phone = db.Column(db.String(20), nullable=False)
    Message = db.Column(db.String(500), nullable=False)


# Initialize SQLite tables safely at startup
try:
    with app.app_context():
        db.create_all()
except Exception as e:
    print(f"[WARN] Database initialization notice: {e}")


# ============================================================================
# Frontend Web Routes
# ============================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    status_msg = None
    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            message = request.form.get("msg", "").strip()

            if name and email and message:
                entry = Contact(Name=name, Phone=phone, Message=message, Date=datetime.now(timezone.utc), Email=email)
                db.session.add(entry)
                db.session.commit()
                status_msg = "Thank you! Your message has been received."
            else:
                status_msg = "Please fill out all required fields."
        except Exception as e:
            db.session.rollback()
            status_msg = f"Notice: Message could not be recorded ({str(e)})"

    return render_template("contact.html", status_msg=status_msg)


@app.route("/mission")
def mission():
    return render_template("mission.html")


@app.route("/team")
def team():
    return render_template("team.html")


@app.route("/object")
def object():
    return render_template("hotspot1.html")


@app.route("/hotspot")
def hotspot():
    return render_template("hotspot.html")


@app.route("/automata")
def automata():
    return render_template("automata.html")


@app.route("/visualizations")
def visualizations():
    return render_template("visualizations.html")


@app.route("/about")
def about():
    return render_template("about.html")


# ============================================================================
# API Routes: Prediction, GIS Prioritisation, and FLA Automata
# ============================================================================

@app.route("/predict", methods=["GET", "POST"])
def predict():
    """
    Image prediction endpoint.
    Accepts base64 encoded image data, preprocesses for Inception v3 (299x299),
    and queries the singleton prediction service.
    """
    if request.method == "GET":
        return jsonify(prediction_service.get_status())

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify(error="No JSON payload received", status="error"), 400

    if isinstance(payload, dict):
        img_data = payload.get("image") or payload.get("data")
    else:
        img_data = payload

    if not img_data or not isinstance(img_data, str):
        return jsonify(error="Missing or invalid base64 image data", status="error"), 400

    try:
        pil_img = base64_to_pil(img_data)
    except ValueError as ve:
        return jsonify(error=str(ve), status="error"), 400
    except Exception as e:
        return jsonify(error=f"Image decoding failed: {str(e)}", status="error"), 400

    res = prediction_service.predict(pil_img)

    if res.get("status") == "success":
        return jsonify(
            result=res.get("result"),
            status="success",
            predictions=res.get("predictions")
        )
    elif res.get("status") == "unavailable":
        return jsonify(
            result="Inference Unavailable",
            status="unavailable",
            error=res.get("error"),
            detail=res.get("detail"),
            remediation=res.get("remediation"),
            expected_dimensions=res.get("expected_dimensions"),
            labels=res.get("labels")
        ), 503
    else:
        return jsonify(error=res.get("error", "Prediction failed"), status="error"), res.get("http_status", 400)


@app.route("/api/hotspots", methods=["GET"])
def api_hotspots():
    """Returns ranked GIS observations from Laurent Lebreton et al. (2018) dataset."""
    tier = request.args.get("tier")
    inside_gpgp_arg = request.args.get("inside_gpgp")
    inside_gpgp = int(inside_gpgp_arg) if inside_gpgp_arg in ("0", "1") else None
    limit = min(int(request.args.get("limit", 200)), 1000)

    hotspots = hotspot_service.get_hotspots(tier=tier, inside_gpgp=inside_gpgp, limit=limit)
    return jsonify(count=len(hotspots), hotspots=hotspots)


@app.route("/api/hotspots/stats", methods=["GET"])
def api_hotspot_stats():
    """Returns statistical distribution of the ocean plastic survey dataset."""
    return jsonify(hotspot_service.get_summary_stats())


@app.route("/api/hotspots/clusters", methods=["GET"])
def api_hotspot_clusters():
    """Returns spatial grid clusters (macro accumulation hotspots)."""
    grid_size = float(request.args.get("grid_size", 5.0))
    clusters = hotspot_service.get_spatial_clusters(grid_size=grid_size)
    return jsonify(count=len(clusters), grid_size_deg=grid_size, clusters=clusters)


@app.route("/api/fsm/spec", methods=["GET"])
def api_fsm_spec():
    """Returns the formal 5-tuple specification of the FLA observation automaton."""
    return jsonify(
        formal_specification={
            "states_Q": sorted(WasteObservationFSM.STATES),
            "alphabet_Sigma": sorted(WasteObservationFSM.ALPHABET),
            "start_state_q0": WasteObservationFSM.INITIAL_STATE,
            "accepting_states_F": sorted(WasteObservationFSM.ACCEPTING_STATES),
            "transition_rules_delta": [
                {"from_state": src, "input_symbol": sym, "to_state": dest}
                for (src, sym), dest in sorted(WasteObservationFSM.TRANSITIONS.items())
            ]
        }
    )


@app.route("/api/fsm/transition", methods=["POST"])
def api_fsm_transition():
    """Executes a formal DFA state transition."""
    data = request.get_json(silent=True) or {}
    current_state = data.get("current_state", "DRAFT")
    symbol = data.get("symbol")

    if not symbol:
        return jsonify(error="Missing required field 'symbol'", status="error"), 400

    try:
        fsm = WasteObservationFSM(initial_state=current_state)
        next_state = fsm.transition(symbol)
        return jsonify(
            status="success",
            previous_state=current_state,
            symbol=symbol,
            next_state=next_state,
            is_accepted=fsm.is_accepted(),
            valid_next_inputs=list(fsm.get_valid_transitions().keys())
        )
    except (ValueError, InvalidTransitionError) as e:
        return jsonify(
            status="error",
            error=str(e),
            current_state=current_state,
            symbol=symbol
        ), 400


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() in ("true", "1")
    print(f"Starting Plastic Waste Hotspot Server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
