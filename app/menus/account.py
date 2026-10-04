from app.client.ciam import get_otp, submit_otp
from app.menus.tui import (
    WIDTH,
    clear_screen,
    tui_pause,
    render_header,
    render_box_top,
    render_box_bottom,
    render_box_divider,
    render_hdr_line,
    render_empty_line,
    render_alert,
    tui_input,
    tui_confirm,
    badge,
    status_badge,
    format_msisdn,
    C_PRI,
    C_WHI,
    C_MUT,
    C_DIM,
    C_SUC,
    C_DAN,
    C_AMB,
    p_line,
    bg_spaces,
)
from app.service.auth import AuthInstance
from app.util import normalize_msisdn

def show_login_menu():
    clear_screen()
    render_header("LOGIN MYXL", breadcrumb="engsel ❯ Akun", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    
    line1 = bg_spaces(2) + badge("1", C_PRI) + bg_spaces(1) + C_WHI("Request OTP")
    print(p_line(line1, len("  [ 1] Request OTP"), width=WIDTH))
    
    line2 = bg_spaces(2) + badge("2", C_PRI) + bg_spaces(1) + C_MUT("Submit OTP")
    print(p_line(line2, len("  [ 2] Submit OTP"), width=WIDTH))
    
    line_exit = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali")
    print(p_line(line_exit, len("  [00] Kembali"), width=WIDTH))
    
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(footer="Pilih opsi", width=WIDTH))

