from app.client.engsel import get_package, send_api_request
from app.menus.tui import (
    WIDTH,
    clear_screen,
    tui_pause,
    render_header,
    render_box_bottom,
    render_box_divider,
    render_hdr_line,
    render_empty_line,
    render_alert,
    render_kv_line,
    render_kv_2col,
    status_badge,
    format_quota_byte,
    truncate_str,
    C_PRI,
    C_WHI,
    C_MUT,
    C_DIM,
    C_AMB,
    C_DAN,
    C_SUC,
    p_line,
    bg_spaces,
)
import json
from datetime import datetime
from app.service.auth import AuthInstance
from time import sleep
import threading
import sys
import os

def enter_sentry_mode():
    api_key = AuthInstance.api_key
    active_user = AuthInstance.get_active_user()
    if active_user is None:
        render_alert("Sesi login tidak aktif. Silakan login terlebih dahulu.", level="error", width=WIDTH)
        tui_pause()
        return
    
    tokens = active_user.get("tokens", {})
    id_token = tokens.get("id_token")

    if not os.path.exists("sentry"):
        os.makedirs("sentry")

    file_name = os.path.join(
        "sentry",
        f"sentry_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )

    stop_flag = {"stop": False}

    def listen_for_quit():
        while True:
            try:
                user_input = sys.stdin.readline()
                if not user_input:
                    continue
                if user_input.strip().lower() in ("q", "exit", "quit"):
                    stop_flag["stop"] = True
                    break
            except Exception:
                break

    listener_thread = threading.Thread(target=listen_for_quit, daemon=True)
    listener_thread.start()

    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    clear_screen()
    render_header("SENTRY MODE: LIVE MONITOR", breadcrumb="engsel ❯ Sentry", width=WIDTH)
    print(render_hdr_line("STATUS MONITORING KUOTA", width=WIDTH))
    print(render_kv_line("File Log", file_name, C_AMB, width=WIDTH))
    print(render_kv_2col("Interval", "1 Detik", C_PRI, "Status", status_badge("RUNNING"), C_SUC, col2=28, width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_divider(title="PETUNJUK KELUAR", width=WIDTH))
    row_hint = bg_spaces(2) + C_MUT("Tekan ") + C_DAN("Ctrl+C") + C_MUT(" atau ketik ") + C_PRI("'q' + Enter") + C_MUT(" untuk berhenti.")
    print(p_line(row_hint, len("  Tekan Ctrl+C atau ketik 'q' + Enter untuk berhenti."), width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(footer="Monitoring berjalan secara realtime", width=WIDTH))
    print()

    count = 0
    try:
        with open(file_name, 'a') as f:
            while not stop_flag["stop"]:
                sleep(1)
                count += 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                try:
                    sys.stdout.write(f"\r\033[38;2;56;189;248m[Sentry]\033[0m Snapshot #{count} at \033[38;2;251;191;36m{timestamp}\033[0m... ")
                    sys.stdout.flush()
                    
                    res = send_api_request(api_key, path, payload, id_token, "POST")
                    if res.get("status") != "SUCCESS":
                        print(f"\n\033[38;2;248;113;113mGagal mengambil data kuota:\033[0m {res}")
                        tui_pause()
                        return None
                    
                    quotas = res.get("data", {}).get("quotas", [])
                    data_point = {
                        "time": timestamp,
                        "quotas": quotas
                    }

                    f.write(json.dumps(data_point) + "\n")
                    f.flush()
                except Exception as e:
                    print(f"\n\033[38;2;248;113;113mError fetch snapshot:\033[0m {e}")
                    continue

    except KeyboardInterrupt:
        pass
    finally:
        print()
        render_alert(f"Sentry Mode dihentikan. Total {count} snapshot tersimpan di {file_name}.", level="success", width=WIDTH)
        tui_pause()
