from app.client.store.segments import get_segments
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
from app.service.auth import AuthInstance
from app.menus.package import show_package_details

def show_store_segments_menu(is_enterprise: bool = False):
    in_store_segments_menu = True
    while in_store_segments_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        clear_screen()
        render_alert("Mengambil data Store Segments dari server...", level="info", width=WIDTH)
        segments_res = get_segments(api_key, tokens, is_enterprise)
        if not segments_res:
            render_alert("Tidak ada segmen promo ditemukan.", level="warning", width=WIDTH)
            tui_pause()
            in_store_segments_menu = False
            continue
        
        segments = segments_res.get("data", {}).get("store_segments", [])
        if not segments:
            render_alert("Daftar segmen promo kosong.", level="info", width=WIDTH)
            tui_pause()
            in_store_segments_menu = False
            continue

        clear_screen()
        render_header("STORE SEGMENTS & PROMO", breadcrumb="engsel ❯ Promo ❯ Segments", width=WIDTH)
        print(render_hdr_line(f"KATEGORI PROMO ({len(segments)})", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        packages = {}
        for i, segment in enumerate(segments):
            name = segment.get("title", "Promo")
            banners = segment.get("banners", [])
            letter = chr(65 + i)  # 0 -> A, 1 -> B, etc.
            
            print(render_box_divider(title=f"BANNER {letter}: {name}", width=WIDTH))
            for j, banner in enumerate(banners, 1):
                discounted_price = banner.get("discounted_price", 0)
                price_str = format_rupiah(discounted_price)
                title = banner.get("title", "Paket")
                validity = banner.get("validity", "-")
                family_name = banner.get("family_name", "")
                
                code_key = f"{letter}{j}"
                packages[code_key.lower()] = {
                    "action_param": banner.get("action_param", ""),
                    "action_type": banner.get("action_type", "")
                }
                
                full_t = f"{family_name} - {title}".strip(" -")
                avail_t_w = (WIDTH - 2) - len(f"  [{code_key}] ") - len(price_str) - 2
                t_clean = truncate_str(full_t, avail_t_w)
                
                left_p = f"  [{code_key}] {t_clean}"
                rem = (WIDTH - 2) - len(left_p) - len(price_str) - 1
                row1 = bg_spaces(2) + badge(code_key, C_PRI) + bg_spaces(1) + C_WHI(t_clean) + bg_spaces(max(1, rem)) + C_AMB(price_str) + bg_spaces(1)
                print(p_line(row1, len(left_p) + max(1, rem) + len(price_str) + 1, width=WIDTH))
                
                row2_p = f"      Masa Aktif: {validity}"
                row2 = bg_spaces(6) + C_DIM(f"Masa Aktif: {validity}")
                print(p_line(row2, len(row2_p), width=WIDTH))
                
            print(render_empty_line(width=WIDTH))

        print(render_box_divider(title="OPSI", width=WIDTH))
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik kode paket (contoh: A1, B2)", width=WIDTH))
        print()

        choice = tui_input("Kode promo (contoh: A1)").strip()
        if choice in ("00", "q", "exit"):
            in_store_segments_menu = False
            continue
        
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            render_alert("Kode paket tidak valid. Masukkan kode seperti A1, B2.", level="warning", width=WIDTH)
            tui_pause()
            continue
        
        action_param = selected_pkg.get("action_param", "")
        action_type = selected_pkg.get("action_type", "")
        
        if action_type == "PDP":
            show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise
            )
        else:
            render_alert(f"Tipe aksi tidak didukung: {action_type} ({action_param})", level="info", width=WIDTH)
            tui_pause()
