#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTERBANK SETTLEMENT TERMINAL — GUI v3.0
Desktop Application with CustomTkinter
Reads config from config.json (synced with web panel)
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
import hashlib
import datetime
import string
import json
import os
import sys

# =====================================================================
# [ CONFIG LOADER ]
# =====================================================================
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    """Load config from JSON file (synced with web panel)."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "result_mode": "SETTLEMENT_LIMIT",
            "result_options": {"SETTLEMENT_LIMIT": "DECLINED — Settlement limit exceeded."},
            "custom_message": "DECLINED BY EXCHANGE",
            "target_bank": "UBS", "target_balance_eur": 49500000,
            "beneficiary_name": "JOHN DOE", "currency": "EUR",
            "timing": {"settlement_duration": 30},
            "account_holders": {}
        }



# =====================================================================
# [ UTILITY ]
# =====================================================================
def ts():
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

def datestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def gen_ref(prefix="TRN"):
    return f"{prefix}-{random.randint(10000,99999)}-{random.choice(string.ascii_uppercase)}{random.randint(10,99)}{random.choice(string.ascii_uppercase)}"

def gen_session_id():
    seed = f"{time.time()}{random.randint(0,99999)}"
    return hashlib.sha256(seed.encode()).hexdigest()[:20].upper()

BANK_REGISTRY = [
    ("UBS", "UBSWCHZH", "CH"), ("CHASE", "CHASUS33", "US"),
    ("CITI", "CITIUS33", "US"), ("BARCLAYS", "BARCGB22", "GB"),
    ("DBS", "DBSSSGSG", "SG"), ("MUFG", "BOTKJPJT", "JP"),
    ("SANTANDER", "BSCHESMM", "ES"), ("ING", "INGBNL2A", "NL"),
    ("DEUTSCHE", "DEUTDEFF", "DE"), ("HSBC", "HSBCGB2L", "GB"),
    ("WELLS FARGO", "WFBIUS6S", "US"), ("BNP PARIBAS", "BNPAFRPP", "FR"),
    ("GOLDMAN SACHS", "GOLDUS33", "US"), ("COMMERZBANK", "COBADEFF", "DE"),
    ("ANZ", "ANZBAU3M", "AU"), ("WESTPAC", "WPACAU2S", "AU"),
]

TXN_TYPES = ["WIRE", "MT202", "MT940", "SEPA-CT", "TARGET2", "CHAPS", "FEDWIRE"]
TXN_STATUS = ["PENDING", "CLEARED", "SETTLING", "IN-TRANSIT", "QUEUED"]
CRYPTO_RATES = {"BTC": 68500.00, "ETH": 3850.00, "USDT": 1.00}



# =====================================================================
# [ MAIN APP CLASS ]
# =====================================================================
class InterbankApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("INTERBANK SETTLEMENT TERMINAL v3.0")
        self.geometry("1000x700")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Load config
        self.config = load_config()
        self.running = False
        self.current_phase = 0

        # Build UI
        self._build_ui()

    def _build_ui(self):
        """Build the main UI layout."""
        # Top banner
        self.banner = ctk.CTkFrame(self, height=60, fg_color="#0a1628")
        self.banner.pack(fill="x", padx=0, pady=0)
        self.banner.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.banner,
            text="[ INTERBANK SETTLEMENT TERMINAL ]",
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold"),
            text_color="#00ccff"
        )
        self.title_label.pack(pady=15)


        # Main content area: left panel (terminal) + right panel (controls)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # LEFT: Terminal output
        self.terminal_frame = ctk.CTkFrame(self.main_frame, fg_color="#0a0a0f",
                                            corner_radius=8, border_width=1,
                                            border_color="#1a3a2a")
        self.terminal_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.terminal = ctk.CTkTextbox(
            self.terminal_frame,
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#0a0a0f", text_color="#00ff88",
            corner_radius=0, wrap="word",
            state="disabled"
        )
        self.terminal.pack(fill="both", expand=True, padx=5, pady=5)


        # RIGHT: Control panel
        self.control_frame = ctk.CTkFrame(self.main_frame, fg_color="#0d1117",
                                           corner_radius=8, border_width=1,
                                           border_color="#1a3a2a", width=280)
        self.control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.control_frame.grid_propagate(False)

        ctrl_title = ctk.CTkLabel(self.control_frame, text="CONTROL PANEL",
                                   font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
                                   text_color="#00ccff")
        ctrl_title.pack(pady=(15, 10))

        # --- Input fields ---
        self._make_label("Nominal (EUR):")
        self.input_nominal = ctk.CTkEntry(self.control_frame,
                                           placeholder_text="49500000",
                                           font=ctk.CTkFont(family="Courier New", size=11),
                                           fg_color="#0a0a0f", text_color="#00ff88",
                                           border_color="#1a3a2a")
        self.input_nominal.pack(fill="x", padx=15, pady=(0, 8))

        self._make_label("Destination Bank:")
        self.input_bank = ctk.CTkEntry(self.control_frame,
                                        placeholder_text="BANK MANDIRI",
                                        font=ctk.CTkFont(family="Courier New", size=11),
                                        fg_color="#0a0a0f", text_color="#00ff88",
                                        border_color="#1a3a2a")
        self.input_bank.pack(fill="x", padx=15, pady=(0, 8))

        self._make_label("Account Number:")
        self.input_account = ctk.CTkEntry(self.control_frame,
                                           placeholder_text="1234567890",
                                           font=ctk.CTkFont(family="Courier New", size=11),
                                           fg_color="#0a0a0f", text_color="#00ff88",
                                           border_color="#1a3a2a")
        self.input_account.pack(fill="x", padx=15, pady=(0, 8))


        self._make_label("Wallet Address:")
        self.input_wallet = ctk.CTkEntry(self.control_frame,
                                          placeholder_text="0x...",
                                          font=ctk.CTkFont(family="Courier New", size=11),
                                          fg_color="#0a0a0f", text_color="#00ff88",
                                          border_color="#1a3a2a")
        self.input_wallet.pack(fill="x", padx=15, pady=(0, 8))

        self._make_label("Network:")
        self.input_network = ctk.CTkComboBox(self.control_frame,
                                              values=["ERC20", "TRC20", "BTC"],
                                              font=ctk.CTkFont(family="Courier New", size=11),
                                              fg_color="#0a0a0f", text_color="#00ff88",
                                              border_color="#1a3a2a",
                                              dropdown_fg_color="#0d1117")
        self.input_network.pack(fill="x", padx=15, pady=(0, 8))

        self._make_label("Asset:")
        self.input_asset = ctk.CTkComboBox(self.control_frame,
                                            values=["USDT", "BTC", "ETH"],
                                            font=ctk.CTkFont(family="Courier New", size=11),
                                            fg_color="#0a0a0f", text_color="#00ff88",
                                            border_color="#1a3a2a",
                                            dropdown_fg_color="#0d1117")
        self.input_asset.pack(fill="x", padx=15, pady=(0, 15))

        # Separator
        sep = ctk.CTkFrame(self.control_frame, height=1, fg_color="#1a3a2a")
        sep.pack(fill="x", padx=15, pady=5)


        # Buttons
        self.btn_start = ctk.CTkButton(
            self.control_frame, text="▶  START ENGINE",
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            fg_color="#00ff8833", hover_color="#00ff8855",
            border_width=1, border_color="#00ff88",
            text_color="#00ff88", command=self.start_engine
        )
        self.btn_start.pack(fill="x", padx=15, pady=(15, 5))

        self.btn_reload = ctk.CTkButton(
            self.control_frame, text="↻  RELOAD CONFIG",
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#00ccff22", hover_color="#00ccff44",
            border_width=1, border_color="#00ccff",
            text_color="#00ccff", command=self.reload_config
        )
        self.btn_reload.pack(fill="x", padx=15, pady=(5, 5))

        self.btn_clear = ctk.CTkButton(
            self.control_frame, text="✕  CLEAR TERMINAL",
            font=ctk.CTkFont(family="Courier New", size=11),
            fg_color="#ff444422", hover_color="#ff444444",
            border_width=1, border_color="#ff4444",
            text_color="#ff4444", command=self.clear_terminal
        )
        self.btn_clear.pack(fill="x", padx=15, pady=(5, 5))

        # Status bar
        self.status_bar = ctk.CTkLabel(
            self, text="[ READY ] Config loaded from config.json",
            font=ctk.CTkFont(family="Courier New", size=10),
            text_color="#666666", anchor="w"
        )
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))

        # Progress bar (hidden initially)
        self.progress = ctk.CTkProgressBar(self, fg_color="#0a0a0f",
                                            progress_color="#00ff88", height=4)
        self.progress.pack(fill="x", padx=10, pady=(0, 5))
        self.progress.set(0)


    def _make_label(self, text):
        lbl = ctk.CTkLabel(self.control_frame, text=text,
                           font=ctk.CTkFont(family="Courier New", size=10),
                           text_color="#88aaaa", anchor="w")
        lbl.pack(fill="x", padx=15, pady=(5, 2))

    # =================================================================
    # [ TERMINAL OUTPUT ]
    # =================================================================
    def tprint(self, text, color=None, delay=0):
        """Print text to terminal widget."""
        def _do():
            self.terminal.configure(state="normal")
            self.terminal.insert("end", text + "\n")
            self.terminal.see("end")
            self.terminal.configure(state="disabled")
        if delay > 0:
            self.after(int(delay * 1000), _do)
        else:
            _do()

    def tprint_slow(self, text, char_delay=0.02):
        """Type text character by character."""
        self.terminal.configure(state="normal")
        for ch in text:
            self.terminal.insert("end", ch)
            self.terminal.see("end")
            self.terminal.update()
            time.sleep(char_delay)
        self.terminal.insert("end", "\n")
        self.terminal.configure(state="disabled")

    def clear_terminal(self):
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end")
        self.terminal.configure(state="disabled")

    def reload_config(self):
        self.config = load_config()
        self.status_bar.configure(text=f"[ RELOADED ] Config refreshed at {ts()}")
        self.tprint(f"\n  [SYS] Config reloaded from config.json at {ts()}")

    def set_status(self, text):
        self.status_bar.configure(text=text)


    # =================================================================
    # [ ENGINE START ]
    # =================================================================
    def start_engine(self):
        if self.running:
            return
        self.running = True
        self.btn_start.configure(state="disabled", text="⟳  RUNNING...")
        self.clear_terminal()

        # Reload config fresh
        self.config = load_config()

        # Get nominal from input or config
        nominal_str = self.input_nominal.get().strip()
        if nominal_str:
            try:
                self.transfer_amount = int(nominal_str.replace(",", "").replace(".", ""))
            except ValueError:
                self.transfer_amount = self.config.get("target_balance_eur", 49500000)
        else:
            self.transfer_amount = self.config.get("target_balance_eur", 49500000)

        # Run in thread
        t = threading.Thread(target=self._run_engine, daemon=True)
        t.start()

    def _run_engine(self):
        """Main engine sequence — runs all phases."""
        try:
            self._phase_boot()
            self._phase_auth()
            self._phase_network()
            self._phase_trn_scan()
            self._phase_routing()
            self._phase_bridge()
            self._phase_settlement()
        except Exception as e:
            self.tprint(f"\n  [FATAL] {e}")
        finally:
            self.running = False
            self.after(0, lambda: self.btn_start.configure(
                state="normal", text="▶  START ENGINE"))


    # =================================================================
    # [ PHASE 1: BOOT ]
    # =================================================================
    def _phase_boot(self):
        self.after(0, lambda: self.set_status("[ PHASE 1 ] System Boot"))
        banner = """
 ██╗███╗   ██╗████████╗███████╗██████╗ ██████╗  █████╗ ███╗   ██╗██╗  ██╗
 ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
 ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝██████╔╝███████║██╔██╗ ██║█████╔╝
 ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██╔═██╗
 ██║██║ ╚████║   ██║   ███████╗██║  ██║██████╔╝██║  ██║██║ ╚████║██║  ██╗
 ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
