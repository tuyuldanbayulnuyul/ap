import sys
import os

sys.path.insert(0, "/home/cloukfcd/interbank")
sys.path.insert(0, "/home/cloukfcd/virtualenv/interbank/3.9/lib/python3.9/site-packages")

from flask import Flask, request, redirect, jsonify, session
import json

BASE_DIR = "/home/cloukfcd/interbank"
app = Flask(__name__)
app.secret_key = "interbank-panel-secret-2024xZ"
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# === CUSTOM LOGIN - GANTI DI SINI ===
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
# =====================================


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def is_logged_in():
    return session.get("logged_in") == True


@app.route("/")
def index():
    if not is_logged_in():
        return redirect("login")
    config = load_config()
    options_html = ""
    for key in config.get("result_options", {}):
        sel = " selected" if config.get("result_mode") == key else ""
        options_html += '<option value="' + key + '"' + sel + '>' + key + '</option>'

    fields_html = ""
    for key, label in [("target_bank","Target Bank"),("beneficiary_name","Beneficiary"),("currency","Currency"),("country","Country"),("iban","IBAN"),("bank_server_code","Bank Code"),("account_type","Account Type")]:
        fields_html += '<div class="r"><label>' + label + ':</label><input name="' + key + '" value="' + str(config.get(key,"")) + '"></div>'

    fields_html += '<div class="r"><label>Balance:</label><input type="number" name="target_balance_eur" value="' + str(config.get("target_balance_eur", 49500000)) + '"></div>'

    timing_html = ""
    for key, val in config.get("timing", {}).items():
        timing_html += '<div class="r"><label>' + key + ':</label><input type="number" step="0.1" name="timing_' + key + '" value="' + str(val) + '"></div>'

    holders_html = ""
    for acc, name in config.get("account_holders", {}).items():
        holders_html += '<div class="r"><input name="holder_account[]" value="' + acc + '"><input name="holder_name[]" value="' + name + '"></div>'

    html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Interbank Panel</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Courier New',monospace;background:#0a0a0f;color:#00ff88;padding:20px}.c{max-width:900px;margin:0 auto}h1{text-align:center;color:#00ccff;border:1px solid #00ccff33;padding:15px;margin-bottom:25px;background:#00ccff08;letter-spacing:2px}.s{border:1px solid #1a3a2a;margin-bottom:20px;padding:20px;background:#0d1117;border-radius:4px}.s h2{color:#00ccff;font-size:.95em;margin-bottom:15px;border-bottom:1px solid #1a3a2a;padding-bottom:8px;letter-spacing:1px}.r{display:flex;align-items:center;margin-bottom:12px;gap:10px}.r label{min-width:160px;color:#88aaaa;font-size:.85em}.r input,.r select{flex:1;background:#0a0a0f;border:1px solid #1a3a2a;color:#00ff88;padding:8px 12px;font-family:monospace;font-size:.85em;border-radius:3px}.r input:focus,.r select:focus{outline:none;border-color:#00ccff;box-shadow:0 0 5px #00ccff33}select option{background:#0d1117;color:#00ff88}.btn{display:block;width:100%;padding:15px;background:#00ff8822;border:1px solid #00ff88;color:#00ff88;font-family:monospace;font-size:1em;cursor:pointer;border-radius:4px;margin-top:20px;letter-spacing:2px}.btn:hover{background:#00ff8844;box-shadow:0 0 15px #00ff8833}.preview{background:#1a0a0a;border:1px solid #ff444444;padding:12px;margin-top:10px;color:#ff6666;font-size:.85em;border-radius:3px}.logout{position:fixed;top:15px;right:20px;color:#ff4444;text-decoration:none;font-size:.85em;border:1px solid #ff4444;padding:5px 12px;border-radius:3px}.logout:hover{background:#ff444422}</style></head>
