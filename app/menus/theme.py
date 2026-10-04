"""
Theme & Styling Module for Engsel CLI
UI/UX Pro Max certified terminal interface for Termux & Developer CLI.
Box Window Pane design (Lazygit / K9s style) with Charcoal/Slate dark interior.
Strict 56-column 2-column grid alignment, WCAG compliant contrast.
"""

import os
import re
import unicodedata
from datetime import datetime

# -------------------------------------------------------------
# Color & Typography (TrueColor Palette)
# -------------------------------------------------------------
BG_R, BG_G, BG_B = 24, 30, 40  # Dark Slate Interior Canvas

def style(fr: int, fg: int, fb: int, text: str, bold: bool = False) -> str:
    """Menggambar teks dengan warna foreground dan background solid terkunci tanpa \\033[0m di tengah."""
    b = "1;" if bold else ""
    return f"\033[{b}38;2;{fr};{fg};{fb};48;2;{BG_R};{BG_G};{BG_B}m{text}"

def bg_spaces(count: int) -> str:
    return f"\033[48;2;{BG_R};{BG_G};{BG_B}m" + (" " * max(0, count))

# Standalone formatting helpers (for prompt, banners, outside container)
def rgb(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def bold_rgb(r: int, g: int, b: int, text: str) -> str:
    return f"\033[1;38;2;{r};{g};{b}m{text}\033[0m"

PRIMARY    = lambda t: bold_rgb(56, 189, 248, t)   # Sapphire / Sky Blue (#38bdf8)
SECONDARY  = lambda t: bold_rgb(148, 163, 184, t)  # Slate Accent (#94a3b8)
SUCCESS    = lambda t: bold_rgb(52, 211, 153, t)   # Emerald Green (#34d399)
AMBER      = lambda t: bold_rgb(251, 191, 36, t)   # Warm Amber (#fbbf24)
DANGER     = lambda t: bold_rgb(248, 113, 113, t)  # Soft Red (#f87171)

TEXT_WHITE = lambda t: bold_rgb(248, 250, 252, t)  # Crisp White (#f8fafc)
TEXT_MUTED = lambda t: rgb(148, 163, 184, t)       # Muted Slate (#94a3b8)
TEXT_DIM   = lambda t: rgb(100, 116, 139, t)       # Dark Slate (#64748b)
BORDER     = lambda t: rgb(71, 85, 105, t)         # Slate Border (#475569)

# Interior Container Styler Functions (Locked Background)
C_PRI  = lambda t: style(56, 189, 248, t, True)
C_SUC  = lambda t: style(52, 211, 153, t, True)
C_AMB  = lambda t: style(251, 191, 36, t, True)
C_DAN  = lambda t: style(248, 113, 113, t, True)
C_WHI  = lambda t: style(248, 250, 252, t, True)
C_MUT  = lambda t: style(148, 163, 184, t, False)
C_DIM  = lambda t: style(100, 116, 139, t, False)
C_BOR  = lambda t: style(71, 85, 105, t, False)
C_END  = "\033[0m"

# -------------------------------------------------------------
# Banner Option 2: Block Tech 3D
# -------------------------------------------------------------
BANNER_BLOCK_TECH = [
    "  ██████╗███╗   ██╗ ██████╗ ███████╗███████╗██╗     ",
    "  ██╔═══╝████╗  ██║██╔════╝ ██╔════╝██╔════╝██║     ",
    "  █████╗ ██╔██╗ ██║██║  ███╗███████╗█████╗  ██║     ",
    "  ██╔══╝ ██║╚██╗██║██║   ██║╚════██║██╔══╝  ██║     ",
    "  ██████╗██║ ╚████║╚██████╔╝███████║███████╗███████╗",
    "  ╚═════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝"
]

HIGHLIGHTS = {"1", "2", "6", "11", "S"}

def clean_len(s: str) -> int:
    """Menghitung lebar visual string di terminal (mengabaikan kode ANSI)."""
    clean = re.sub(r"\033\[[0-9;]*m", "", s)
    w = 0
    for ch in clean:
        if unicodedata.combining(ch):
            continue
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ("F", "W"):
            w += 2
        else:
            w += 1
    return w

def format_msisdn(msisdn) -> str:
    if not msisdn:
        return "-"
    s = str(msisdn).strip()
    if s.startswith("62"):
        s = "0" + s[2:]
    if len(s) == 12:
        return f"{s[:4]}-{s[4:8]}-{s[8:]}"
    elif len(s) == 11:
        return f"{s[:4]}-{s[4:7]}-{s[7:]}"
    elif len(s) == 13:
        return f"{s[:4]}-{s[4:8]}-{s[8:]}"
    return s

def format_rupiah(val) -> str:
    if val is None:
        return "Rp 0"
    try:
        v = int(val)
        return f"Rp {v:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"Rp {val}"

def render_banner(subtitle: str = "CLI Automation Suite for MyXL", width: int = 56):
    for line in BANNER_BLOCK_TECH:
        print(PRIMARY(line))
    sub_centered = subtitle + "  ·  v2.0"
    print(TEXT_DIM(sub_centered.center(width)))
    print()

def p_line(content_str: str, plain_len: int, width: int = 56) -> str:
    """Membungkus baris dalam border kiri dan kanan │ dengan padding latar abu-abu."""
    pad = max(0, (width - 2) - plain_len)
    return C_BOR("│") + content_str + bg_spaces(pad) + C_BOR("│") + C_END

def render_card_row(l_label: str, l_val: str, l_val_fn, r_label: str, r_val: str, r_val_fn, col2: int = 28, width: int = 56) -> str:
    left_plain = f"  {l_label:<8}: {l_val}"
    pad = max(1, col2 - len(left_plain))
    right_plain = f"{r_label:<8}: {r_val}"
    
    content = (
        bg_spaces(2)
        + C_MUT(f"{l_label:<8}: ")
        + l_val_fn(l_val)
        + bg_spaces(pad)
        + C_MUT(f"{r_label:<8}: ")
        + r_val_fn(r_val)
    )
    plain_len = len(left_plain) + pad + len(right_plain)
    return p_line(content, plain_len, width=width)

def render_menu_row(k1: str, t1: str, k2: str, t2: str, col1_w: int = 28, pad_key: bool = True, width: int = 56) -> str:
    hi1 = k1 in HIGHLIGHTS
    hi2 = k2 in HIGHLIGHTS
    c1 = C_WHI(t1) if hi1 else C_MUT(t1)
    c2 = C_WHI(t2) if hi2 else C_MUT(t2)

    k1_fmt = f"{k1:>2}" if pad_key else k1
    k2_fmt = f"{k2:>2}" if pad_key else k2
    b1 = C_BOR("[") + C_PRI(k1_fmt) + C_BOR("]")
    b2 = C_BOR("[") + C_PRI(k2_fmt) + C_BOR("]")

    plain_left = f"  [{k1_fmt}] {t1}"
    pad = max(1, col1_w - len(plain_left))

    content = bg_spaces(2) + b1 + bg_spaces(1) + c1 + bg_spaces(pad) + b2 + bg_spaces(1) + c2
    plain_total = len(plain_left) + pad + len(f"[{k2_fmt}] {t2}")
    return p_line(content, plain_total, width=width)

def render_hdr_line(title: str, width: int = 56) -> str:
    content = bg_spaces(2) + C_PRI(f"▸ {title}")
    return p_line(content, 2 + len(f"▸ {title}"), width=width)

def render_main_menu_display(profile: dict, width: int = 56):
    # 1. Header Banner
    render_banner(width=width)

    # 2. Extract Data Akun
    msisdn_formatted = format_msisdn(profile.get("number", ""))
    balance_formatted = format_rupiah(profile.get("balance", 0))
    
    sub_type = profile.get("subscription_type", "PREPAID")
    sub_label = "Prabayar" if sub_type == "PREPAID" else sub_type

    expired_at = profile.get("balance_expired_at")
    if expired_at:
        try:
            expired_str = datetime.fromtimestamp(expired_at).strftime("%Y-%m-%d")
        except Exception:
            expired_str = str(expired_at)
    else:
        expired_str = "-"

    # Point & Tier info (Ringkas: "Classic (25)" agar pas rapi dan tidak meluap)
    tier = profile.get("tier")
    points = profile.get("points")
    if tier is not None and points is not None:
        tier_names = {0: "Classic", 1: "Silver", 2: "Gold", 3: "Platinum", 4: "Diamond"}
        t_name = tier_names.get(tier, f"Tier {tier}")
        tier_info = f"{t_name} ({points})"
    else:
        tier_info = "Classic (0)"

    # 3. Top Border Panel Box
    print(BORDER("┌" + ("─" * (width - 2)) + "┐"))

    # 4. Account Profile Card
    print(render_card_row("Nomor", msisdn_formatted, C_WHI, "Pulsa", balance_formatted, C_AMB, col2=28, width=width))
    print(render_card_row("Tipe", sub_label, C_MUT, "Tier", tier_info, C_WHI, col2=28, width=width))
    print(render_card_row("Status", "Terverifikasi", C_SUC, "Expired", expired_str, C_DIM, col2=28, width=width))

    # Divider antar Profil & Menu
    print(BORDER("├" + ("─" * (width - 2)) + "┤"))

    # Section 1: Paket & Pembelian (1 - 10)
    print(render_hdr_line("PAKET & PEMBELIAN", width=width))
    print(render_menu_row("1", "Lihat Paket Saya", "6", "Beli Paket HOT", col1_w=28, width=width))
    print(render_menu_row("2", "Beli Paket HOT-2", "7", "Beli Option Code", col1_w=28, width=width))
    print(render_menu_row("3", "Beli Family Code", "8", "Beli Borongan (Loop)", col1_w=28, width=width))
    print(render_menu_row("4", "Store Segments", "9", "Store Family List", col1_w=28, width=width))
    print(render_menu_row("5", "Store Packages", "10", "Redeemables", col1_w=28, width=width))
    print(p_line("", 0, width=width))

    # Section 2: Kuota Bersama & Sharing (11 - 14)
    print(render_hdr_line("KUOTA BERSAMA & SHARING", width=width))
    print(render_menu_row("11", "Family Hub (Akrab)", "13", "Circle Group", col1_w=28, width=width))
    print(render_menu_row("12", "Akrab Organizer", "14", "Transfer Pulsa", col1_w=28, width=width))
    print(p_line("", 0, width=width))

    # Section 3: Akun & Utilitas (S, H, B, N, V, R)
    print(render_hdr_line("AKUN & SISTEM", width=width))
    print(render_menu_row("S", "Ganti Akun / Switch", "H", "Riwayat Transaksi", col1_w=28, pad_key=False, width=width))
    print(render_menu_row("B", "Bookmark Paket", "N", "Pusat Notifikasi", col1_w=28, pad_key=False, width=width))
    print(render_menu_row("V", "Validasi Nomor", "R", "Registrasi Dukcapil", col1_w=28, pad_key=False, width=width))
    print(p_line("", 0, width=width))

    # Exit Option
    exit_c = bg_spaces(2) + C_BOR("[") + C_DAN("99") + C_BOR("]") + bg_spaces(1) + C_DAN("Tutup Aplikasi") + bg_spaces(1) + C_DIM("(atau tekan 0)")
    plain_exit = len("  [99] Tutup Aplikasi (atau tekan 0)")
    print(p_line(exit_c, plain_exit, width=width))

    # Bottom Border Panel Box
    print(BORDER("└" + ("─" * (width - 2)) + "┘"))
    print()

def get_prompt_text() -> str:
    return PRIMARY("engsel") + " " + TEXT_DIM("❯") + " "
