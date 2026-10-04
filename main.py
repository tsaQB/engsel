from dotenv import load_dotenv

from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from app.client.engsel import (
    get_balance,
    get_tiering_info,
)
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil
from app.util import normalize_msisdn
from app.menus.sharing import show_balance_allotment_menu
from app.menus.family_hub import family_hub_menu
from app.menus.theme import render_main_menu_display, get_prompt_text
from app.menus.tui import (
    WIDTH,
    clear_screen,
    tui_pause,
    tui_input,
    tui_confirm,
    render_alert,
    format_msisdn,
    format_rupiah,
)

def show_main_menu(profile):
    clear_screen()
    render_main_menu_display(profile, width=WIDTH)

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            tokens = active_user.get("tokens", {})
            id_token = tokens.get("id_token")
            balance = get_balance(AuthInstance.api_key, id_token) if id_token else {}
            balance_remaining = balance.get("remaining", 0)
            balance_expired_at = balance.get("expired_at", 0)
            
            tier = 0
            current_point = 0
            point_info = "Points: N/A | Tier: N/A"
            
            if active_user.get("subscription_type") == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, tokens)
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user.get("number", ""),
                "subscriber_id": active_user.get("subscriber_id", ""),
                "subscription_type": active_user.get("subscription_type", "PREPAID"),
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "tier": tier,
                "points": current_point,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = input(get_prompt_text()).strip()
            choice_clean = choice.lower()
            choice_key = choice_clean.lstrip("0") if choice_clean not in ("0", "00") else choice_clean

            # Testing shortcuts
            if choice_key == "t":
                tui_pause()
            elif choice_key in ("1", "my", "pkg"):
                fetch_my_packages()
                continue
            elif choice_key in ("2", "hot2"):
                show_hot_menu2()
            elif choice_key == "3":
                family_code = tui_input("Family Code (atau '00' untuk batal)").strip()
                if family_code in ("00", "99", "0", "q", ""):
                    continue
                get_packages_by_family(family_code)
            elif choice_key == "4":
                is_enterprise = tui_confirm("Akses katalog segmen enterprise?", default=False)
                show_store_segments_menu(is_enterprise)
            elif choice_key == "5":
                is_enterprise = tui_confirm("Akses katalog paket enterprise?", default=False)
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice_key in ("6", "hot"):
                show_hot_menu()
            elif choice_key in ("7", "opt"):
                option_code = tui_input("Option Code paket (atau '00' untuk batal)").strip()
                if option_code in ("00", "99", "0", "q", ""):
                    continue
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice_key in ("8", "loop"):
                family_code = tui_input("Family Code (atau '00' untuk batal)").strip()
                if family_code in ("00", "99", "0", "q", ""):
                    continue

                start_from_str = tui_input("Mulai dari nomor opsi (default 1)", default="1").strip()
                try:
                    start_from_option = int(start_from_str)
                except ValueError:
                    start_from_option = 1

                use_decoy = tui_confirm("Gunakan paket decoy untuk bypass?", default=False)
                pause_on_success = tui_confirm("Jeda (pause) setiap kali pembelian sukses?", default=True)
                delay_str = tui_input("Jeda antar pembelian dalam detik (0 untuk tanpa jeda)", default="0").strip()
                try:
                    delay_seconds = int(delay_str)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
            elif choice_key == "9":
                is_enterprise = tui_confirm("Akses katalog enterprise?", default=False)
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice_key == "10":
                is_enterprise = tui_confirm("Akses katalog enterprise?", default=False)
                show_redeemables_menu(is_enterprise)
            elif choice_key in ("11", "fh"):
                family_hub_menu()
            elif choice_key in ("12", "akrab"):
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice_key in ("13", "circle"):
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice_key in ("14", "ba"):
                show_balance_allotment_menu()
            elif choice_key in ("s", "login", "acc", "15", "a"):
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                continue
            elif choice_key in ("h", "history", "16"):
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice_key in ("b", "bm", "00", "17"):
                show_bookmark_menu()
            elif choice_key in ("n", "18"):
                show_notification_menu()
            elif choice_key in ("v", "19"):
                raw_msisdn = tui_input("Nomor MSISDN yang ingin divalidasi (contoh: 08123456789)").strip()
                msisdn = normalize_msisdn(raw_msisdn)
                render_alert(f"Memvalidasi nomor {format_msisdn(msisdn)}...", level="info", width=WIDTH)
                res = validate_msisdn(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    msisdn,
                )
                if res.get("status", "").lower() == "success":
                    role = res.get("data", {}).get("family_plan_role", "NO_ROLE")
                    render_alert(f"Hasil Validasi: {format_msisdn(msisdn)} | Role: {role} | Status: VALID", level="success", width=WIDTH)
                else:
                    render_alert(f"Validasi gagal: {res.get('message', 'Nomor tidak valid')}", level="error", width=WIDTH)
                tui_pause()
            elif choice_key in ("r", "20"):
                raw_m = tui_input("Nomor MSISDN yang didaftarkan (contoh: 08123456789)").strip()
                msisdn = normalize_msisdn(raw_m)
                nik = tui_input("Nomor Induk Kependudukan (NIK 16 digit)").strip()
                kk = tui_input("Nomor Kartu Keluarga (KK 16 digit)").strip()
                
                render_alert("Mengirim data registrasi Dukcapil...", level="info", width=WIDTH)
                res = dukcapil(
                    AuthInstance.api_key,
                    msisdn,
                    kk,
                    nik,
                )
                if res.get("status", "").lower() == "success":
                    render_alert("Registrasi nomor berhasil diverifikasi oleh Dukcapil!", level="success", width=WIDTH)
                else:
                    err_code = res.get("code", "")
                    raw_msg = res.get("message", "")
                    if err_code == "164":
                        err_msg = "Error 164: Kartu SIM belum terpasang di HP / belum latch sinyal BTS, atau NIK telah melebihi kuota 3 nomor."
                    elif err_code == "213":
                        err_msg = "Error 213: Data NIK atau Nomor KK tidak ditemukan / tidak cocok di Dukcapil."
                    elif raw_msg:
                        err_msg = f"{raw_msg} (Kode: {err_code})"
                    else:
                        err_msg = f"Kode {err_code}: Data ditolak oleh operator atau verifikasi gagal."
                    render_alert(f"Registrasi gagal: {err_msg}", level="error", width=WIDTH)
                tui_pause()
            elif choice_key in ("99", "0", "q", "exit"):
                clear_screen()
                render_alert("Terima kasih telah menggunakan Engsel CLI TUI. Sampai jumpa!", level="info", width=WIDTH)
                sys.exit(0)
            elif choice_key == "sentry":
                enter_sentry_mode()
            else:
                render_alert("Pilihan menu tidak valid. Silakan pilih nomor atau kode yang tertera.", level="warning", width=WIDTH)
                tui_pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)

if __name__ == "__main__":
    try:
        need_update = check_for_updates()
        if need_update:
            tui_pause()

        main()
    except KeyboardInterrupt:
        clear_screen()
        sys.exit(0)
