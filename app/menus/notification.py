from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
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

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        render_header("PUSAT NOTIFIKASI", breadcrumb="engsel ❯ Notifikasi", width=WIDTH)
        
        notifications_res = dashboard_segments(api_key, tokens)
        if not notifications_res:
            render_alert("Tidak ada data notifikasi ditemukan dari server.", level="info", width=WIDTH)
            tui_pause()
            return
        
        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            render_alert("Kotak masuk notifikasi Anda kosong.", level="info", width=WIDTH)
            tui_pause()
            return

        unread_count = sum(1 for n in notifications if not n.get("is_read", False))
        
        # Summary Header
        summary_txt = f"Total: {len(notifications)} Pesan | Belum Dibaca: {unread_count}"
        print(render_hdr_line(summary_txt, width=WIDTH))
        print(render_empty_line(width=WIDTH))

        for idx, notification in enumerate(notifications, start=1):
            is_read = notification.get("is_read", False)
            brief = notification.get("brief_message", "").strip() or "Pemberitahuan"
            full = notification.get("full_message", "").strip()
            time_str = notification.get("timestamp", "-")

            k_badge = badge(str(idx), C_PRI)
            stat_badge = C_DIM("[SUDAH DIBACA]") if is_read else C_AMB("[BARU]")
            
            # Baris 1: [No] [BARU/DIBACA] Judul
            avail_w = (WIDTH - 2) - len(f"  [{idx:>2}] ") - len(" [BARU] ") - 2
            brief_trunc = truncate_str(brief, avail_w)
            row1_p = f"  [{idx:>2}] " + ("[BARU] " if not is_read else "[DIBACA] ") + brief_trunc
            content1 = bg_spaces(2) + k_badge + bg_spaces(1) + stat_badge + bg_spaces(1) + (C_WHI(brief_trunc) if not is_read else C_MUT(brief_trunc))
            print(p_line(content1, len(row1_p), width=WIDTH))

            # Baris 2: Waktu
            row2_p = f"      Waktu: {time_str}"
            content2 = bg_spaces(6) + C_DIM(f"Waktu: {time_str}")
            print(p_line(content2, len(row2_p), width=WIDTH))

            # Baris 3: Pesan lengkap (dipotong rapi jika melebihi lebar)
            if full and full != brief:
                full_trunc = truncate_str(full, WIDTH - 10)
                row3_p = f"      {full_trunc}"
                content3 = bg_spaces(6) + C_MUT(full_trunc)
                print(p_line(content3, len(row3_p), width=WIDTH))

            if idx < len(notifications):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        
        line_read = bg_spaces(2) + badge("1", C_SUC) + bg_spaces(1) + C_WHI("Tandai Semua Notifikasi Sudah Dibaca")
        print(p_line(line_read, len("  [ 1] Tandai Semua Notifikasi Sudah Dibaca"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih opsi", width=WIDTH))
        print()

        choice = tui_input("Pilihan notifikasi").strip()
        if choice == "1":
            marked = 0
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    marked += 1
            render_alert(f"{marked} notifikasi berhasil ditandai sebagai sudah dibaca.", level="success", width=WIDTH)
            tui_pause()
        elif choice in ("00", "q", "exit"):
            in_notification_menu = False
        else:
            render_alert("Pilihan tidak valid. Silakan coba lagi.", level="warning", width=WIDTH)
            tui_pause()
