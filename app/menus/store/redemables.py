from app.client.store.redeemables import get_redeemables
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
    p_line,
    bg_spaces,
)
from app.menus.package import show_package_details, get_packages_by_family
from datetime import datetime

def show_redeemables_menu(is_enterprise: bool = False):
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        clear_screen()
        render_alert("Mengambil data Redeemables dari server...", level="info", width=WIDTH)
        redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
        if not redeemables_res:
            render_alert("Tidak ada redeemables ditemukan.", level="warning", width=WIDTH)
            tui_pause()
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        if not categories:
            render_alert("Daftar kategori redeemables kosong.", level="info", width=WIDTH)
            tui_pause()
            in_redeemables_menu = False
            continue

        clear_screen()
        render_header("KATALOG REDEEMABLES", breadcrumb="engsel ❯ Store ❯ Redeem", width=WIDTH)
        print(render_hdr_line(f"KATEGORI REDEEMABLES ({len(categories)})", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        packages = {}
        for i, category in enumerate(categories):
            category_name = category.get("category_name", "Kategori")
            category_code = category.get("category_code", "-")
            redemables = category.get("redeemables", [])
            letter = chr(65 + i)
            
            print(render_box_divider(title=f"KATEGORI {letter}: {category_name}", width=WIDTH))
            if not redemables:
                row_e = bg_spaces(2) + C_MUT("Tidak ada item redeemable di kategori ini.")
                print(p_line(row_e, len("  Tidak ada item redeemable di kategori ini."), width=WIDTH))
            else:
                for j, redemable in enumerate(redemables, 1):
                    name = redemable.get("name", "Item")
                    valid_until = redemable.get("valid_until", 0)
                    try:
                        valid_until_date = datetime.fromtimestamp(valid_until).strftime("%d %b %Y")
                    except Exception:
                        valid_until_date = "-"
                    
                    code_key = f"{letter}{j}"
                    packages[code_key.lower()] = {
                        "action_param": redemable.get("action_param", ""),
                        "action_type": redemable.get("action_type", "")
                    }
                    
                    avail_w = (WIDTH - 2) - len(f"  [{code_key}] ") - 2
                    name_clean = truncate_str(name, avail_w)
                    
                    row1_p = f"  [{code_key}] {name_clean}"
                    row1 = bg_spaces(2) + badge(code_key, C_PRI) + bg_spaces(1) + C_WHI(name_clean)
                    print(p_line(row1, len(row1_p), width=WIDTH))
                    
                    row2_p = f"      Berlaku s/d: {valid_until_date}"
                    row2 = bg_spaces(6) + C_DIM(f"Berlaku s/d: {valid_until_date}")
                    print(p_line(row2, len(row2_p), width=WIDTH))
                    
            print(render_empty_line(width=WIDTH))

        print(render_box_divider(title="OPSI", width=WIDTH))
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik kode item (contoh: A1, B2)", width=WIDTH))
        print()

        choice = tui_input("Kode item (contoh: A1)").strip()
        if choice in ("00", "q", "exit"):
            in_redeemables_menu = False
            continue
        
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            render_alert("Kode item tidak valid. Masukkan kode seperti A1, B2.", level="warning", width=WIDTH)
            tui_pause()
            continue
        
        action_param = selected_pkg.get("action_param", "")
        action_type = selected_pkg.get("action_type", "")
        
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "")
        elif action_type == "PDP":
            show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise,
            )
        else:
            render_alert(f"Tipe aksi tidak didukung: {action_type} ({action_param})", level="info", width=WIDTH)
            tui_pause()