"""
        self.tprint(banner)
        self.tprint("  ▸▸▸  INTERBANK TRANSFER TRANSACTION  ◂◂◂")
        self.tprint("  Protocol: BANK-SERVER | Encryption: AES-256-GCM | TLS 1.3")
        self.tprint("  " + "─" * 60)
        time.sleep(0.5)

        boot_items = [
            ("KERNEL", "Loading secure kernel module v4.19.2"),
            ("CRYPTO", "Initializing OpenSSL 3.1.4"),
            ("NET", "Binding to BankNet Core Link 7.4"),
            ("HSM", "Hardware Security Module handshake"),
            ("PKI", "Loading X.509 certificate chain (4096-bit RSA)"),
            ("AUTH", "Starting PAM authentication daemon"),
            ("AUDIT", "Enabling ISO 27001 audit logger"),
            ("MEM", "Allocating 2048MB secure memory"),
            ("CLOCK", "NTP sync to stratum-1 (<2ms)"),
            ("CORE", "Connecting to Core Banking Engine v12.7"),
        ]
        for tag, msg in boot_items:
            self.tprint(f"  [{tag}] {msg} [OK]")
            time.sleep(random.uniform(0.15, 0.35))

        self._animate_progress("System Initialization",
                               self.config.get("timing", {}).get("boot_progress", 8))
        self.tprint("\n  ████  SYSTEM READY  ████")
        time.sleep(1)


    # =================================================================
    # [ PHASE 2: AUTH ]
    # =================================================================
    def _phase_auth(self):
        self.after(0, lambda: self.set_status("[ PHASE 2 ] Authentication"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       AUTHENTICATION GATEWAY")
        self.tprint("       Remote Banking Server Login")
        self.tprint("═" * 60)

        fake_ip = f"103.{random.randint(10,99)}.{random.randint(100,255)}.{random.randint(2,254)}"
        session_id = gen_session_id()

        self.tprint(f"\n  Connecting to : https://{fake_ip}:8443/secure/auth")
        self.tprint(f"  Host          : ibank-server.bankmandiri.co.id")
        self.tprint(f"  Protocol      : TLS 1.3 / AES-256-GCM-SHA384")
        self.tprint(f"  Certificate   : VALID (DigiCert Global Root G2)")
        self.tprint(f"  Session       : {session_id}")
        self.tprint(f"  Timestamp     : {datestamp()} {ts()}")

        timing = self.config.get("timing", {})
        self._spinner("Establishing secure connection", timing.get("auth_connect", 1.5))
        self._spinner("Authenticating operator credentials", timing.get("auth_verify", 1.5))
        self._spinner("Validating 2FA biometric token", timing.get("auth_2fa", 1.2))
        self._spinner("Generating ephemeral session key", timing.get("auth_session_key", 3))

        self.tprint("\n  [✓] IDENTITY CONFIRMED — ACCESS GRANTED")
        self.tprint(f"      Server: ibank-server.bankmandiri.co.id ({fake_ip})")
        time.sleep(0.8)


    # =================================================================
    # [ PHASE 3: NETWORK ]
    # =================================================================
    def _phase_network(self):
        self.after(0, lambda: self.set_status("[ PHASE 3 ] Network Handshake"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       NETWORK HANDSHAKE")
        self.tprint("       Multi-Node Secure Tunnel")
        self.tprint("═" * 60 + "\n")

        hops = [
            (1, "LOCAL-GATEWAY", "ENTRY"),
            (2, "ISP-CORE-ROUTER", "RELAY"),
            (3, "EU-BACKBONE-NODE-7", "TRUNK"),
            (4, "BANK-PROXY-BRUSSELS", "BANK-SRV"),
            (5, "INTERBANK-CORE-LDN", "CORE"),
            (6, "SETTLEMENT-ENGINE-A", "TARGET"),
        ]
        timing = self.config.get("timing", {})
        hop_dur = timing.get("net_hop_duration", 1.0)

        for num, node, ntype in hops:
            latency = random.randint(12, 189)
            self.tprint(f"  HOP {num:02d} ▸▸▸▸▸ {node:<25} [{ntype}] {latency}ms ✓")
            time.sleep(random.uniform(hop_dur * 0.5, hop_dur * 0.8))

        self.tprint(f"\n  Route: LOCAL → ISP → EU → BANK-SRV → CORE → ENGINE")
        self.tprint(f"  Total latency: {random.randint(45,120)}ms | Jitter: <2ms | Loss: 0.00%\n")

        self._spinner("ECDHE key exchange (P-384)", 1.2)
        self._spinner("Forward-secrecy channel", 1.0)
        self._animate_progress("Secure Tunnel",
                               timing.get("net_tunnel_progress", 4))

        self.tprint("\n  [✓] CONNECTED TO GLOBAL SETTLEMENT NETWORK")
        time.sleep(0.8)


    # =================================================================
    # [ PHASE 4: TRN SCAN ]
    # =================================================================
    def _phase_trn_scan(self):
        self.after(0, lambda: self.set_status("[ PHASE 4 ] TRN Deep Scan"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       DEEP TRACE — FUND TRACKING ENGINE")
        self.tprint("       Multi-Node Transaction Scanner v3.2")
        self.tprint("═" * 60)
        self.tprint(f"\n  Mode    : DEEP SCAN (Multi-TRN Parallel Trace)")
        self.tprint(f"  Network : BANK-SERVER + TARGET2 + FEDWIRE + CHAPS")
        self.tprint(f"  Range   : Last 72 hours — All jurisdictions")
        self.tprint(f"  Time    : {datestamp()} {ts()}\n")

        timing = self.config.get("timing", {})

        # Scan nodes
        scan_nodes = [
            "BANK-SERVER Tracker (Brussels)",
            "FEDWIRE Real-Time (New York)",
            "TARGET2 Cluster (Frankfurt)",
            "CHAPS Sterling (London)",
            "SEPA Hub (Amsterdam)",
            "RTGS Asia-Pacific (Singapore)",
        ]
        for node in scan_nodes:
            self._spinner(f"Probing {node}",
                         random.uniform(timing.get("scan_probe_duration", 4) * 0.5,
                                       timing.get("scan_probe_duration", 4) * 0.8))

        self.tprint("\n  [✓] All scan probes deployed.\n")
        time.sleep(0.5)

        # Live feed table
        self.tprint("  ┌────────────────┬──────────┬────────────┬──────────────┬──────────┐")
        self.tprint("  │ TRN REF        │ TYPE     │ BANK       │       AMOUNT │ STATUS   │")
        self.tprint("  ├────────────────┼──────────┼────────────┼──────────────┼──────────┤")

        currencies = ["€", "$", "£", "¥", "CHF"]
        total_scanned = 0
        for i in range(random.randint(40, 60)):
            bank_info = random.choice(BANK_REGISTRY)
            trn = gen_ref("TRN")
            # Censor TRN
            trn_c = trn[:4] + "*" * (len(trn) - 6) + trn[-2:] if len(trn) > 6 else trn
            txtype = random.choice(TXN_TYPES)
            amount = random.randint(100000, 25000000)
            cur = random.choice(currencies)
            st = random.choice(TXN_STATUS)
            total_scanned += random.randint(80000, 200000)

            self.tprint(f"  │ {trn_c:<14} │ {txtype:<8} │ {bank_info[0]:<10} │ {amount:>10,} {cur} │ {st:<8} │")
            time.sleep(random.uniform(0.02, 0.06))

            # Batch scan animation every 10 rows
            if (i + 1) % 10 == 0:
                hex_data = ' '.join([f"{random.randint(0,255):02X}" for _ in range(6)])
                self.tprint(f"  │ [SCAN] Batch #{(i+1)//10} | {9000000+total_scanned:,} scanned | {hex_data} │")
                time.sleep(timing.get("scan_batch_duration", 2) * 0.3)

        self.tprint("  └────────────────┴──────────┴────────────┴──────────────┴──────────┘")
        self.tprint(f"\n  Total Scanned : {9000000+total_scanned:,} transactions")
        time.sleep(0.5)


        # Target found
        self.tprint(f"\n  {'━' * 55}")
        self.tprint(f"  ✓ TARGET SIGNATURE MATCHED — FUND TRACE CONFIRMED ✓")
        self.tprint(f"  {'━' * 55}")
        time.sleep(1)

        # Decrypt layers
        layers = ["Stripping TLS envelope", "Decoding SWIFT payload",
                  "Extracting beneficiary metadata", "Reconstructing ledger entry"]
        for i, desc in enumerate(layers, 1):
            hex_d = ' '.join([f"{random.randint(0,255):02X}" for _ in range(8)])
            self.tprint(f"  [Layer {i}/4] {desc} | {hex_d} [DECODED]")
            time.sleep(0.8)

        # Reveal target
        balance = self.transfer_amount
        cfg = self.config
        self.tprint(f"\n  {'═' * 55}")
        self.tprint(f"    ██  TARGET FUND LOCATED — SIGNATURE VERIFIED  ██")
        self.tprint(f"  {'═' * 55}")
        self.tprint(f"\n  TRN Reference  : {gen_ref('TRN')}")
        self.tprint(f"  Message Type   : Interbank Transaction (Fund Settlement)")
        self.tprint(f"  Ordering Bank  : {cfg.get('target_bank', 'UBS')} BANK")
        self.tprint(f"  Balance        : {cfg.get('currency', 'EUR')} {balance:,.2f}")
        self.tprint(f"  Beneficiary    : {cfg.get('beneficiary_name', 'JOHN DOE')}")
        self.tprint(f"  Value Date     : {datestamp()}")
        self.tprint(f"  Status         : VERIFIED — FUNDS LOCKED IN ESCROW")
        self.tprint(f"\n  [✓] Target fund confirmed: {cfg.get('currency','EUR')} {balance:,.2f} available.")
        time.sleep(1.5)


    # =================================================================
    # [ PHASE 5: ROUTING ]
    # =================================================================
    def _phase_routing(self):
        self.after(0, lambda: self.set_status("[ PHASE 5 ] Settlement Routing"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       SETTLEMENT ROUTING")
        self.tprint("       Destination Bank Configuration")
        self.tprint("═" * 60 + "\n")

        # Get from input fields
        bank_name = self.input_bank.get().strip() or "BANK MANDIRI"
        account_no = self.input_account.get().strip() or "1640004347177"

        # Auto-resolve holder
        holders = self.config.get("account_holders", {})
        holder_name = holders.get(account_no, "ACCOUNT HOLDER")

        # Mask account
        if len(account_no) > 4:
            masked = "*" * (len(account_no) - 4) + account_no[-4:]
        else:
            masked = "*" * len(account_no)

        self.tprint(f"  Destination Bank : {bank_name.upper()}")
        self.tprint(f"  Account Number   : {masked}")
        self.tprint(f"  Holder (Auto)    : {holder_name}")
        self.tprint("")

        timing = self.config.get("timing", {})
        self._spinner("Validating SWIFT Code (ISO 9362)", timing.get("routing_validate", 2.0))
        self._spinner("Cross-referencing AML/KYC database", timing.get("routing_aml", 1.5))
        self._spinner("Confirming correspondent bank", timing.get("routing_correspondent", 5))

        self.tprint(f"\n  ┌────────────────────────────────────────────────┐")
        self.tprint(f"  │      ROUTING VERIFICATION: PASSED              │")
        self.tprint(f"  └────────────────────────────────────────────────┘")
        self.tprint(f"  Bank      : {bank_name.upper()}")
        self.tprint(f"  Account   : {masked}")
        self.tprint(f"  Holder    : {holder_name}")
        self.tprint(f"  AML Check : CLEARED")
        self.tprint(f"  KYC       : VERIFIED")
        time.sleep(1)

        # Store for settlement phase
        self.routing_info = {
            "bank_name": bank_name.upper(),
            "account_no": account_no,
            "masked": masked,
            "holder_name": holder_name,
        }


    # =================================================================
    # [ PHASE 6: BRIDGE ]
    # =================================================================
    def _phase_bridge(self):
        self.after(0, lambda: self.set_status("[ PHASE 6 ] Settlement Bridge"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       SETTLEMENT BRIDGE")
        self.tprint("       Institutional Firewall Traversal")
        self.tprint("═" * 60 + "\n")

        firewalls = [
            ("SANCTIONS-SCREEN", "COMPLIANCE", "Sanctions list cross-check"),
            ("FED-RESERVE-OFAC", "REGULATORY", "OFAC/SDN clearance"),
            ("ECB-OVERSIGHT", "REGULATORY", "ECB transaction monitoring"),
            ("INTERPOL-I-24/7", "SECURITY", "Financial crime scan"),
            ("FATF-GREYLIST", "AML", "FATF mutual evaluation"),
            ("COLD-WALLET-AUTH", "CRYPTO", "Multi-sig authorization"),
            ("NOSTRO-LINK", "BANKING", "Nostro account reconciliation"),
        ]

        for fw_name, fw_type, desc in firewalls:
            dots = "·" * random.randint(5, 12)
            self.tprint(f"  [{fw_type:^12}] {fw_name:<22} {dots} [CLEARED]")
            self.tprint(f"               └─ {desc}")
            time.sleep(random.uniform(0.3, 0.7))

        timing = self.config.get("timing", {})
        self.tprint("")
        self._animate_progress("Multi-Sig Escrow Override", 2.5)
        self._animate_progress("Syncing Settlement Tunnel",
                               timing.get("bridge_sync_progress", 4))

        self.tprint("\n  [✓] ALL LAYERS CLEARED — SETTLEMENT BRIDGE ACTIVE")
        time.sleep(0.8)


    # =================================================================
    # [ PHASE 7: SETTLEMENT (Always fails based on config) ]
    # =================================================================
    def _phase_settlement(self):
        self.after(0, lambda: self.set_status("[ PHASE 7 ] Blockchain Settlement"))
        self.tprint("\n" + "═" * 60)
        self.tprint("       BLOCKCHAIN SETTLEMENT ENGINE")
        self.tprint("       Fiat-to-Crypto Bridge Protocol")
        self.tprint("═" * 60)

        wallet = self.input_wallet.get().strip()
        if not wallet:
            wallet = "0x" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:40]
        network = self.input_network.get()
        coin = self.input_asset.get()

        balance = self.transfer_amount
        rate = CRYPTO_RATES.get(coin, 1.0)
        crypto_amt = balance / rate
        gas_fee = random.uniform(0.5, 15.0)
        cfg = self.config

        self.tprint(f"\n  From    : ESCROW VAULT")
        self.tprint(f"  To      : {wallet[:24]}...{wallet[-8:]}")
        self.tprint(f"  Amount  : {cfg.get('currency','EUR')} {balance:>14,.2f}")
        self.tprint(f"  Convert : {crypto_amt:>14,.4f} {coin}")
        self.tprint(f"  Rate    : 1 {coin} = {cfg.get('currency','EUR')} {rate:,.2f}")
        self.tprint(f"  Network : {network} | Gas: ~{gas_fee:.2f} {coin}")
        self.tprint("")

        self._spinner("Signing transaction with HSM private key", 1.5)
        self._spinner("Broadcasting to mempool", 1.0)

        # Progress bar with failure
        timing = self.config.get("timing", {})
        settle_dur = timing.get("settlement_duration", 30)
        self._animate_progress_fail("Propagating across validators", settle_dur)


        # Get failure message from config
        result_mode = cfg.get("result_mode", "SETTLEMENT_LIMIT")
        result_options = cfg.get("result_options", {})
        if result_mode == "CUSTOM":
            fail_msg = cfg.get("custom_message", "DECLINED BY EXCHANGE")
        else:
            fail_msg = result_options.get(result_mode, "DECLINED — Settlement limit exceeded.")

        # Display failure
        err_code = f"0x{random.randint(0xA000, 0xFFFF):04X}"
        tx_hash = "0x" + hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:64]

        self.tprint(f"\n  [✗] CRITICAL: Smart contract execution reverted")
        self.tprint(f"  [✗] TX REJECTED: Amount exceeds settlement capacity")
        time.sleep(0.5)

        self.tprint(f"\n  ╔{'═' * 56}╗")
        self.tprint(f"  ║{'SETTLEMENT FAILED':^56}║")
        self.tprint(f"  ╠{'═' * 56}╣")
        self.tprint(f"  ║  Error      : ERR_NETWORK_TIMEOUT ({err_code})" + " " * 10 + "║")
        self.tprint(f"  ║  TX Hash    : {tx_hash[:42]}...  ║")
        self.tprint(f"  ║  Beneficiary: {self.routing_info['holder_name']:<40}║")
        self.tprint(f"  ║  Bank       : {self.routing_info['bank_name']} ({self.routing_info['masked']})" + " " * max(0, 27 - len(self.routing_info['bank_name']) - len(self.routing_info['masked'])) + "║")
        self.tprint(f"  ║  Wallet     : {wallet[:42]:<42}║")
        self.tprint(f"  ║  Amount     : {crypto_amt:,.4f} {coin}" + " " * max(0, 36 - len(f"{crypto_amt:,.4f} {coin}")) + "║")
        self.tprint(f"  ║  Status     : {fail_msg[:42]:<42}║")
        self.tprint(f"  ╚{'═' * 56}╝")
        self.tprint(f"\n  {fail_msg}")
        self.tprint(f"  Transaction declined at {ts()}")
        self.tprint(f"  Contact exchange liaison for manual settlement approval.")

        self.after(0, lambda: self.set_status(f"[ COMPLETED ] Result: {result_mode}"))
        self.after(0, lambda: self.progress.configure(progress_color="#ff4444"))
        self.after(0, lambda: self.progress.set(0.78))


    # =================================================================
    # [ ANIMATION HELPERS ]
    # =================================================================
    def _spinner(self, label, duration=2.0):
        """Simulate spinner in terminal textbox."""
        frames = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        start = time.time()
        i = 0
        while time.time() - start < duration:
            pct = min(int(((time.time() - start) / duration) * 100), 99)
            frame = frames[i % len(frames)]
            # Update last line
            text = f"  [{frame}] {label} ({pct}%)"
            self._update_last_line(text)
            time.sleep(0.08)
            i += 1
        self._update_last_line(f"  [✓] {label} (100%)")
        self.tprint("")  # newline after

    def _animate_progress(self, label, duration=3.0):
        """Animate a text-based progress bar in terminal."""
        width = 30
        steps = 50
        step_dur = duration / steps
        for i in range(steps + 1):
            filled = int((i / steps) * width)
            empty = width - filled
            bar = "█" * filled + "░" * empty
            pct = int((i / steps) * 100)
            text = f"  [SYS] {label} [{bar}] {pct}%"
            self._update_last_line(text)
            time.sleep(step_dur)
            # Update GUI progress bar
            self.after(0, lambda v=i/steps: self.progress.set(v))
        self.tprint("")

    def _animate_progress_fail(self, label, duration=30.0):
        """Progress bar that fails at ~78%."""
        width = 30
        fail_pct = 0.78
        steps_green = int(50 * fail_pct)
        step_dur = duration / 50

        for i in range(steps_green):
            filled = int((i / 50) * width)
            empty = width - filled
            bar = "█" * filled + "░" * empty
            pct = int((i / 50) * 100)
            text = f"  [TX] {label} [{bar}] {pct}%"
            self._update_last_line(text)
            self.after(0, lambda v=i/50: self.progress.set(v))
            time.sleep(step_dur)

        # Freeze and fail
        time.sleep(min(duration * 0.1, 3))
        filled = int(fail_pct * width)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        text = f"  [TX] {label} [{bar}] FAILED"
        self._update_last_line(text)
        self.tprint("")

    def _update_last_line(self, text):
        """Replace last line in terminal."""
        def _do():
            self.terminal.configure(state="normal")
            # Delete last line
            last_line_start = self.terminal.index("end-2l linestart")
            last_line_end = self.terminal.index("end-1l lineend")
            current = self.terminal.get(last_line_start, last_line_end)
            if current.strip():
                self.terminal.delete(last_line_start, last_line_end + "+1c")
            self.terminal.insert("end", text + "\n")
            self.terminal.see("end")
            self.terminal.configure(state="disabled")
        self.after(0, _do)
        time.sleep(0.01)  # Give GUI time to update



# =====================================================================
# [ ENTRY POINT ]
# =====================================================================
if __name__ == "__main__":
    app = InterbankApp()
    app.mainloop()
