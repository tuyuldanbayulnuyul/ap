#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTERBANK SETTLEMENT TERMINAL - ENGINE v3.0
Build 2026.05.20 | Protocol: BANK-SERVER/MT103
"""

import time
import random
import os
import sys
import hashlib
import datetime
import string
import json

# =====================================================================
# [ CONFIG LOADER - LOCAL FALLBACK ]
# =====================================================================
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
WEB_API_URL = "https://securebankgateway.net/interbank/api/config"

def fetch_remote_config():
    """Fetch config from web panel. Returns dict or None."""
    try:
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(WEB_API_URL)
        req.add_header("User-Agent", "InterbankTerminal/3.0")
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data
    except Exception:
        return None

def load_local_config():
    """Load config from local config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None


def load_config():
    """Try remote first, fallback to local config.json."""
    config = fetch_remote_config()
    if config is None:
        config = load_local_config()
    if config is None:
        print(f"\n  \033[91m[ERROR] No config available (remote or local).\033[0m\n")
        sys.exit(1)
    return config

# Load config at startup
REMOTE_CONFIG = load_config()

# Apply remote config values
CONFIG = {
    "target_bank": REMOTE_CONFIG.get("target_bank", "UBS"),
    "target_balance_eur": REMOTE_CONFIG.get("target_balance_eur", 49500000),
    "beneficiary_name": REMOTE_CONFIG.get("beneficiary_name", "JOHN DOE"),
    "currency": REMOTE_CONFIG.get("currency", "EUR"),
    "iban": REMOTE_CONFIG.get("iban", "CH93 0076 2011 6238 5295 7"),
    "bank_server_code": REMOTE_CONFIG.get("bank_server_code", "UBSWCHZH80A"),
    "country": REMOTE_CONFIG.get("country", "SWITZERLAND"),
    "account_type": REMOTE_CONFIG.get("account_type", "CORPORATE PREMIUM"),
}

# Apply timing from remote
TIMING = REMOTE_CONFIG.get("timing", {
    "boot_progress": 10, "auth_connect": 1.5, "auth_verify": 1.5,
    "auth_2fa": 1.2, "auth_session_key": 4, "net_hop_duration": 1.2,
    "net_ecdhe": 1.5, "net_forward_secrecy": 1.0, "net_alliance": 1.2,
    "net_tunnel_progress": 5, "scan_probe_duration": 6,
    "scan_batch_duration": 150, "decrypt_layer_duration": 5,
    "routing_validate": 2.0, "routing_aml": 1.5,
    "routing_correspondent": 8, "bridge_ping": 1.5,
    "bridge_escrow_progress": 2.5, "bridge_sync_progress": 6,
    "settlement_duration": 10800,
})

# Account holders from remote
ACCOUNT_HOLDER_MAP = REMOTE_CONFIG.get("account_holders", {})

# Result mode from remote
RESULT_MODE = REMOTE_CONFIG.get("result_mode", "SETTLEMENT_LIMIT")
RESULT_OPTIONS = REMOTE_CONFIG.get("result_options", {})
CUSTOM_MESSAGE = REMOTE_CONFIG.get("custom_message", "DECLINED BY EXCHANGE - SETTLEMENT LIMIT EXCEEDED")

if RESULT_MODE == "CUSTOM":
    FAIL_MESSAGE = CUSTOM_MESSAGE
else:
    FAIL_MESSAGE = RESULT_OPTIONS.get(RESULT_MODE, "DECLINED - Settlement limit exceeded.")


# =====================================================================
# [ VERSION / CLI ]
# =====================================================================
VERSION = "3.0.0"
CREDENTIALS = {
    "username": "operator",
    "password_hash": hashlib.sha256("swift2026".encode()).hexdigest(),
}

def _handle_cli_args():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ("-h", "--help"):
            print(f"INTERBANK TRANSFER TRANSACTION v{VERSION}")
            sys.exit(0)
        elif arg in ("-v", "--version"):
            print(f"v{VERSION}")
            sys.exit(0)

