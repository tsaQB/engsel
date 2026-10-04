"""
TUI (Terminal User Interface) Component Engine for Engsel CLI
UI/UX Pro Max certified terminal interface for Termux & Developer CLI.
Box Window Pane design (Lazygit / K9s style) with Charcoal/Slate dark interior.
Strict 56-column grid alignment, WCAG compliant contrast, and hybrid interactive navigation.
"""

import os
import sys
import re
import select
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Callable

# -------------------------------------------------------------
# Color & Typography (TrueColor Palette)
# -------------------------------------------------------------
BG_R, BG_G, BG_B = 24, 30, 40  # Dark Slate Interior Canvas

def style(fr: int, fg: int, fb: int, text: str, bold: bool = False) -> str:
    """Menggambar teks dengan warna foreground dan background solid terkunci tanpa \\033[0m di tengah."""
    b = "1;" if bold else ""
    return f"\033[{b}38;2;{fr};{fg};{fb};48;2;{BG_R};{BG_G};{BG_B}m{text}"

def bg_spaces(count: int) -> str:
    """Mengisi spasi dengan warna background canvas seragam."""
    return f"\033[48;2;{BG_R};{BG_G};{BG_B}m" + (" " * max(0, count))

# Standalone formatting helpers (for prompt, banners, outside container)
def rgb(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def bold_rgb(r: int, g: int, b: int, text: str) -> str:
    return f"\033[1;38;2;{r};{g};{b}m{text}\033[0m"

# Palet Semantik
PRIMARY    = lambda t: bold_rgb(56, 189, 248, t)   # Sapphire / Sky Blue (#38bdf8)
SECONDARY  = lambda t: bold_rgb(148, 163, 184, t)  # Slate Accent (#94a3b8)
SUCCESS    = lambda t: bold_rgb(52, 211, 153, t)   # Emerald Green (#34d399)
AMBER      = lambda t: bold_rgb(251, 191, 36, t)   # Warm Amber (#fbbf24)
DANGER     = lambda t: bold_rgb(248, 113, 113, t)  # Soft Red (#f87171)
PURPLE     = lambda t: bold_rgb(192, 132, 252, t)  # Light Purple (#c084fc)

TEXT_WHITE = lambda t: bold_rgb(248, 250, 252, t)  # Crisp White (#f8fafc)
TEXT_MUTED = lambda t: rgb(148, 163, 184, t)       # Muted Slate (#94a3b8)
TEXT_DIM   = lambda t: rgb(100, 116, 139, t)       # Dark Slate (#64748b)
BORDER     = lambda t: rgb(71, 85, 105, t)         # Slate Border (#475569)

# Interior Container Styler Functions (Locked Background)
C_PRI  = lambda t: style(56, 189, 248, t, True)
C_SEC  = lambda t: style(148, 163, 184, t, True)
C_SUC  = lambda t: style(52, 211, 153, t, True)
C_AMB  = lambda t: style(251, 191, 36, t, True)
C_DAN  = lambda t: style(248, 113, 113, t, True)
C_PUR  = lambda t: style(192, 132, 252, t, True)
C_WHI  = lambda t: style(248, 250, 252, t, True)
C_MUT  = lambda t: style(148, 163, 184, t, False)
C_DIM  = lambda t: style(100, 116, 139, t, False)
C_BOR  = lambda t: style(71, 85, 105, t, False)
C_END  = "\033[0m"

# Highlight bar for active cursor in menus (Inverted or brighter slate background)
H_BG_R, H_BG_G, H_BG_B = 40, 50, 68
def h_style(fr: int, fg: int, fb: int, text: str, bold: bool = True) -> str:
    b = "1;" if bold else ""
    return f"\033[{b}38;2;{fr};{fg};{fb};48;2;{H_BG_R};{H_BG_G};{H_BG_B}m{text}"

def h_bg_spaces(count: int) -> str:
    return f"\033[48;2;{H_BG_R};{H_BG_G};{H_BG_B}m" + (" " * max(0, count))

# -------------------------------------------------------------
# Terminal Layout & Length Calculation
# -------------------------------------------------------------
DEFAULT_WIDTH = 56

def get_terminal_width(fallback: int = DEFAULT_WIDTH) -> int:
    """Mengambil lebar terminal, dengan clamp aman untuk layar ponsel Termux."""
    try:
        cols = os.get_terminal_size().columns
        return max(50, min(cols, 60))
    except Exception:
        return fallback

WIDTH = DEFAULT_WIDTH

def clean_len(s: str) -> int:
    """Menghitung lebar visual string di terminal (mengabaikan kode warna ANSI)."""
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

def truncate_str(text: str, max_w: int, ellipsis: str = "…") -> str:
    """Pemotongan string berbasis visual width yang aman."""
    if clean_len(text) <= max_w:
        return text
    e_w = clean_len(ellipsis)
    target = max_w - e_w
    cur_w = 0
    res = []
    for ch in text:
        ch_w = 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1
        if cur_w + ch_w > target:
            break
        cur_w += ch_w
        res.append(ch)
    return "".join(res) + ellipsis

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def tui_pause(msg: str = "Tekan Enter untuk melanjutkan..."):
    print()
    try:
        input(TEXT_DIM(f"  [ {msg} ] "))
    except (KeyboardInterrupt, EOFError):
        pass

# -------------------------------------------------------------
# Box Pane Drawing Components (Lazygit / K9s Style)
# -------------------------------------------------------------
def p_line(content_str: str, plain_len: int, width: int = WIDTH) -> str:
    """Membungkus baris dalam border kiri dan kanan │ dengan padding latar canvas terkunci."""
    pad = max(0, (width - 2) - plain_len)
    return C_BOR("│") + content_str + bg_spaces(pad) + C_BOR("│") + C_END

def render_box_top(title: str = "", width: int = WIDTH) -> str:
    """Menggambar garis batas atas ┌──────┐ atau ┌─── [ Judul ] ───┐."""
    if isinstance(title, int):
        width = title
        title = ""
    if title:
        t_clean = f" {title} "
        t_len = len(t_clean)
        rem = width - 2 - t_len - 2
        left_d = 2
        right_d = max(0, rem)
        return BORDER("┌" + ("─" * left_d)) + PRIMARY(t_clean) + BORDER(("─" * right_d) + "┐")
    return BORDER("┌" + ("─" * (width - 2)) + "┐")

def render_box_bottom(footer: str = "", width: int = WIDTH) -> str:
    """Menggambar garis batas bawah └──────┘ atau └─── [ Footer ] ───┘."""
    if isinstance(footer, int):
        width = footer
        footer = ""
    if footer:
        f_clean = f" {footer} "
        f_len = len(f_clean)
        rem = width - 2 - f_len - 2
        left_d = 2
        right_d = max(0, rem)
        return BORDER("└" + ("─" * left_d)) + TEXT_DIM(f_clean) + BORDER(("─" * right_d) + "┘")
    return BORDER("└" + ("─" * (width - 2)) + "┘")

def render_box_divider(title: str = "", width: int = WIDTH) -> str:
    """Menggambar garis pembatas antar section ├──────┤."""
    if isinstance(title, int):
        width = title
        title = ""
    if title:
        t_clean = f" {title} "
        t_len = len(t_clean)
        rem = width - 2 - t_len - 2
        left_d = 2
        right_d = max(0, rem)
        return BORDER("├" + ("─" * left_d)) + PRIMARY(t_clean) + BORDER(("─" * right_d) + "┤")
    return BORDER("├" + ("─" * (width - 2)) + "┤")

def render_empty_line(width: int = WIDTH) -> str:
    """Baris kosong berlatar canvas di dalam box pane."""
    return p_line("", 0, width=width)

def render_hdr_line(title: str, width: int = WIDTH) -> str:
    """Header kategori di dalam container (contoh: ▸ PAKET HOT)."""
    content = bg_spaces(2) + C_PRI(f"▸ {title}")
    return p_line(content, 2 + len(f"▸ {title}"), width=width)

def render_subhdr_line(title: str, width: int = WIDTH) -> str:
    content = bg_spaces(2) + C_MUT(f"• {title}")
    return p_line(content, 2 + len(f"• {title}"), width=width)

# -------------------------------------------------------------
# Breadcrumb & Window Headers
# -------------------------------------------------------------
def render_header(title: str, breadcrumb: str = "engsel", width: int = WIDTH):
    """Menampilkan header jendela TUI dengan breadcrumb yang konsisten."""
    print(render_box_top(width=width))
    bc_str = f"  {breadcrumb} ❯ "
    content = bg_spaces(2) + C_DIM(f"{breadcrumb} ") + C_PRI("❯ ") + C_WHI(title)
    plain_len = len(bc_str) + len(title)
    print(p_line(content, plain_len, width=width))
    print(render_box_divider(width=width))

# -------------------------------------------------------------
# Card & Key-Value Components
# -------------------------------------------------------------
def render_kv_line(label: str, val: str, val_fn=C_WHI, width: int = WIDTH, lbl_w: int = 12) -> str:
    """Baris Key-Value tunggal di dalam panel box."""
    lbl_str = f"  {label:<{lbl_w}}: "
    val_clean = truncate_str(str(val), width - 4 - len(lbl_str))
    content = bg_spaces(2) + C_MUT(f"{label:<{lbl_w}}: ") + val_fn(val_clean)
    plain_len = len(lbl_str) + clean_len(val_clean)
    return p_line(content, plain_len, width=width)

def render_kv_2col(l_label: str, l_val: str, l_fn, r_label: str, r_val: str, r_fn, col2: int = 28, width: int = WIDTH, lbl_w: int = 8) -> str:
    """Baris Key-Value 2 kolom (contoh: Nomor & Pulsa)."""
    left_plain = f"  {l_label:<{lbl_w}}: {l_val}"
    pad = max(1, col2 - len(left_plain))
    right_plain = f"{r_label:<{lbl_w}}: {r_val}"

    content = (
        bg_spaces(2)
        + C_MUT(f"{l_label:<{lbl_w}}: ")
        + l_fn(str(l_val))
        + bg_spaces(pad)
        + C_MUT(f"{r_label:<{lbl_w}}: ")
        + r_fn(str(r_val))
    )
    plain_len = len(left_plain) + pad + len(right_plain)
    return p_line(content, plain_len, width=width)

# -------------------------------------------------------------
# Table Components
# -------------------------------------------------------------
def render_table_header(cols: List[Tuple[str, int]], width: int = WIDTH) -> str:
    """
    cols: [(title, col_width), ...]
    Total col_width harus <= width - 4
    """
    content = bg_spaces(2)
    plain = "  "
    for title, w in cols:
        t_fmt = f"{title:<{w}}"
        content += C_PRI(t_fmt)
        plain += t_fmt
    return p_line(content, len(plain), width=width)

def render_table_row(cols: List[Tuple[str, int, Any]], is_active: bool = False, width: int = WIDTH) -> str:
    """
    cols: [(text, col_width, color_fn), ...]
    """
    spc_fn = h_bg_spaces if is_active else bg_spaces
    content = spc_fn(2)
    plain = "  "
    for text, w, fn in cols:
        val_clean = truncate_str(str(text), w - 1)
        t_fmt = f"{val_clean:<{w}}"
        if is_active:
            content += h_style(248, 250, 252, t_fmt, True)
        else:
            content += fn(t_fmt)
        plain += t_fmt
    
    pad = max(0, (width - 2) - len(plain))
    if is_active:
        return C_PRI("▌") + content + spc_fn(pad) + C_PRI("▐") + C_END
    return C_BOR("│") + content + spc_fn(pad) + C_BOR("│") + C_END

# -------------------------------------------------------------
# Badges & Status Indicators
# -------------------------------------------------------------
def badge(text: str, fg_fn=C_PRI, is_active: bool = False) -> str:
    """Badge pill sederhana berbingkai [ text ]."""
    bor_fn = C_PRI if is_active else C_BOR
    return bor_fn("[") + fg_fn(text) + bor_fn("]")

def status_badge(status: str) -> str:
    s = str(status).upper()
    if s in ("SUCCESS", "BERHASIL", "AKTIF", "ACTIVE", "VERIFIED", "TERVERIFIKASI"):
        return C_SUC("✔ " + s)
    elif s in ("PENDING", "WAITING", "INVITED", "UNREAD"):
        return C_AMB("● " + s)
    elif s in ("FAILED", "GAGAL", "EXPIRED", "BLOCKED", "ERROR"):
        return C_DAN("✖ " + s)
    return C_MUT(s)

def format_rupiah(val) -> str:
    if val is None:
        return "Rp 0"
    try:
        v = int(val)
        return f"Rp {v:,}".replace(",", ".")
    except (ValueError, TypeError):
        return f"Rp {val}"

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

def format_quota_byte(quota_byte: int) -> str:
    try:
        b = int(quota_byte)
    except Exception:
        return str(quota_byte)
    GB = 1024 ** 3 
    MB = 1024 ** 2
    KB = 1024
    if b >= GB:
        return f"{b / GB:.2f} GB"
    elif b >= MB:
        return f"{b / MB:.2f} MB"
    elif b >= KB:
        return f"{b / KB:.2f} KB"
    else:
        return f"{b} B"

# -------------------------------------------------------------
# Alert & Banner Boxes
# -------------------------------------------------------------
def render_alert(message: str, level: str = "info", width: int = WIDTH):
    """Menampilkan kotak alert/notifikasi dengan warna semantik."""
    prefixes = {
        "success": ("✔ SUKSES", SUCCESS, C_SUC),
        "error":   ("✖ ERROR",  DANGER,  C_DAN),
        "warning": ("⚠ PERHATIAN", AMBER, C_AMB),
        "info":    ("ℹ INFO",   PRIMARY, C_PRI),
    }
    title, out_fn, in_fn = prefixes.get(level.lower(), prefixes["info"])
    
    # Bungkus pesan jika panjang
    words = message.split()
    lines = []
    cur = ""
    max_w = width - 6
    for w in words:
        if len(cur) + len(w) + 1 <= max_w:
            cur = f"{cur} {w}" if cur else w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    print(render_box_top(title=title, width=width))
    for l in lines:
        content = bg_spaces(2) + in_fn(l)
        print(p_line(content, 2 + len(l), width=width))
    print(render_box_bottom(width=width))

def render_progress(current: int, total: int, prefix: str = "Progress", width: int = WIDTH) -> str:
    """Menggambar visual progress bar terukur di dalam box."""
    if total <= 0:
        pct = 0
    else:
        pct = min(100, int((current / total) * 100))
    bar_w = 20
    filled = int((pct / 100) * bar_w)
    empty = bar_w - filled
    bar_str = "█" * filled + "░" * empty
    
    txt = f"  {prefix}: [{bar_str}] {pct}% ({current}/{total})"
    content = bg_spaces(2) + C_MUT(f"{prefix}: ") + C_PRI(f"[{bar_str}] ") + C_WHI(f"{pct}% ({current}/{total})")
    return p_line(content, len(txt), width=width)

# -------------------------------------------------------------
# Interactive Keyboard Handler (Raw Input)
# -------------------------------------------------------------
def get_single_key(timeout: Optional[float] = None) -> str:
    """
    Membaca single keypress atau escape sequence tanpa perlu menekan Enter.
    Mendukung Linux / Android Termux melalui termios & tty.
    Fallback ke readline jika bukan interactive tty.
    """
    if not sys.stdin.isatty():
        try:
            return sys.stdin.readline().strip()
        except Exception:
            return ""

    import termios, tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if timeout is not None:
            r, _, _ = select.select([sys.stdin], [], [], timeout)
            if not r:
                return ""
        ch = sys.stdin.read(1)
        if ch == "\x1b":  # Escape
            r, _, _ = select.select([sys.stdin], [], [], 0.05)
            if r:
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    r2, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if r2:
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A": return "UP"
                        if ch3 == "B": return "DOWN"
                        if ch3 == "C": return "RIGHT"
                        if ch3 == "D": return "LEFT"
                        return f"\x1b[{ch3}"
                return f"\x1b{ch2}"
            return "ESC"
        elif ch in ("\r", "\n"):
            return "ENTER"
        elif ch in ("\x7f", "\x08"):
            return "BACKSPACE"
        elif ch == "\x03":
            raise KeyboardInterrupt
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# -------------------------------------------------------------
# Unified TUI Prompt & Interactive Menus
# -------------------------------------------------------------
def get_prompt_text(context: str = "engsel") -> str:
    return PRIMARY(context) + " " + TEXT_DIM("❯") + " "

def tui_input(prompt_label: str = "Pilihan", default: str = "") -> str:
    """Prompt input yang seragam dan bersih."""
    d_str = f" [{default}]" if default else ""
    try:
        val = input(f"  {PRIMARY(prompt_label)}{TEXT_DIM(d_str)} {TEXT_DIM('❯')} ").strip()
        return val if val else default
    except (KeyboardInterrupt, EOFError):
        return "00"

def tui_confirm(question: str, default: bool = True) -> bool:
    """Dialog konfirmasi Yes / No yang rapi."""
    hint = "[Y/n]" if default else "[y/N]"
    ans = input(f"  {AMBER('?')} {TEXT_WHITE(question)} {TEXT_DIM(hint)}: ").strip().lower()
    if not ans:
        return default
    return ans in ("y", "ya", "yes", "1", "true")

def render_menu_item(key: str, title: str, is_active: bool = False, extra: str = "", danger: bool = False, pad_key: bool = True, width: int = WIDTH) -> str:
    """Menggambar 1 baris item menu di dalam box pane dengan indikator kursor aktif."""
    spc_fn = h_bg_spaces if is_active else bg_spaces
    cursor = "▶ " if is_active else "  "
    k_fmt = f"{key:>2}" if pad_key else key

    # Warna badge shortcut
    if danger:
        b_fn = C_DAN
    elif is_active:
        b_fn = C_WHI
    else:
        b_fn = C_PRI
    
    badge_str = C_BOR("[") + b_fn(k_fmt) + C_BOR("]")
    
    # Warna teks judul
    if danger:
        t_fn = C_DAN
    elif is_active:
        t_fn = C_WHI
    else:
        t_fn = C_MUT
        
    plain_left = f"{cursor}[{k_fmt}] {title}"
    content = spc_fn(1) + (C_PRI("▶") if is_active else bg_spaces(1)) + spc_fn(1) + badge_str + spc_fn(1) + t_fn(title)

    plain_extra = f" {extra}" if extra else ""
    rem = (width - 2) - len(plain_left) - len(plain_extra) - 1
    if rem < 1:
        # Potong title jika terlalu panjang
        max_title_w = (width - 2) - len(f"{cursor}[{k_fmt}] ") - len(plain_extra) - 2
        title_trunc = truncate_str(title, max_title_w)
        content = spc_fn(1) + (C_PRI("▶") if is_active else bg_spaces(1)) + spc_fn(1) + badge_str + spc_fn(1) + t_fn(title_trunc)
        plain_left = f"{cursor}[{k_fmt}] {title_trunc}"
        rem = max(1, (width - 2) - len(plain_left) - len(plain_extra) - 1)

    if extra:
        content += spc_fn(rem) + C_DIM(extra) + spc_fn(1)
    else:
        content += spc_fn(rem + 1)

    if is_active:
        return C_PRI("▌") + content + C_PRI("▐") + C_END
    return C_BOR("│") + content + C_BOR("│") + C_END

# -------------------------------------------------------------
# Interactive Selector Runner
# -------------------------------------------------------------
def run_interactive_menu(
    title: str,
    items: List[Dict[str, Any]],
    breadcrumb: str = "engsel",
    header_extra_renderer: Optional[Callable[[], None]] = None,
    width: int = WIDTH
) -> str:
    """
    TUI Selector Interaktif kelas Lazygit/K9s.
    Mendukung:
      - Navigasi tombol panah (↑ / ↓) atau (k / j)
      - Tekan Enter untuk memilih item yang disorot
      - Tekan langsung angka/huruf shortcut (1, 2, s, 00, dll.)
      - Mengetik perintah langsung jika diperlukan
    """
    if not sys.stdin.isatty():
        # Fallback jika berjalan di lingkungan non-interactive
        clear_screen()
        render_header(title, breadcrumb=breadcrumb, width=width)
        if header_extra_renderer:
            header_extra_renderer()
        for it in items:
            print(render_menu_item(it["key"], it["label"], is_active=False, extra=it.get("extra", ""), danger=it.get("danger", False), width=width))
        print(render_box_bottom(footer="Ketik nomor/shortcut", width=width))
        return tui_input("Pilihan").strip()

    active_idx = 0
    # Map shortcut keys for instant match
    shortcut_map = {str(it["key"]).strip().lower(): str(it["key"]) for it in items}

    buffer_chars = ""

    while True:
        clear_screen()
        render_header(title, breadcrumb=breadcrumb, width=width)
        if header_extra_renderer:
            header_extra_renderer()

        for idx, it in enumerate(items):
            is_active = (idx == active_idx)
            print(render_menu_item(
                key=str(it["key"]),
                title=str(it["label"]),
                is_active=is_active,
                extra=str(it.get("extra", "")),
                danger=bool(it.get("danger", False)),
                pad_key=bool(it.get("pad_key", True)),
                width=width
            ))

        footer_hint = "↑/↓: Pilih  Enter: Buka  00: Kembali"
        if buffer_chars:
            footer_hint = f"Input: {buffer_chars} (tekan Enter)"
        print(render_box_bottom(footer=footer_hint, width=width))

        key = get_single_key()

        if key in ("UP", "k"):
            active_idx = (active_idx - 1) % len(items)
            buffer_chars = ""
        elif key in ("DOWN", "j"):
            active_idx = (active_idx + 1) % len(items)
            buffer_chars = ""
        elif key == "ENTER":
            if buffer_chars:
                chosen = buffer_chars.strip().lower()
                buffer_chars = ""
                # Cek apakah cocok dengan shortcut
                for it in items:
                    if str(it["key"]).lower() == chosen:
                        return str(it["key"])
                return chosen
            else:
                return str(items[active_idx]["key"])
        elif key in ("ESC", "q"):
            return "00"
        elif key == "BACKSPACE":
            buffer_chars = buffer_chars[:-1]
        elif len(key) == 1 and key.isprintable():
            buffer_chars += key
            # Cek kecocokan langsung jika satu karakter unik
            low = buffer_chars.lower()
            exact_matches = [it for it in items if str(it["key"]).lower() == low]
            # Jika exact match dan tidak ada item lain yang dimulai dengan prefix ini
            prefix_matches = [it for it in items if str(it["key"]).lower().startswith(low)]
            if len(exact_matches) == 1 and len(prefix_matches) == 1:
                return str(exact_matches[0]["key"])
