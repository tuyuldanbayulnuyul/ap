#!/bin/bash
echo "============================================"
echo "  INTERBANK SETTLEMENT TERMINAL - Launcher"
echo "============================================"
echo ""
echo "[1] Start Desktop App (GUI)"
echo "[2] Start Web Panel (Config)"
echo "[3] Start Both"
echo ""
read -p "Select option: " choice

case $choice in
    1)
        echo "Starting GUI App..."
        python3 interbank_gui.py
        ;;
    2)
        echo "Starting Web Panel on http://127.0.0.1:5000"
        python3 web_panel.py
        ;;
    3)
        echo "Starting Web Panel..."
        python3 web_panel.py &
        sleep 2
        echo "Starting GUI App..."
        python3 interbank_gui.py
        ;;
    *)
        echo "Invalid option."
        ;;
esac