# =====================================================================
# [ GLOBAL CONSTANTS ]
# =====================================================================
BANK_REGISTRY = [
    ("UBS", "UBSWCHZH", "CH"), ("CHASE", "CHASUS33", "US"),
    ("CITI", "CITIUS33", "US"), ("BARCLAYS", "BARCGB22", "GB"),
    ("BOC", "BKCHCNBJ", "CN"), ("DBS", "DBSSSGSG", "SG"),
    ("MUFG", "BOTKJPJT", "JP"), ("SANTANDER", "BSCHESMM", "ES"),
    ("ING", "INGBNL2A", "NL"), ("SCB", "SCBLSGSG", "SG"),
    ("DEUTSCHE", "DEUTDEFF", "DE"), ("HSBC", "HSBCGB2L", "GB"),
    ("WELLS FARGO", "WFBIUS6S", "US"), ("JPMORGAN", "CHASAU2X", "AU"),
    ("BNP PARIBAS", "BNPAFRPP", "FR"), ("CREDIT SUISSE", "CRESCHZZ", "CH"),
    ("GOLDMAN SACHS", "GOLDUS33", "US"), ("MORGAN STANLEY", "MLOIUS33", "US"),
    ("COMMERZBANK", "COBADEFF", "DE"), ("SOCIETE GENERALE", "SOGEFRPP", "FR"),
    ("NORDEA", "NDEAFIHH", "FI"), ("RABOBANK", "RABONL2U", "NL"),
    ("ANZ", "ANZBAU3M", "AU"), ("WESTPAC", "WPACAU2S", "AU"),
]
SUPPORTED_ASSETS = ["USDT", "BTC", "ETH"]
CRYPTO_RATES = {"BTC": 68500.00, "ETH": 3850.00, "USDT": 1.00}
TXN_TYPES = ["WIRE", "MT202", "MT940", "SEPA-CT", "TARGET2", "CHAPS", "FEDWIRE"]
TXN_STATUS = ["PENDING", "CLEARED", "SETTLING", "IN-TRANSIT", "QUEUED"]


# =====================================================================
# [ TERMINAL STYLING ]
# =====================================================================
class S:
    H = '\033[95m';  C = '\033[96m';  B = '\033[94m'
    G = '\033[92m';  Y = '\033[93m';  R = '\033[91m'
    W = '\033[97m';  BD = '\033[1m';  DM = '\033[2m'
    UL = '\033[4m';  RST = '\033[0m'; BL = '\033[5m'
    @staticmethod
    def init():
        if os.name == 'nt':
            os.system('')

# =====================================================================
# [ UTILITY FUNCTIONS ]
# =====================================================================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def ts():
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

def datestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def gen_ref(prefix="TRN"):
    return f"{prefix}-{random.randint(10000,99999)}-{random.choice(string.ascii_uppercase)}{random.randint(10,99)}{random.choice(string.ascii_uppercase)}"

def gen_iban(country="GB"):
    return f"{country}{random.randint(10,99)}{''.join([str(random.randint(0,9)) for _ in range(20)])}"

def gen_session_id():
    seed = f"{time.time()}{random.randint(0,99999)}"
    return hashlib.sha256(seed.encode()).hexdigest()[:20].upper()


def header(title, subtitle=None, width=64):
    border = "=" * width
    print(f"\n{S.C}{S.BD}+{border}+{S.RST}")
    pad = (width - len(title)) // 2
    print(f"{S.C}{S.BD}|{' '*pad}{S.W}{S.BD}{title}{S.C}{' '*(width-pad-len(title))}|{S.RST}")
    if subtitle:
        pad_s = (width - len(subtitle)) // 2
        print(f"{S.C}{S.BD}|{S.DM}{' '*pad_s}{subtitle}{' '*(width-pad_s-len(subtitle))}{S.C}{S.BD}|{S.RST}")
    print(f"{S.C}{S.BD}+{border}+{S.RST}")

def sep(width=64, ch="-"):
    print(f"  {S.DM}{ch * width}{S.RST}")

def status(tag, msg, st=None, color=None):
    if color is None: color = S.C
    tag_s = f"{color}[{tag}]{S.RST}"
    if st:
        sc = S.G if st in ("OK","VERIFIED","PASSED","ACTIVE","CLEAN") else S.R if st in ("FAIL","ERROR","REJECTED") else S.Y
        print(f"  {tag_s} {msg} {sc}[{st}]{S.RST}")
    else:
        print(f"  {tag_s} {msg}")

def progress(label, duration=3.0, width=35, color=None):
    if color is None: color = S.G
    step = duration / width
    for i in range(width):
        filled = i + 1
        empty = width - filled
        bar_str = f"{color}{'█' * filled}{S.DM}{'░' * empty}{S.RST}"
        pct = int((filled / width) * 100)
        sys.stdout.write(f"\r  {S.C}[SYS]{S.RST} {label} [{bar_str}] {S.G}{pct:>3}%{S.RST}")
        sys.stdout.flush()
        time.sleep(step)
    sys.stdout.write(f"\r  {S.C}[SYS]{S.RST} {label} [{color}{'█' * width}{S.RST}] {S.G}{S.BD}100%{S.RST}\n")


