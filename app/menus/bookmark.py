from app.menus.package import show_package_details
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
    tui_confirm,
    badge,
    truncate_str,
    C_PRI,
    C_WHI,
    C_MUT,
    C_DIM,
    C_DAN,
    C_AMB,
    p_line,
    bg_spaces,
)
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        bookmarks = BookmarkInstance.get_bookmarks()
        
        render_header("BOOKMARK PAKET", breadcrumb="engsel ❯ Bookmark", width=WIDTH)
        print(render_hdr_line("DAFTAR PAKET TERSIMPAN", width=WIDTH))
        print(render_empty_line(width=WIDTH))
        
        if not bookmarks or len(bookmarks) == 0:
            content_empty = bg_spaces(2) + C_MUT("Tidak ada paket yang disimpan di bookmark.")
            print(p_line(content_empty, len("  Tidak ada paket yang disimpan di bookmark."), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            tui_pause()
            return None
        
        for idx, bm in enumerate(bookmarks, start=1):
            k_badge = badge(str(idx), C_PRI)
            fam = bm.get("family_name", "")
            var = bm.get("variant_name", "")
            opt = bm.get("option_name", "")
            full_title = f"{fam} - {var} - {opt}".strip()
            
            # Truncate clean
            title_trunc = truncate_str(full_title, WIDTH - 12)
            content = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(title_trunc)
            plain_len = len(f"  [{idx:>2}] ") + len(title_trunc)
            print(p_line(content, plain_len, width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="PILIHAN AKSI", width=WIDTH))
        
        line_select = bg_spaces(2) + badge("1..N", C_PRI) + bg_spaces(1) + C_MUT("Ketik nomor paket untuk melihat detail & beli")
        print(p_line(line_select, len("  [1..N] Ketik nomor paket untuk melihat detail & beli"), width=WIDTH))
        
        line_del = bg_spaces(2) + badge("000", C_DAN) + bg_spaces(1) + C_DAN("Hapus Paket dari Bookmark")
        print(p_line(line_del, len("  [000] Hapus Paket dari Bookmark"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [ 00] Kembali ke Menu Utama"), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor/opsi", width=WIDTH))
        print()
        
        choice = tui_input("Pilihan bookmark").strip()
        
        if choice in ("00", "q", "exit"):
            in_bookmark_menu = False
            return None
        elif choice == "000":
            del_choice = tui_input("Nomor bookmark yang ingin dihapus").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                title_del = f"{del_bm.get('family_name', '')} - {del_bm.get('option_name', '')}"
                if tui_confirm(f"Hapus bookmark '{title_del}'?", default=True):
                    BookmarkInstance.remove_bookmark(
                        del_bm["family_code"],
                        del_bm["is_enterprise"],
                        del_bm["variant_name"],
                        del_bm["order"],
                    )
                    render_alert("Bookmark berhasil dihapus.", level="success", width=WIDTH)
                else:
                    render_alert("Penghapusan bookmark dibatalkan.", level="info", width=WIDTH)
                tui_pause()
            else:
                render_alert("Nomor bookmark tidak valid.", level="error", width=WIDTH)
                tui_pause()
            continue
        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            clear_screen()
            render_alert("Mengambil data paket dari server MyXL...", level="info", width=WIDTH)
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                render_alert("Gagal mengambil data family paket dari server.", level="error", width=WIDTH)
                tui_pause()
                continue
            
            package_variants = family_data.get("package_variants", [])
            option_code = None
            for variant in package_variants:
                if variant.get("name") == selected_bm.get("variant_name"):
                    selected_variant = variant
                    package_options = selected_variant.get("package_options", [])
                    for option in package_options:
                        if option.get("order") == selected_bm.get("order"):
                            selected_option = option
                            option_code = selected_option.get("package_option_code")
                            break
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                render_alert("Kode paket tidak ditemukan atau paket sudah tidak tersedia.", level="error", width=WIDTH)
                tui_pause()
        else:
            render_alert("Input tidak valid. Silakan coba lagi.", level="error", width=WIDTH)
            tui_pause()
            continue