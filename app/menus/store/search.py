from app.client.store.search import get_family_list, get_store_packages
from app.menus.package import get_packages_by_family, show_package_details
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

def show_family_list_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    in_family_list_menu = True
    while in_family_list_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        clear_screen()
        render_alert("Mengambil daftar Family Paket dari Store...", level="info", width=WIDTH)
        family_list_res = get_family_list(api_key, tokens, subs_type, is_enterprise)
        if not family_list_res:
            render_alert("Tidak ada daftar family ditemukan.", level="warning", width=WIDTH)
            tui_pause()
            in_family_list_menu = False
            continue
        
        family_list = family_list_res.get("data", {}).get("results", [])
        if not family_list:
            render_alert("Daftar family paket kosong.", level="info", width=WIDTH)
            tui_pause()
            in_family_list_menu = False
            continue

        clear_screen()
        render_header("DAFTAR FAMILY PAKET", breadcrumb="engsel ❯ Store ❯ Family", width=WIDTH)
        print(render_hdr_line(f"KATALOG FAMILY ({len(family_list)})", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        for i, family in enumerate(family_list, 1):
            f_name = family.get("label", "Family")
            f_code = family.get("id", "-")
            
            avail_w = (WIDTH - 2) - len(f"  [{i:>2}] ") - 2
            name_clean = truncate_str(f_name, avail_w)
            
            row1_p = f"  [{i:>2}] {name_clean}"
            row1 = bg_spaces(2) + badge(str(i), C_PRI) + bg_spaces(1) + C_WHI(name_clean)
            print(p_line(row1, len(row1_p), width=WIDTH))
            
            row2_p = f"      Kode: {f_code}"
            row2 = bg_spaces(6) + C_DIM(f"Kode: {f_code}")
            print(p_line(row2, len(row2_p), width=WIDTH))

            if i < len(family_list):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor family (1..N)", width=WIDTH))
        print()

        choice = tui_input("Pilih family (nomor)").strip()
        if choice in ("00", "q", "exit"):
            in_family_list_menu = False
            continue
        
        if choice.isdigit() and 1 <= int(choice) <= len(family_list):
            selected_family = family_list[int(choice) - 1]
            family_code = selected_family.get("id", "")
            get_packages_by_family(family_code)
        else:
            render_alert("Nomor pilihan tidak valid.", level="warning", width=WIDTH)
            tui_pause()

def show_store_packages_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    in_store_packages_menu = True
    while in_store_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        clear_screen()
        render_alert("Mengambil daftar paket Store dari server...", level="info", width=WIDTH)
        store_packages_res = get_store_packages(api_key, tokens, subs_type, is_enterprise)
        if not store_packages_res:
            render_alert("Tidak ada paket store ditemukan.", level="warning", width=WIDTH)
            tui_pause()
            in_store_packages_menu = False
            continue
        
        store_packages = store_packages_res.get("data", {}).get("results_price_only", [])
        if not store_packages:
            render_alert("Daftar paket store kosong.", level="info", width=WIDTH)
            tui_pause()
            in_store_packages_menu = False
            continue

        clear_screen()
        render_header("KATALOG PAKET STORE", breadcrumb="engsel ❯ Store ❯ Paket", width=WIDTH)
        print(render_hdr_line(f"DAFTAR PAKET ({len(store_packages)})", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        packages = {}
        for i, package in enumerate(store_packages, 1):
            title = package.get("title", "Paket")
            orig = package.get("original_price", 0)
            disc = package.get("discounted_price", 0)
            price = disc if disc > 0 else orig
            price_str = format_rupiah(price)
            validity = package.get("validity", "-")
            family_name = package.get("family_name", "")
            
            packages[str(i)] = {
                "action_type": package.get("action_type", ""),
                "action_param": package.get("action_param", "")
            }
            
            avail_w = (WIDTH - 2) - len(f"  [{i:>2}] ") - len(price_str) - 2
            title_clean = truncate_str(title, avail_w)
            
            left_p = f"  [{i:>2}] {title_clean}"
            rem = (WIDTH - 2) - len(left_p) - len(price_str) - 1
            row1 = bg_spaces(2) + badge(str(i), C_PRI) + bg_spaces(1) + C_WHI(title_clean) + bg_spaces(max(1, rem)) + C_AMB(price_str) + bg_spaces(1)
            print(p_line(row1, len(left_p) + max(1, rem) + len(price_str) + 1, width=WIDTH))

            fam_str = f"Family: {family_name} • Masa Aktif: {validity}" if family_name else f"Masa Aktif: {validity}"
            fam_clean = truncate_str(fam_str, WIDTH - 8)
            row2 = bg_spaces(6) + C_DIM(fam_clean)
            print(p_line(row2, len(f"      {fam_clean}"), width=WIDTH))

            if i < len(store_packages):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor paket (1..N)", width=WIDTH))
        print()

        choice = tui_input("Pilih paket (nomor)").strip()
        if choice in ("00", "q", "exit"):
            in_store_packages_menu = False
            continue
        elif choice in packages:
            selected_package = packages[choice]
            action_type = selected_package["action_type"]
            action_param = selected_package["action_param"]
            
            if action_type == "PDP":
                show_package_details(api_key, tokens, action_param, is_enterprise)
            else:
                render_alert(f"Tipe aksi tidak didukung: {action_type} ({action_param})", level="info", width=WIDTH)
                tui_pause()
        else:
            render_alert("Nomor paket tidak valid.", level="warning", width=WIDTH)
            tui_pause()