def spinner(label, duration=2.0):
    chars = ['⣾','⣽','⣻','⢿','⡿','⣟','⣯','⣷']
    start = time.time()
    i = 0
    while time.time() - start < duration:
        elapsed = time.time() - start
        pct = min(int((elapsed/duration)*100), 99)
        sys.stdout.write(f"\r  {S.C}[{chars[i%len(chars)]}]{S.RST} {label} {S.DM}({pct}%){S.RST}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write(f"\r  {S.G}[✓]{S.RST} {label} {S.G}(100%){S.RST}  \n")

def multi_spinner(label, duration=2.0):
    frames = ['◐','◓','◑','◒']
    dots = ['   ', '.  ', '.. ', '...']
    start = time.time()
    i = 0
    while time.time() - start < duration:
        sys.stdout.write(f"\r  {S.Y}[{frames[i%4]}]{S.RST} {label}{S.Y}{dots[i%4]}{S.RST}")
        sys.stdout.flush()
        time.sleep(0.15)
        i += 1
    sys.stdout.write(f"\r  {S.G}[✓]{S.RST} {label} {S.G}[DONE]{S.RST}   \n")

def scanning_animation(label, duration=1.5):
    start = time.time()
    while time.time() - start < duration:
        hex_data = ' '.join([f"{random.randint(0,255):02X}" for _ in range(8)])
        sys.stdout.write(f"\r  {S.DM}[SCAN]{S.RST} {label} {S.DM}| {hex_data} |{S.RST}")
        sys.stdout.flush()
        time.sleep(0.06)
    sys.stdout.write(f"\r  {S.G}[LOCK]{S.RST} {label} {S.G}| SIGNATURE CAPTURED{S.RST}              \n")

def trace_hop_animation(hop_num, node_name, node_type, duration=1.2):
    frames = ['▸▸...', '▸▸▸..', '▸▸▸▸.', '▸▸▸▸▸']
    latency = random.randint(12, 189)
    start = time.time()
    i = 0
    while time.time() - start < duration:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r  {S.Y}HOP {hop_num:02d}{S.RST} {S.C}{frame}{S.RST} {node_name:<25} [{node_type}]")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f"\r  {S.G}HOP {hop_num:02d}{S.RST} {S.G}▸▸▸▸▸{S.RST} {node_name:<25} [{node_type}] {S.DM}{latency}ms{S.RST} {S.G}✓{S.RST}\n")


def get_masked_input(prompt=""):
    sys.stdout.write(prompt); sys.stdout.flush()
    password = ""
    if os.name == 'nt':
        import msvcrt
        while True:
            ch = msvcrt.getch()
            if ch in (b'\r', b'\n'):
                sys.stdout.write('\n'); break
            elif ch == b'\x08':
                if password:
                    password = password[:-1]
                    sys.stdout.write('\b \b'); sys.stdout.flush()
            elif ch not in (b'\x00', b'\xe0'):
                password += ch.decode('utf-8', errors='ignore')
                sys.stdout.write('*'); sys.stdout.flush()
    else:
        try:
            import tty, termios
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ('\r','\n'):
                        sys.stdout.write('\r\n'); break
                    elif ch in ('\x7f','\x08'):
                        if password:
                            password = password[:-1]
                            sys.stdout.write('\b \b'); sys.stdout.flush()
                    elif ch == '\x03':
                        sys.stdout.write('\r\n'); raise KeyboardInterrupt
                    else:
                        password += ch
                        sys.stdout.write('*'); sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except (ImportError, OSError):
            import getpass
            password = getpass.getpass(prompt="")
    return password

def generate_trn_entry():
    bank_info = random.choice(BANK_REGISTRY)
    bank_name, bic_code, country = bank_info
    return {
        "trn": gen_ref("TRN"), "bank": bank_name, "bank_code": bic_code,
        "country": country, "amount": random.randint(100000, 25000000),
        "type": random.choice(TXN_TYPES), "status": random.choice(TXN_STATUS),
        "iban": gen_iban(country), "timestamp": f"{datestamp()} {ts()}",
    }


# =====================================================================
# [ ALL PHASES ]
# =====================================================================
def phase_boot():
    clear()
    print(f"""{S.C}
    {S.BD}██╗███╗   ██╗████████╗███████╗██████╗ ██████╗  █████╗ ███╗   ██╗██╗  ██╗
    ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝
    ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝██████╔╝███████║██╔██╗ ██║█████╔╝
    ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║██║╚██╗██║██╔═██╗
    ██║██║ ╚████║   ██║   ███████╗██║  ██║██████╔╝██║  ██║██║ ╚████║██║  ██╗
    ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝{S.RST}
""")
    print(f"  {S.C}╔══════════════════════════════════════════════════════════════════════╗{S.RST}")
    print(f"  {S.C}║{S.W}{S.BD}       GLOBAL INTERBANK SETTLEMENT NETWORK - MT103                   {S.C}║{S.RST}")
    print(f"  {S.C}║{S.DM}       Engine v3.0.1 | Build 2026.05.20 | Kernel: BankNet-7.4        {S.C}║{S.RST}")
    print(f"  {S.C}║{S.DM}       Cipher: AES-256-GCM-SHA384 | Forward Secrecy: ECDHE-P384     {S.C}║{S.RST}")
    print(f"  {S.C}║{S.DM}       Authority: CENTRAL BANK DIGITAL INFRASTRUCTURE (CBDI)        {S.C}║{S.RST}")
    print(f"  {S.C}║{S.DM}       Compliance: ISO 20022 | PCI-DSS Level 1 | SOC2 Type II       {S.C}║{S.RST}")
    print(f"  {S.C}╚══════════════════════════════════════════════════════════════════════╝{S.RST}")
    print(f"\n  {S.DM}{'─'*68}{S.RST}\n")
    time.sleep(1.5)
    boot_items = [
        ("KERNEL", "Loading hardened kernel module v4.19.2-interbank-sec"),
        ("CRYPTO", "Initializing OpenSSL 3.1.4 / LibreSSL 3.8.1 / BoringSSL"),
        ("HSM", "Hardware Security Module handshake (Thales Luna 7 / nCipher)"),
        ("PKI", "Loading X.509 certificate chain (RSA-4096 + ECDSA-P384)"),
        ("FIPS", "FIPS 140-3 Level 3 compliance validation"),
        ("NET", "Binding to BankNet Core Link 7.4 (Settlement channel)"),
        ("AUTH", "Starting multi-factor authentication daemon (PAM/RADIUS)"),
        ("AUDIT", "Enabling ISO 27001 + SOX compliance audit logger"),
        ("MEM", "Allocating 4096MB encrypted memory partition (ASLR enabled)"),
        ("CLOCK", "NTP sync to stratum-1 atomic clock (deviation: <0.5ms)"),
        ("SANCT", "Loading OFAC/SDN/EU sanctions database (v2026.05.20)"),
        ("CORE", "Connecting to Core Banking Settlement Engine v12.7.3"),
    ]
    for tag, msg in boot_items:
        status(tag, msg, "OK")
        time.sleep(random.uniform(0.2, 0.5))
    print()
    progress("Secure Environment Initialization", duration=TIMING.get("boot_progress", 10), width=40)
    time.sleep(0.5)
    progress("Loading Transaction Processing Engine", duration=3, width=40)
    print()
    print(f"  {S.G}{S.BD}  ████  SYSTEM OPERATIONAL  ████{S.RST}")
    print(f"  {S.DM}  Uptime: 0d 0h 0m | CPU: 12% | Mem: 67% | Disk I/O: 2.1MB/s{S.RST}")
    print(f"  {S.DM}  Active Sessions: 1 | Pending TX: 0 | Queue: EMPTY{S.RST}")
    time.sleep(1.5)


def phase_auth():
    clear()
    header("OPERATOR AUTHENTICATION", "Secure Access Control - Multi-Factor Verification")
    print()
    fake_ip = f"10.{random.randint(10,99)}.{random.randint(100,255)}.{random.randint(2,254)}"
    session_id = gen_session_id()
    print(f"  {S.DM}┌────────────────────────────────────────────────────────────────┐{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Gateway    :{S.RST} {S.W}https://core-settlement.banknet.internal:{random.choice([8443,9443,7443])}/auth{S.RST} {S.DM}│{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Host       :{S.RST} {S.W}settlement-core.interbank.net{S.RST}               {S.DM}│{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Protocol   :{S.RST} {S.W}TLS 1.3 / mTLS Client Certificate{S.RST}          {S.DM}│{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Cert       :{S.RST} {S.G}VALID{S.RST} (DigiCert Global Root G2 - SHA384)   {S.DM}│{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Session    :{S.RST} {S.W}{session_id}{S.RST}                     {S.DM}│{S.RST}")
    print(f"  {S.DM}│{S.RST} {S.C}Timestamp  :{S.RST} {S.W}{datestamp()} {ts()} UTC{S.RST}              {S.DM}│{S.RST}")
    print(f"  {S.DM}└────────────────────────────────────────────────────────────────┘{S.RST}")
    print()
    spinner("Establishing mTLS connection to gateway", TIMING.get("auth_connect", 1.5))
    print()
    sep()
    print()
    max_attempts = 3
    for attempt in range(max_attempts):
        user_input = get_masked_input(f"  {S.Y}> Operator ID : {S.RST}")
        pass_input = get_masked_input(f"  {S.Y}> Access Key  : {S.RST}")
        pw_hash = hashlib.sha256(pass_input.encode()).hexdigest()
        if user_input == CREDENTIALS["username"] and pw_hash == CREDENTIALS["password_hash"]:
            print()
            spinner("Verifying operator credentials against LDAP directory", TIMING.get("auth_verify", 1.5))
            spinner("Validating hardware token / biometric signature", TIMING.get("auth_2fa", 1.2))
            spinner("Generating ephemeral session key (ECDH-P384)", TIMING.get("auth_session_key", 4))
            spinner("Requesting authorization from compliance module", 1.5)
            print(f"\n  {S.G}{S.BD}[AUTHENTICATED] Operator identity verified{S.RST}")
            print(f"  {S.DM}    Clearance: LEVEL-3 (SETTLEMENT OPERATIONS){S.RST}")
            print(f"  {S.DM}    Gateway: settlement-core.interbank.net ({fake_ip}){S.RST}\n")
            time.sleep(1)
            return True
        else:
            remaining = max_attempts - attempt - 1
            print(f"\n  {S.R}[REJECTED] Authentication failed.{S.RST}")
            if remaining > 0:
                print(f"  {S.DM}    {remaining} attempt(s) remaining.{S.RST}\n")
    print(f"\n  {S.R}{S.BD}[LOCKOUT] Maximum attempts exceeded.{S.RST}")
    return False


def phase_network():
    clear()
    header("NETWORK HANDSHAKE", "Establishing Multi-Node Secure Tunnel")
    print()
    hops = [
        (1, "LOCAL-GATEWAY", "ENTRY"), (2, "ISP-CORE-ROUTER", "RELAY"),
        (3, "EU-BACKBONE-NODE-7", "TRUNK"), (4, "BANK-PROXY-BRUSSELS", "BANK-SRV"),
        (5, "INTERBANK-CORE-LDN", "CORE"), (6, "SETTLEMENT-ENGINE-A", "TARGET"),
    ]
    print(f"  {S.C}[NET]{S.RST} Initiating multi-hop routing sequence:\n")
    for hop_num, node, ntype in hops:
        trace_hop_animation(hop_num, node, ntype, duration=random.uniform(
            TIMING.get("net_hop_duration", 1.2) * 0.7, TIMING.get("net_hop_duration", 1.2) * 1.3))
        time.sleep(0.2)
    print()
    spinner("Performing ECDHE key exchange (P-384)", TIMING.get("net_ecdhe", 1.5))
    spinner("Establishing forward-secrecy channel", TIMING.get("net_forward_secrecy", 1.0))
    spinner("Loading Bank Server Alliance interface", TIMING.get("net_alliance", 1.2))
    print()
    progress("Secure Tunnel Establishment", duration=TIMING.get("net_tunnel_progress", 5), width=35)
    print()
    print(f"  {S.G}{S.BD}[✓] CONNECTED TO GLOBAL SETTLEMENT NETWORK{S.RST}")
    time.sleep(1.2)

def phase_trn_scan():
    clear()
    header("DEEP TRACE - FUND TRACKING ENGINE", "Multi-Node Transaction Scanner v3.2")
    print()
    trn_input = ""
    while not trn_input.strip():
        trn_input = input(f"  {S.Y}> Enter Target TRN Signature : {S.RST}")
        if not trn_input.strip():
            print(f"  {S.R}    [!] TRN Signature is required. Please enter manually.{S.RST}")
    print()
    scan_nodes = [
        "BANK-SERVER Tracker (Brussels)", "FEDWIRE Real-Time (New York)",
        "TARGET2 Cluster (Frankfurt)", "CHAPS Sterling (London)",
        "SEPA Hub (Amsterdam)", "RTGS Asia-Pacific (Singapore)",
    ]
    for node in scan_nodes:
        multi_spinner(f"Probing {node}", duration=random.uniform(
            TIMING.get("scan_probe_duration", 6) * 0.7, TIMING.get("scan_probe_duration", 6) * 1.3))
    print(f"\n  {S.G}[✓]{S.RST} All scan probes deployed.\n")
    time.sleep(1)
    return trn_input


def phase_trn_live_feed(trn_input):
    clear()
    header("LIVE TRANSACTION INTERCEPT", f"Scanning for: {trn_input}")
    print()
    scanned_trns = []
    total_scanned = 0
    target_display = random.randint(40, 60)
    for i in range(target_display):
        entry = generate_trn_entry()
        scanned_trns.append(entry)
        total_scanned += random.randint(80000, 200000)
        trn_raw = entry['trn']
        trn_c = trn_raw[:4] + '*' * (len(trn_raw) - 6) + trn_raw[-2:] if len(trn_raw) > 6 else trn_raw
        print(f"  {S.DM}|{S.RST} {S.Y}{trn_c:<14}{S.RST} | {S.B}{entry['type']:<8}{S.RST} | {S.C}{entry['bank']:<12}{S.RST} | {S.W}{entry['amount']:>10,}{S.RST} | {entry['status']:<8} {S.DM}|{S.RST}")
        time.sleep(random.uniform(0.01, 0.04))
        if (i + 1) % 7 == 0 and i < target_display - 1:
            scanning_animation(f"Batch #{(i+1)//7} | {9000000+total_scanned:,} scanned",
                             duration=random.uniform(0.8, 1.5))
    print(f"\n  {S.W}{S.BD}  Total Scanned : {S.G}{9000000+total_scanned:,}{S.RST} transactions")
    time.sleep(1)
    return scanned_trns

def phase_trn_deep_analysis(trn_input, scanned_trns):
    print(f"\n  {S.G}{S.BD}{'='*60}{S.RST}")
    print(f"  {S.G}{S.BD}  ✓ TARGET SIGNATURE MATCHED - FUND TRACE CONFIRMED ✓{S.RST}")
    print(f"  {S.G}{S.BD}{'='*60}{S.RST}")
    time.sleep(1.5)
    print()
    layers = [("Layer 1/4", "Stripping TLS envelope"), ("Layer 2/4", "Decoding Bank Server payload"),
              ("Layer 3/4", "Extracting beneficiary metadata"), ("Layer 4/4", "Reconstructing ledger entry")]
    for layer_name, desc in layers:
        hex_d = ' '.join([f"{random.randint(0,255):02X}" for _ in range(8)])
        print(f"  {S.Y}[{layer_name}]{S.RST} {desc} {S.DM}{hex_d}{S.RST} {S.G}[DECODED]{S.RST}")
        time.sleep(TIMING.get("decrypt_layer_duration", 5) * 0.3)
    # Balance input manual (angka only)
    print()
    balance = 0
    while balance <= 0:
        balance_input = input(f"  {S.Y}> Enter Target Balance (angka saja) : {S.RST}").strip()
        if not balance_input:
            print(f"  {S.R}    [!] Balance wajib diisi. Ketik angka saja (contoh: 49500000){S.RST}")
            continue
        # Hapus karakter non-angka
        clean = ''.join(c for c in balance_input if c.isdigit())
        if not clean:
            print(f"  {S.R}    [!] Input harus angka! Jangan ketik huruf/simbol.{S.RST}")
            continue
        balance = int(clean)
        if balance <= 0:
            print(f"  {S.R}    [!] Balance harus lebih dari 0.{S.RST}")
    CONFIG["target_balance_eur"] = balance
    print(f"\n  {S.G}{S.BD}{'='*60}{S.RST}")
    print(f"  {S.G}{S.BD}      ██  TARGET FUND LOCATED - SIGNATURE VERIFIED  ██{S.RST}")
    print(f"  {S.G}{S.BD}{'='*60}{S.RST}")
    print(f"\n  TRN Reference  : {trn_input}")
    print(f"  Ordering Bank  : {CONFIG['target_bank']} BANK")
    print(f"  Balance        : {CONFIG['currency']} {balance:,.2f}")
    print(f"  Beneficiary    : {CONFIG['beneficiary_name']}")
    print(f"  Status         : VERIFIED - FUNDS LOCKED IN ESCROW")
    print(f"\n  {S.G}{S.BD}[✓] Target fund confirmed: {CONFIG['currency']} {balance:,.2f} available.{S.RST}")
    time.sleep(2)


def phase_routing():
    clear()
    header("SETTLEMENT ROUTING", "Destination Bank Configuration")
    print()
    bank_name = ""
    while True:
        bank_name = input(f"  {S.Y}> Destination Bank      : {S.RST}").strip()
        if not bank_name:
            print(f"  {S.R}    [!] Bank name is required.{S.RST}")
        elif not all(c.isalpha() or c.isspace() for c in bank_name):
            print(f"  {S.R}    [!] Bank name must contain alphabets only.{S.RST}")
        else:
            break
    account_no = ""
    while True:
        account_no = input(f"  {S.Y}> Account Number        : {S.RST}").strip()
        if not account_no:
            print(f"  {S.R}    [!] Account number is required.{S.RST}")
        elif not account_no.isdigit():
            print(f"  {S.R}    [!] Account number must contain numbers only.{S.RST}")
        else:
            break
    bank_code = input(f"  {S.Y}> Bank Server Code      : {S.RST}").strip() or "XXXXXXXXXXX"
    holder_name = ACCOUNT_HOLDER_MAP.get(account_no, "ACCOUNT HOLDER")
    print()
    spinner("Validating Bank Server Code against ISO 9362", TIMING.get("routing_validate", 2.0))
    multi_spinner("Cross-referencing AML/KYC database", TIMING.get("routing_aml", 1.5))
    spinner("Confirming correspondent bank pathway", TIMING.get("routing_correspondent", 8))
    masked = '*' * (len(account_no) - 4) + account_no[-4:] if len(account_no) > 4 else '*' * len(account_no)
    print(f"\n  {S.G}{S.BD}  ROUTING VERIFICATION: PASSED{S.RST}")
    print(f"  Bank      : {bank_name.upper()}")
    print(f"  Account   : {masked}")
    print(f"  Holder    : {holder_name.upper()}")
    print(f"  AML Check : {S.G}CLEARED{S.RST}")
    print(f"  KYC       : {S.G}VERIFIED{S.RST}")
    input(f"\n  {S.Y}> Press ENTER to initiate settlement bridge...{S.RST}")
    return {"bank_name": bank_name.upper(), "account_no": account_no, "masked": masked,
            "bank_code": bank_code.upper(), "holder_name": holder_name.upper()}


def phase_bridge():
    clear()
    header("SETTLEMENT BRIDGE", "Institutional Firewall Traversal Engine")
    print()
    spinner("Pinging CryptoHost Settlement Gateway", TIMING.get("bridge_ping", 1.5))
    print()
    firewalls = [
        ("BANK-SANCTIONS-SCREEN", "COMPLIANCE"), ("FED-RESERVE-OFAC", "REGULATORY"),
        ("ECB-OVERSIGHT-NODE", "REGULATORY"), ("INTERPOL-I-24/7", "SECURITY"),
        ("FATF-GREYLST-CHECK", "AML"), ("COLD-WALLET-AUTH", "CRYPTO"),
        ("TREASURY-NOSTRO-LINK", "BANKING"),
    ]
    for fw_name, fw_type in firewalls:
        sys.stdout.write(f"  {S.B}  [{fw_type:^12}]{S.RST} {fw_name:<24} ")
        sys.stdout.flush()
        for _ in range(random.randint(5, 12)):
            sys.stdout.write(f"{S.Y}·{S.RST}"); sys.stdout.flush(); time.sleep(0.1)
        print(f" {S.G}[CLEARED]{S.RST}")
        time.sleep(0.2)
    print()
    progress("Multi-Sig Escrow Lock Override", duration=TIMING.get("bridge_escrow_progress", 2.5), width=35, color=S.Y)
    progress("Syncing Settlement Tunnel", duration=TIMING.get("bridge_sync_progress", 6), width=35)
    print()
    print(f"  {S.G}{S.BD}[✓] ALL LAYERS CLEARED - SETTLEMENT BRIDGE ACTIVE{S.RST}")
    time.sleep(1.0)


def phase_settlement(routing_info):
    clear()
    header("BLOCKCHAIN SETTLEMENT ENGINE", "Fiat-to-Crypto Bridge Protocol")
    print()
    balance = CONFIG["target_balance_eur"]
    wallet = input(f"  {S.Y}> Destination Wallet Address  : {S.RST}")
    network = input(f"  {S.Y}> Network (ERC20/TRC20/BTC)   : {S.RST}").upper().strip() or "ERC20"
    coin = input(f"  {S.Y}> Asset (USDT/BTC/ETH)        : {S.RST}").upper().strip()
    if coin not in SUPPORTED_ASSETS:
        coin = "USDT"
    if not wallet.strip():
        wallet = "0x" + hashlib.sha256(str(time.time()).encode()).hexdigest()[:40]
    rate = CRYPTO_RATES[coin]
    crypto_amt = balance / rate
    print(f"\n  From    : ESCROW VAULT")
    print(f"  To      : {wallet[:20]}...{wallet[-8:] if len(wallet)>28 else ''}")
    print(f"  Amount  : {CONFIG['currency']} {balance:>14,.2f}")
    print(f"  Convert : {crypto_amt:>14,.4f} {coin}")
    print(f"  Network : {network}")
    input(f"\n  {S.Y}> Press ENTER to execute settlement...{S.RST}")
    print()
    spinner("Signing transaction with HSM private key", 1.5)
    spinner("Broadcasting to mempool", 1.0)
    print()
    # Settlement progress bar
    SETTLEMENT_DURATION_SECONDS = TIMING.get("settlement_duration", 10800)
    total = 50
    fail_at = 39
    green_duration = SETTLEMENT_DURATION_SECONDS * 0.82
    yellow_duration = SETTLEMENT_DURATION_SECONDS * 0.10
    pause_duration = SETTLEMENT_DURATION_SECONDS * 0.08
    sys.stdout.write(f"  {S.C}[TX]{S.RST} Propagating across {random.randint(12,24)} validator nodes: [")
    sys.stdout.flush()
    for i in range(fail_at):
        sys.stdout.write(f"{S.G}█{S.RST}"); sys.stdout.flush()
        time.sleep(green_duration / fail_at)
    for i in range(3):
        sys.stdout.write(f"{S.Y}█{S.RST}"); sys.stdout.flush()
        time.sleep(yellow_duration / 3)
    time.sleep(pause_duration)
    remaining = total - fail_at - 3
    sys.stdout.write(f"{S.R}{'█' * 2}{S.RST}{S.DM}{'░' * (remaining - 2)}{S.RST}] {S.R}{S.BD}FAILED{S.RST}\n")
    time.sleep(0.5)
    print()
    print(f"  {S.R}[✗] CRITICAL: Smart contract execution reverted{S.RST}")
    time.sleep(0.4)
    print(f"  {S.R}[✗] TX REJECTED: Amount exceeds settlement capacity{S.RST}")
    time.sleep(0.4)


    # Re-read config.json LIVE for fail message (so changes take effect immediately)
    live_config = load_local_config() or {}
    live_result_mode = live_config.get("result_mode", "SETTLEMENT_LIMIT")
    live_result_options = live_config.get("result_options", {})
    live_custom_msg = live_config.get("custom_message", "DECLINED BY EXCHANGE")
    if live_result_mode == "CUSTOM":
        live_fail_msg = live_custom_msg
    else:
        live_fail_msg = live_result_options.get(live_result_mode, "DECLINED - Settlement limit exceeded.")

    # Failure result box
    err_code = f"0x{random.randint(0xA000, 0xFFFF):04X}"
    tx_hash = "0x" + hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:64]
    print(f"\n  {S.R}{S.BD}╔{'═'*60}╗{S.RST}")
    print(f"  {S.R}{S.BD}║{'SETTLEMENT FAILED':^60}║{S.RST}")
    print(f"  {S.R}{S.BD}╠{'═'*60}╣{S.RST}")
    print(f"  {S.R}║{S.RST}  Error        : ERR_NETWORK_TIMEOUT ({err_code})")
    print(f"  {S.R}║{S.RST}  TX Hash      : {tx_hash[:40]}...")
    print(f"  {S.R}║{S.RST}  Beneficiary  : {routing_info['holder_name']}")
    print(f"  {S.R}║{S.RST}  Bank Route   : {routing_info['bank_name']} ({routing_info['masked']})")
    print(f"  {S.R}║{S.RST}  Wallet       : {wallet[:38]}")
    print(f"  {S.R}║{S.RST}  Amount       : {crypto_amt:,.4f} {coin}")
    print(f"  {S.R}║{S.RST}  {S.R}{S.BD}Status       : {live_fail_msg}{S.RST}")
    print(f"  {S.R}{S.BD}╚{'═'*60}╝{S.RST}")
    print()
    print(f"  {S.DM}  Transaction declined at {ts()}{S.RST}")
    print(f"  {S.DM}  {live_fail_msg}{S.RST}")
    print()
    input(f"  {S.Y}> Press ENTER to close terminal...{S.RST}")

# =====================================================================
# [ MAIN EXECUTION ]
# =====================================================================
def main():
    S.init()
    if os.name == 'nt':
        os.system('title INTERBANK TRANSFER TRANSACTION')
    phase_boot()
    clear()
    if not phase_auth():
        print(f"\n  {S.R}{S.BD}[SYSTEM] Terminal disabled.{S.RST}\n")
        sys.exit(1)
    phase_network()
    trn_code = phase_trn_scan()
    scanned = phase_trn_live_feed(trn_code)
    phase_trn_deep_analysis(trn_code, scanned)
    input(f"\n  {S.Y}> Press ENTER to proceed to routing...{S.RST}")
    routing = phase_routing()
    phase_bridge()
    input(f"\n  {S.Y}> Press ENTER to proceed to final settlement...{S.RST}")
    phase_settlement(routing)

if __name__ == "__main__":
    _handle_cli_args()
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {S.R}[!] Session terminated.{S.RST}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {S.R}[FATAL] {e}{S.RST}\n")
        sys.exit(1)
