from datetime import datetime, timedelta

from app.client.engsel import get_transaction_history
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
    tui_input,
    badge,
    status_badge,
    format_rupiah,
    truncate_str,
    C_PRI,
    C_WHI,
    C_MUT,
    C_DIM,
    C_AMB,
    C_DAN,
    p_line,
    bg_spaces,
)

def show_transaction_history(api_key, tokens):
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        render_header("RIWAYAT TRANSAKSI", breadcrumb="engsel ❯ Transaksi", width=WIDTH)
        
        history = []
        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", []) if data else []
        except Exception as e:
            render_alert(f"Gagal mengambil riwayat transaksi: {e}", level="error", width=WIDTH)
            history = []
        
        print(render_hdr_line("DAFTAR TRANSAKSI TERAKHIR", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        if len(history) == 0:
            content_empty = bg_spaces(2) + C_MUT("Tidak ada data riwayat transaksi.")
            print(p_line(content_empty, len("  Tidak ada data riwayat transaksi."), width=WIDTH))
        else:
            for idx, transaction in enumerate(history, start=1):
                transaction_timestamp = transaction.get("timestamp", 0)
                try:
                    dt = datetime.fromtimestamp(transaction_timestamp)
                    dt_jakarta = dt - timedelta(hours=7)
                    formatted_time = dt_jakarta.strftime("%d %b %Y, %H:%M WIB")
                except Exception:
                    formatted_time = str(transaction_timestamp)

                title = transaction.get("title", "Transaksi")
                price = format_rupiah(transaction.get("price", 0))
                pay_method = transaction.get("payment_method_label", "-")
                status = str(transaction.get("status", "-")).upper()
                pay_status = str(transaction.get("payment_status", "-")).upper()

                # Baris 1: [Idx] Title  (kanan: Price)
                k_badge = badge(str(idx), C_PRI)
                price_str = f" {price}"
                avail_title_w = (WIDTH - 2) - len(f"  [{idx:>2}] ") - len(price_str) - 2
                title_clean = truncate_str(title, avail_title_w)
                
                left_p = f"  [{idx:>2}] {title_clean}"
                rem1 = (WIDTH - 2) - len(left_p) - len(price_str) - 1
                row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(title_clean) + bg_spaces(max(1, rem1)) + C_AMB(price) + bg_spaces(1)
                print(p_line(row1, len(left_p) + max(1, rem1) + len(price_str) + 1, width=WIDTH))

                # Baris 2: Waktu & Metode
                line2_plain = f"      {formatted_time} • {pay_method}"
                line2_clean = truncate_str(line2_plain, WIDTH - 4)
                row2 = bg_spaces(6) + C_DIM(line2_clean[6:])
                print(p_line(row2, len(line2_clean), width=WIDTH))

                # Baris 3: Status
                stat_badge_str = status_badge(status)
                pay_stat_badge_str = status_badge(pay_status)
                plain_stat = f"      Status: {status} | Pembayaran: {pay_status}"
                row3 = bg_spaces(6) + C_MUT("Status: ") + stat_badge_str + C_MUT(" | ") + pay_stat_badge_str
                print(p_line(row3, len(plain_stat), width=WIDTH))

                if idx < len(history):
                    print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        
        line_ref = bg_spaces(2) + badge("0", C_PRI) + bg_spaces(1) + C_WHI("Refresh Data Transaksi")
        print(p_line(line_ref, len("  [ 0] Refresh Data Transaksi"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih opsi", width=WIDTH))
        print()

        choice = tui_input("Pilihan riwayat").strip()
        if choice == "0":
            continue
        elif choice in ("00", "q", "exit"):
            in_transaction_menu = False
        else:
            render_alert("Opsi tidak valid. Silakan pilih 0 atau 00.", level="warning", width=WIDTH)
            tui_pause()