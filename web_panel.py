#!/usr/bin/env python3
"""
Web Panel — Interbank Settlement Configuration
Akses via browser untuk setting hasil akhir yang tampil di app desktop.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import json
import os

app = Flask(__name__)
app.secret_key = "interbank-panel-secret-key"

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


@app.route("/")
def index():
    config = load_config()
    return render_template("index.html", config=config)


@app.route("/save", methods=["POST"])
def save():
    config = load_config()

    # Update result mode
    config["result_mode"] = request.form.get("result_mode", "SETTLEMENT_LIMIT")
    config["custom_message"] = request.form.get("custom_message", "")

    # Update target info
    config["target_bank"] = request.form.get("target_bank", "UBS")
    config["beneficiary_name"] = request.form.get("beneficiary_name", "JOHN DOE")
    config["currency"] = request.form.get("currency", "EUR")
    config["country"] = request.form.get("country", "SWITZERLAND")
    config["iban"] = request.form.get("iban", "")
    config["bank_server_code"] = request.form.get("bank_server_code", "")
    config["account_type"] = request.form.get("account_type", "CORPORATE PREMIUM")

    # Update balance
    try:
        config["target_balance_eur"] = int(request.form.get("target_balance_eur", 49500000))
    except ValueError:
        config["target_balance_eur"] = 49500000

    # Update timing
    timing_fields = [
        "boot_progress", "auth_connect", "auth_verify", "auth_2fa",
        "auth_session_key", "net_hop_duration", "net_tunnel_progress",
        "scan_probe_duration", "scan_batch_duration", "routing_validate",
        "routing_aml", "routing_correspondent", "bridge_sync_progress",
        "settlement_duration"
    ]
    for field in timing_fields:
        val = request.form.get(f"timing_{field}")
        if val:
            try:
                config["timing"][field] = float(val)
            except ValueError:
                pass

    # Update account holders
    holder_keys = request.form.getlist("holder_account[]")
    holder_names = request.form.getlist("holder_name[]")
    config["account_holders"] = {}
    for acc, name in zip(holder_keys, holder_names):
        if acc.strip() and name.strip():
            config["account_holders"][acc.strip()] = name.strip()

    save_config(config)
    flash("Configuration saved! App desktop akan otomatis sync.", "success")
    return redirect(url_for("index"))


@app.route("/api/config")
def api_config():
    """API endpoint untuk app desktop fetch config."""
    return jsonify(load_config())


if __name__ == "__main__":
    print("\n  [WEB PANEL] Running on http://127.0.0.1:5000")
    print("  Open browser to configure the desktop app.\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
