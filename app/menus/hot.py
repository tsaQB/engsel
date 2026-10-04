import json

from app.client.engsel import get_family, get_package_details
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
    render_kv_line,
    render_kv_2col,
    tui_input,
    tui_confirm,
    badge,
    format_rupiah,
    format_quota_byte,
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
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.util import display_html

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        render_header("PAKET HOT", breadcrumb="engsel ❯ Promo", width=WIDTH)
        print(render_hdr_line("DAFTAR REKOMENDASI PAKET HOT", width=WIDTH))
        print(render_empty_line(width=WIDTH))
        
        hot_packages = []
        try:
            with open("hot_data/hot.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            render_alert(f"Gagal memuat file hot_data/hot.json: {e}", level="error", width=WIDTH)
            tui_pause()
            return None

        for idx, p in enumerate(hot_packages, start=1):
            k_badge = badge(str(idx), C_PRI)
            fam = p.get("family_name", "")
            var = p.get("variant_name", "")
            opt = p.get("option_name", "")
            title = f"{fam} - {var} - {opt}".strip()
            title_clean = truncate_str(title, WIDTH - 12)
            
            content = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(title_clean)
            plain_len = len(f"  [{idx:>2}] ") + len(title_clean)
            print(p_line(content, plain_len, width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor paket (1..N)", width=WIDTH))
        print()
        
        choice = tui_input("Pilih paket (nomor)").strip()
        if choice in ("00", "q", "exit"):
            in_hot_menu = False
            return None
            
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            clear_screen()
            render_alert("Mengambil data detail paket dari server...", level="info", width=WIDTH)
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                render_alert("Gagal mengambil data family paket.", level="error", width=WIDTH)
                tui_pause()
                continue
            
            package_variants = family_data.get("package_variants", [])
            option_code = None
            for variant in package_variants:
                if variant.get("name") == selected_bm.get("variant_name"):
                    package_options = variant.get("package_options", [])
                    for option in package_options:
                        if option.get("order") == selected_bm.get("order"):
                            option_code = option.get("package_option_code")
                            break
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                render_alert("Kode opsi paket tidak ditemukan.", level="error", width=WIDTH)
                tui_pause()
        else:
            render_alert("Input tidak valid. Silakan masukkan nomor urut yang benar.", level="error", width=WIDTH)
            tui_pause()
            continue

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        render_header("PAKET HOT 2 (COMBO)", breadcrumb="engsel ❯ Promo 2", width=WIDTH)
        print(render_hdr_line("DAFTAR PAKET COMBO SPESIAL", width=WIDTH))
        print(render_empty_line(width=WIDTH))
        
        hot_packages = []
        try:
            with open("hot_data/hot2.json", "r", encoding="utf-8") as f:
                hot_packages = json.load(f)
        except Exception as e:
            render_alert(f"Gagal memuat file hot_data/hot2.json: {e}", level="error", width=WIDTH)
            tui_pause()
            return None

        for idx, p in enumerate(hot_packages, start=1):
            k_badge = badge(str(idx), C_PRI)
            name = p.get("name", "Paket")
            price_raw = p.get("price", 0)
            price_str = format_rupiah(price_raw)
            
            # Baris 1: [Idx] Name   Price
            avail_name_w = (WIDTH - 2) - len(f"  [{idx:>2}] ") - len(price_str) - 2
            name_trunc = truncate_str(name, avail_name_w)
            
            left_p = f"  [{idx:>2}] {name_trunc}"
            rem1 = (WIDTH - 2) - len(left_p) - len(price_str) - 1
            row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(name_trunc) + bg_spaces(max(1, rem1)) + C_AMB(price_str) + bg_spaces(1)
            print(p_line(row1, len(left_p) + max(1, rem1) + len(price_str) + 1, width=WIDTH))
            
            # Detail singkat jika ada
            detail_str = p.get("detail", "").strip()
            if detail_str:
                det_trunc = truncate_str(detail_str, WIDTH - 8)
                row_det = bg_spaces(6) + C_DIM(det_trunc)
                print(p_line(row_det, len(f"      {det_trunc}"), width=WIDTH))
            
            if idx < len(hot_packages):
                print(render_empty_line(width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="OPSI", width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih paket (1..N)", width=WIDTH))
        print()
        
        choice = tui_input("Pilih paket (nomor)").strip()
        if choice in ("00", "q", "exit"):
            in_hot_menu = False
            return None
            
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                render_alert("Paket tidak memiliki rincian sub-paket.", level="error", width=WIDTH)
                tui_pause()
                continue
            
            clear_screen()
            render_alert("Mengambil rincian sub-paket dari server...", level="info", width=WIDTH)
            
            payment_items = []
            main_package_detail = None
            fetch_failed = False
            
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )
                
                if package == packages[0]:
                    main_package_detail = package_detail
                
                if not package_detail:
                    render_alert(f"Gagal mengambil detail paket untuk {package.get('family_code')}.", level="error", width=WIDTH)
                    tui_pause()
                    fetch_failed = True
                    break
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            if fetch_failed or not main_package_detail:
                continue
            
            # Tampilkan kartu rincian TUI
            clear_screen()
            render_header("DETAIL PAKET HOT 2", breadcrumb="engsel ❯ Hot 2 ❯ Detail", width=WIDTH)
            
            pkg_opt = main_package_detail.get("package_option", {})
            pkg_fam = main_package_detail.get("package_family", {})
            
            price_val = pkg_opt.get("price", 0)
            validity_val = pkg_opt.get("validity", "-")
            points_val = pkg_opt.get("point", 0)
            plan_type_val = pkg_fam.get("plan_type", "PREPAID")
            
            print(render_hdr_line("INFORMASI UTAMA", width=WIDTH))
            print(render_kv_line("Nama Paket", selected_package.get("name", ""), C_WHI, width=WIDTH))
            print(render_kv_2col("Harga", format_rupiah(price_val), C_AMB, "Masa Aktif", validity_val, C_WHI, col2=28, width=WIDTH))
            print(render_kv_2col("Poin", f"{points_val} Pts", C_PRI, "Tipe Plan", plan_type_val, C_MUT, col2=28, width=WIDTH))
            print(render_empty_line(width=WIDTH))
            
            # Benefits
            benefits = pkg_opt.get("benefits", [])
            if benefits and isinstance(benefits, list):
                print(render_box_divider(title="BENEFIT & KUOTA", width=WIDTH))
                for b in benefits:
                    b_name = b.get("name", "Benefit")
                    d_type = b.get("data_type", "")
                    total = b.get("total", 0)
                    
                    if d_type == "VOICE" and total > 0:
                        val_str = f"{total / 60:.0f} Menit"
                    elif d_type == "TEXT" and total > 0:
                        val_str = f"{total} SMS"
                    elif d_type == "DATA" and total > 0:
                        val_str = format_quota_byte(total)
                    else:
                        val_str = f"{total} ({d_type})" if total > 0 else "-"
                    
                    if b.get("is_unlimited", False):
                        val_str += " (Unlimited)"
                    
                    print(render_kv_line(truncate_str(b_name, 18), val_str, C_SUC, width=WIDTH, lbl_w=18))
                print(render_empty_line(width=WIDTH))

            # Menu Pembayaran
            print(render_box_divider(title="METODE PEMBAYARAN", width=WIDTH))
            
            line_bal = bg_spaces(2) + badge("1", C_PRI) + bg_spaces(1) + C_WHI("Beli dengan Pulsa (Balance)")
            print(p_line(line_bal, len("  [ 1] Beli dengan Pulsa (Balance)"), width=WIDTH))
            
            line_ewal = bg_spaces(2) + badge("2", C_PRI) + bg_spaces(1) + C_WHI("Beli dengan E-Wallet (GoPay/OVO/ShopeePay)")
            print(p_line(line_ewal, len("  [ 2] Beli dengan E-Wallet (GoPay/OVO/ShopeePay)"), width=WIDTH))
            
            line_qris = bg_spaces(2) + badge("3", C_PRI) + bg_spaces(1) + C_WHI("Bayar dengan QRIS")
            print(p_line(line_qris, len("  [ 3] Bayar dengan QRIS"), width=WIDTH))
            
            line_back_pay = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Daftar Paket")
            print(p_line(line_back_pay, len("  [00] Kembali ke Daftar Paket"), width=WIDTH))
            
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(footer="Pilih metode bayar", width=WIDTH))
            print()
            
            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            input_method = tui_input("Metode pembayaran").strip()
            if input_method == "1":
                if overwrite_amount == -1:
                    last_price = payment_items[-1]["item_price"]
                    if not tui_confirm(f"Pastikan sisa pulsa KURANG DARI Rp{last_price} jika ingin memanfaatkan trik decoy. Lanjutkan?", default=False):
                        render_alert("Pembelian dibatalkan oleh pengguna.", level="info", width=WIDTH)
                        tui_pause()
                        continue

                settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    payment_for,
                    ask_overwrite,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=token_confirmation_idx,
                    amount_idx=amount_idx,
                )
                tui_pause()
            elif input_method == "2":
                show_multipayment(
                    api_key,
                    tokens,
                    payment_items,
                    payment_for,
                    ask_overwrite,
                    overwrite_amount,
                    token_confirmation_idx,
                    amount_idx,
                )
                tui_pause()
            elif input_method == "3":
                show_qris_payment(
                    api_key,
                    tokens,
                    payment_items,
                    payment_for,
                    ask_overwrite,
                    overwrite_amount,
                    token_confirmation_idx,
                    amount_idx,
                )
                tui_pause()
            elif input_method in ("00", "q", "exit"):
                continue
            else:
                render_alert("Metode pembayaran tidak valid.", level="error", width=WIDTH)
                tui_pause()
        else:
            render_alert("Input tidak valid. Silakan coba lagi.", level="error", width=WIDTH)
            tui_pause()