def login_prompt(api_key: str):
    clear_screen()
    render_header("LOGIN MYXL", breadcrumb="engsel ❯ Login", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    
    line_info = bg_spaces(2) + C_MUT("Masukkan nomor XL Anda (contoh: 081234567890)")
    print(p_line(line_info, len("  Masukkan nomor XL Anda (contoh: 081234567890)"), width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    print()
    
    phone_number = tui_input("Nomor XL").strip()
    if not phone_number or phone_number in ("00", "0", "q"):
        return None, None
        
    phone_number = normalize_msisdn(phone_number)

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        render_alert("Nomor tidak valid! Pastikan nomor diawali 08/628 dan panjangnya sesuai.", level="error", width=WIDTH)
        tui_pause()
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            render_alert("Gagal mengirim OTP ke nomor tersebut. Silakan coba lagi.", level="error", width=WIDTH)
            tui_pause()
            return None, None
            
        render_alert(f"OTP berhasil dikirim via SMS ke {format_msisdn(phone_number)}", level="success", width=WIDTH)
        
        try_count = 5
        while try_count > 0:
            print()
            render_alert(f"Sisa kesempatan memasukkan OTP: {try_count} kali", level="warning" if try_count <= 2 else "info", width=WIDTH)
            otp = tui_input("Kode OTP (6 digit)").strip()
            
            if otp in ("00", "q"):
                render_alert("Proses login dibatalkan oleh pengguna.", level="warning", width=WIDTH)
                tui_pause()
                return None, None
                
            if not otp.isdigit() or len(otp) != 6:
                render_alert("OTP tidak valid! Harus berupa 6 digit angka.", level="error", width=WIDTH)
                continue
            
            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if not tokens:
                render_alert("Kode OTP salah atau telah kedaluwarsa. Silakan coba lagi.", level="error", width=WIDTH)
                try_count -= 1
                continue
            
            render_alert(f"Login berhasil untuk nomor {format_msisdn(phone_number)}!", level="success", width=WIDTH)
            tui_pause()
            return phone_number, tokens["refresh_token"]

        render_alert("Gagal login setelah 5 percobaan. Silakan coba lagi nanti.", level="error", width=WIDTH)
        tui_pause()
        return None, None
    except Exception as e:
        render_alert(f"Terjadi kesalahan saat login: {e}", level="error", width=WIDTH)
        tui_pause()
        return None, None

def show_account_menu():
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
        
    in_account_menu = True
    add_user = False
    
    while in_account_menu:
        clear_screen()
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                render_alert("Gagal menambah akun baru.", level="warning", width=WIDTH)
                tui_pause()
                if add_user:
                    add_user = False
                continue
            
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            
            if add_user:
                add_user = False
            continue
        
        # 1. Header Box Panel
        render_header("MANAJEMEN AKUN", breadcrumb="engsel ❯ Akun", width=WIDTH)
        
        # 2. Section: Daftar Akun
        print(render_hdr_line("DAFTAR AKUN TERSIMPAN", width=WIDTH))
        print(render_empty_line(width=WIDTH))
        
        if not users or len(users) == 0:
            content_empty = bg_spaces(2) + C_MUT("Belum ada akun XL yang tersimpan.")
            print(p_line(content_empty, len("  Belum ada akun XL yang tersimpan."), width=WIDTH))
        else:
            for idx, user in enumerate(users, start=1):
                is_active = active_user and user["number"] == active_user["number"]
                
                # Format nomor rapi
                num_raw = str(user.get("number", ""))
                num_fmt = format_msisdn(num_raw)
                
                # Tipe langganan
                sub_type = str(user.get("subscription_type", "PREPAID"))
                sub_label = "Prabayar" if sub_type == "PREPAID" else ("Pascabayar" if sub_type == "POSTPAID" else sub_type)
                
                k_badge = badge(str(idx), C_WHI if is_active else C_PRI)
                num_col = C_WHI(f"{num_fmt:<14}") if is_active else C_MUT(f"{num_fmt:<14}")
                type_col = C_DIM(f"[{sub_label:<10}]")
                
                if is_active:
                    status_col = C_SUC("✔ AKTIF")
                    plain_row = f"  [{idx:>2}] {num_fmt:<14} [{sub_label:<10}] ✔ AKTIF"
                else:
                    status_col = bg_spaces(7)
                    plain_row = f"  [{idx:>2}] {num_fmt:<14} [{sub_label:<10}]        "
                
                content = bg_spaces(2) + k_badge + bg_spaces(1) + num_col + bg_spaces(1) + type_col + bg_spaces(1) + status_col
                print(p_line(content, len(plain_row), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="AKSI & PERINTAH", width=WIDTH))
        
        # Section Aksi
        line_add = bg_spaces(2) + badge("0", C_SUC) + bg_spaces(1) + C_WHI("Tambah Akun Baru (Login)")
        print(p_line(line_add, len("  [ 0] Tambah Akun Baru (Login)"), width=WIDTH))
        
        line_switch = bg_spaces(2) + badge("1..N", C_PRI) + bg_spaces(1) + C_MUT("Ketik nomor urut untuk ganti akun aktif")
        print(p_line(line_switch, len("  [1..N] Ketik nomor urut untuk ganti akun aktif"), width=WIDTH))
        
        line_del = bg_spaces(2) + badge("del N", C_DAN) + bg_spaces(1) + C_DAN("Hapus akun tertentu (contoh: del 2)")
        print(p_line(line_del, len("  [del N] Hapus akun tertentu (contoh: del 2)"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor/perintah", width=WIDTH))
        print()
        
        input_str = tui_input("Pilihan").strip()
        
        if input_str in ("00", "q", "exit"):
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            render_alert(f"Beralih ke akun {format_msisdn(selected_user['number'])}...", level="success", width=WIDTH)
            return selected_user["number"]
        elif input_str.startswith("del ") or input_str.startswith("del"):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])
                
                if 1 <= del_index <= len(users):
                    user_to_delete = users[del_index - 1]
                    
                    # Cegah menghapus akun yang sedang aktif
                    if active_user and user_to_delete["number"] == active_user["number"]:
                        render_alert("Tidak dapat menghapus akun yang sedang aktif! Silakan beralih ke akun lain terlebih dahulu.", level="error", width=WIDTH)
                        tui_pause()
                        continue
                    
                    if tui_confirm(f"Yakin ingin menghapus akun {format_msisdn(user_to_delete['number'])}?", default=False):
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        render_alert(f"Akun {format_msisdn(user_to_delete['number'])} berhasil dihapus.", level="success", width=WIDTH)
                    else:
                        render_alert("Penghapusan akun dibatalkan.", level="info", width=WIDTH)
                    tui_pause()
                else:
                    render_alert(f"Nomor urut tidak valid (1-{len(users)}).", level="error", width=WIDTH)
                    tui_pause()
            else:
                render_alert("Format salah! Gunakan: del <nomor urut> (contoh: del 2)", level="warning", width=WIDTH)
                tui_pause()
            continue
        else:
            render_alert("Pilihan atau perintah tidak valid. Silakan coba lagi.", level="error", width=WIDTH)
            tui_pause()
            continue