<body><a href="logout" class="logout">LOGOUT</a><div class="c"><h1>[ INTERBANK ] - CONTROL PANEL</h1>
<form method="POST" action="save">
<div class="s"><h2>// RESULT OUTPUT (Tampil di App Desktop)</h2>
<div class="r"><label>Result Mode:</label><select name="result_mode">''' + options_html + '''</select></div>
<div class="r"><label>Custom Message:</label><input name="custom_message" value="''' + str(config.get('custom_message','')) + '''"></div>
<div class="preview">Active: ''' + str(config.get("result_options", {}).get(config.get("result_mode",""), "")) + '''</div></div>
<div class="s"><h2>// TARGET ACCOUNT INFO</h2>''' + fields_html + '''</div>
<div class="s"><h2>// ACCOUNT HOLDERS</h2>''' + holders_html + '''</div>
<div class="s"><h2>// TIMING (detik)</h2>''' + timing_html + '''</div>
<button type="submit" class="btn">[ SAVE CONFIGURATION ]</button></form></div></body></html>'''

    return html


@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = ""
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")
        if user == ADMIN_USER and pw == ADMIN_PASS:
            session["logged_in"] = True
            return redirect(".")
        else:
            error_msg = "Invalid credentials. Access denied."

    err_html = ""
    if error_msg:
        err_html = '<div style="color:#ff4444;border:1px solid #ff4444;padding:10px;margin-bottom:15px;border-radius:3px;text-align:center">' + error_msg + '</div>'

    return '''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login - Interbank</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Courier New',monospace;background:#0a0a0f;color:#00ff88;display:flex;justify-content:center;align-items:center;min-height:100vh}.box{width:400px;border:1px solid #1a3a2a;padding:40px;background:#0d1117;border-radius:8px}h1{text-align:center;color:#00ccff;font-size:1.1em;margin-bottom:25px;letter-spacing:2px}input{width:100%;background:#0a0a0f;border:1px solid #1a3a2a;color:#00ff88;padding:12px;font-family:monospace;margin-bottom:15px;border-radius:3px;font-size:.9em}input:focus{outline:none;border-color:#00ccff;box-shadow:0 0 5px #00ccff33}button{width:100%;padding:12px;background:#00ff8822;border:1px solid #00ff88;color:#00ff88;font-family:monospace;font-size:1em;cursor:pointer;border-radius:4px;letter-spacing:2px}button:hover{background:#00ff8844}.sub{text-align:center;color:#444;font-size:.75em;margin-top:15px}</style></head>
<body><div class="box"><h1>[ INTERBANK ] - LOGIN</h1>''' + err_html + '''<form method="POST" action="login">
<input type="text" name="username" placeholder="Username" autocomplete="off">
<input type="password" name="password" placeholder="Password">
<button type="submit">[ ACCESS PANEL ]</button></form>
<p class="sub">Authorized personnel only.</p></div></body></html>'''


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("login")


@app.route("/save", methods=["POST"])
def save():
    if not is_logged_in():
        return redirect("login")
    config = load_config()
    config["result_mode"] = request.form.get("result_mode", "SETTLEMENT_LIMIT")
    config["custom_message"] = request.form.get("custom_message", "")
    config["target_bank"] = request.form.get("target_bank", "UBS")
    config["beneficiary_name"] = request.form.get("beneficiary_name", "JOHN DOE")
    config["currency"] = request.form.get("currency", "EUR")
    config["country"] = request.form.get("country", "SWITZERLAND")
    config["iban"] = request.form.get("iban", "")
    config["bank_server_code"] = request.form.get("bank_server_code", "")
    config["account_type"] = request.form.get("account_type", "CORPORATE PREMIUM")
    try:
        config["target_balance_eur"] = int(request.form.get("target_balance_eur", 49500000))
    except ValueError:
        config["target_balance_eur"] = 49500000
    for field in ["boot_progress","auth_connect","auth_verify","auth_2fa","auth_session_key","net_hop_duration","net_tunnel_progress","scan_probe_duration","scan_batch_duration","routing_validate","routing_aml","routing_correspondent","bridge_sync_progress","settlement_duration"]:
        val = request.form.get("timing_" + field)
        if val:
            try:
                config["timing"][field] = float(val)
            except ValueError:
                pass
    holder_keys = request.form.getlist("holder_account[]")
    holder_names = request.form.getlist("holder_name[]")
    config["account_holders"] = {}
    for acc, name in zip(holder_keys, holder_names):
        if acc.strip() and name.strip():
            config["account_holders"][acc.strip()] = name.strip()
    save_config(config)
    return redirect(".")


@app.route("/api/config")
def api_config():
    return jsonify(load_config())


application = app
