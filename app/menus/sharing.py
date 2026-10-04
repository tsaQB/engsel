import json

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
    render_kv_line,
    tui_input,
    tui_confirm,
    format_rupiah,
    format_msisdn,
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
from app.client.engsel import get_balance
from app.client.sharing import balance_allotment
from app.client.ciam import get_auth_code
from app.util import normalize_msisdn

def show_balance_allotment_menu():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        render_alert("Silakan login terlebih dahulu untuk transfer pulsa.", level="error", width=WIDTH)
        tui_pause()
        return None
        
    clear_screen()
    render_header("TRANSFER PULSA", breadcrumb="engsel ❯ Sharing", width=WIDTH)
    
    balance_res = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
    balance_remaining = balance_res.get("remaining", 0) if balance_res else 0
    balance_fmt = format_rupiah(balance_remaining)
    sender_fmt = format_msisdn(active_user.get("number", ""))

    print(render_hdr_line("INFORMASI PENGIRIM", width=WIDTH))
    print(render_kv_line("Nomor Anda", sender_fmt, C_WHI, width=WIDTH))
    print(render_kv_line("Sisa Pulsa", balance_fmt, C_AMB, width=WIDTH))
    print(render_empty_line(width=WIDTH))
    
    info_line = bg_spaces(2) + C_MUT("Catatan: Pastikan Anda sudah mengatur PIN di MyXL.")
    print(p_line(info_line, len("  Catatan: Pastikan Anda sudah mengatur PIN di MyXL."), width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    print()
    
    pin = tui_input("PIN Transaksi (6 digit)").strip()
    if pin in ("00", "q", ""):
        return None
        
    if len(pin) != 6 or not pin.isdigit():
        render_alert("Format PIN tidak valid! Harus berupa 6 digit angka.", level="error", width=WIDTH)
        tui_pause()
        return None
    
    render_alert("Memvalidasi PIN & otentikasi transaksi...", level="info", width=WIDTH)
    stage_token = get_auth_code(
        active_user["tokens"],
        pin,
        active_user["number"]
    )
    
    if stage_token is None:
        render_alert("Gagal mendapatkan kode otentikasi. Pastikan PIN Anda benar.", level="error", width=WIDTH)
        tui_pause()
        return None
    
    receiver_input = tui_input("Nomor Penerima (contoh: 08123456789)").strip()
    if not receiver_input or receiver_input in ("00", "q"):
        return None
    receiver_msisdn = normalize_msisdn(receiver_input)
    
    amount_str = tui_input("Nominal Transfer (contoh: 5000)").strip()
    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        render_alert("Nominal transfer tidak valid! Masukkan angka lebih dari 0.", level="error", width=WIDTH)
        tui_pause()
        return None
    
    # Konfirmasi TUI
    clear_screen()
    render_header("KONFIRMASI TRANSFER", breadcrumb="engsel ❯ Konfirmasi", width=WIDTH)
    print(render_hdr_line("RINCIAN TRANSAKSI", width=WIDTH))
    print(render_kv_line("Penerima", format_msisdn(receiver_msisdn), C_WHI, width=WIDTH))
    print(render_kv_line("Nominal", format_rupiah(amount), C_AMB, width=WIDTH))
    print(render_kv_line("Sisa Nanti", format_rupiah(balance_remaining - amount), C_MUT, width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    print()
    
    if not tui_confirm("Lanjutkan proses transfer pulsa ini?", default=False):
        render_alert("Transfer pulsa dibatalkan oleh pengguna.", level="info", width=WIDTH)
        tui_pause()
        return None
    
    render_alert("Mengirim permintaan transfer pulsa ke server...", level="info", width=WIDTH)
    res = balance_allotment(
        AuthInstance.api_key,
        active_user["tokens"],
        stage_token,
        receiver_msisdn,
        amount,
    )
    
    if res is None:
        render_alert("Transfer pulsa gagal diproses oleh server.", level="error", width=WIDTH)
    else:
        render_alert(f"Transfer pulsa {format_rupiah(amount)} ke {format_msisdn(receiver_msisdn)} berhasil dikirim!", level="success", width=WIDTH)
    
    tui_pause()
    return res
