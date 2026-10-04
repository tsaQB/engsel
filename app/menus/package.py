import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request, unsubscribe
from app.client.ciam import get_auth_code
from app.service.bookmark import BookmarkInstance
from app.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
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
    render_progress,
    tui_input,
    tui_confirm,
    badge,
    status_badge,
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
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.service.decoy import DecoyInstance
from app.menus.util import display_html

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "") if active_user else ""
    
    clear_screen()
    render_alert("Mengambil data detail paket dari server MyXL...", level="info", width=WIDTH)
    package = get_package(api_key, tokens, package_option_code)
    if not package:
        render_alert("Gagal memuat data detail paket dari server.", level="error", width=WIDTH)
        tui_pause()
        return False

    price = package.get("package_option", {}).get("price", 0)
    detail_raw = package.get("package_option", {}).get("tnc", "")
    detail = display_html(detail_raw)
    validity = package.get("package_option", {}).get("validity", "-")

    option_name = package.get("package_option", {}).get("name", "")
    family_name = package.get("package_family", {}).get("name", "")
    variant_name = package.get("package_detail_variant", {}).get("name", "")
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    family_code = package.get("package_family", {}).get("package_family_code", "")
    parent_code = package.get("package_addon", {}).get("parent_code", "")
    if parent_code == "":
        parent_code = "N/A"
    
    token_confirmation = package.get("token_confirmation", "")
    ts_to_sign = package.get("timestamp", "")
    payment_for = package.get("package_family", {}).get("payment_for", "")
    if payment_for == "":
        payment_for = "BUY_PACKAGE"
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]

    clear_screen()
    render_header("DETAIL PAKET", breadcrumb="engsel ❯ Paket ❯ Detail", width=WIDTH)
    
    # 1. Informasi Utama
    print(render_hdr_line("INFORMASI PAKET", width=WIDTH))
    print(render_kv_line("Nama Paket", title, C_WHI, width=WIDTH))
    print(render_kv_2col("Harga", format_rupiah(price), C_AMB, "Masa Aktif", validity, C_WHI, col2=28, width=WIDTH))
    
    points_val = package.get("package_option", {}).get("point", 0)
    plan_type_val = package.get("package_family", {}).get("plan_type", "PREPAID")
    print(render_kv_2col("Poin", f"{points_val} Pts", C_PRI, "Plan Type", plan_type_val, C_MUT, col2=28, width=WIDTH))
    print(render_kv_2col("Family", family_code, C_DIM, "Parent", parent_code, C_DIM, col2=28, width=WIDTH))
    print(render_empty_line(width=WIDTH))

    # 2. Benefit & Kuota
    benefits = package.get("package_option", {}).get("benefits", [])
    if benefits and isinstance(benefits, list):
        print(render_box_divider(title="BENEFIT & KUOTA", width=WIDTH))
        for benefit in benefits:
            b_name = benefit.get("name", "Benefit")
            data_type = benefit.get("data_type", "")
            total = benefit.get("total", 0)

            if data_type == "VOICE" and total > 0:
                val_str = f"{total / 60:.0f} Menit"
            elif data_type == "TEXT" and total > 0:
                val_str = f"{total} SMS"
            elif data_type == "DATA" and total > 0:
                val_str = format_quota_byte(total)
            else:
                val_str = f"{total} ({data_type})" if total > 0 else "-"

            if benefit.get("is_unlimited", False):
                val_str += " (Unlimited)"

            print(render_kv_line(truncate_str(b_name, 18), val_str, C_SUC, width=WIDTH, lbl_w=18))
        print(render_empty_line(width=WIDTH))

    # 3. Addons
    addons = get_addons(api_key, tokens, package_option_code)
    bonuses = addons.get("bonuses", []) if addons else []
    if bonuses and len(bonuses) > 0:
        print(render_box_divider(title="BONUS & ADDON TERSEDIA", width=WIDTH))
        for idx_b, b in enumerate(bonuses[:3], 1):
            b_label = b.get("name", "Bonus")
            print(render_kv_line(f"Bonus #{idx_b}", truncate_str(b_label, 26), C_AMB, width=WIDTH, lbl_w=10))
        print(render_empty_line(width=WIDTH))

    # 4. SnK ringkas
    if detail:
        clean_snk = detail.replace("\n", " ").strip()
        if len(clean_snk) > 10:
            print(render_box_divider(title="SYARAT & KETENTUAN", width=WIDTH))
            snk_snip = truncate_str(clean_snk, WIDTH - 8)
            row_snk = bg_spaces(2) + C_DIM(snk_snip)
            print(p_line(row_snk, 2 + len(snk_snip), width=WIDTH))
            print(render_empty_line(width=WIDTH))

    in_package_detail_menu = True
    while in_package_detail_menu:
        print(render_box_divider(title="PILIHAN METODE & AKSI", width=WIDTH))
        
        m_items = [
            ("1", "Beli dengan Pulsa (Balance)", C_PRI),
            ("2", "Beli dengan E-Wallet (GoPay/ShopeePay/OVO)", C_PRI),
            ("3", "Bayar dengan QRIS", C_PRI),
            ("4", "Pulsa + Decoy (Bypass Kuota/Harga)", C_MUT),
            ("5", "Pulsa + Decoy V2 (Bypass Token)", C_MUT),
            ("6", "QRIS + Decoy (+1K)", C_MUT),
            ("7", "QRIS + Decoy (Rp 0)", C_MUT),
            ("8", "Pulsa N Kali (Loop Pembelian)", C_MUT),
        ]

        for k, lbl, fn in m_items:
            row_m = bg_spaces(2) + badge(k, fn) + bg_spaces(1) + C_WHI(lbl)
            print(p_line(row_m, len(f"  [{k:>2}] {lbl}"), width=WIDTH))

        if payment_for == "REDEEM_VOUCHER":
            print(p_line(bg_spaces(2) + badge("B", C_SUC) + bg_spaces(1) + C_SUC("Ambil sebagai Bonus Voucher"), len("  [ B] Ambil sebagai Bonus Voucher"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("BA", C_SUC) + bg_spaces(1) + C_SUC("Kirim Bonus ke Nomor Lain"), len("  [BA] Kirim Bonus ke Nomor Lain"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("L", C_AMB) + bg_spaces(1) + C_AMB("Beli dengan Poin Loyalty"), len("  [ L] Beli dengan Poin Loyalty"), width=WIDTH))

        if option_order != -1:
            print(p_line(bg_spaces(2) + badge("0", C_SUC) + bg_spaces(1) + C_WHI("Simpan ke Bookmark"), len("  [ 0] Simpan ke Bookmark"), width=WIDTH))

        line_exit = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Daftar Paket")
        print(p_line(line_exit, len("  [00] Kembali ke Daftar Paket"), width=WIDTH))
        
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih aksi pembayaran", width=WIDTH))
        print()

        choice = tui_input("Metode/Aksi").strip()
        if choice in ("00", "q", "exit"):
            return False
        elif choice == "0" and option_order != -1:
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code", ""),
                family_name=package.get("package_family", {}).get("name", ""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                render_alert("Paket berhasil ditambahkan ke daftar bookmark!", level="success", width=WIDTH)
            else:
                render_alert("Paket ini sudah ada di dalam bookmark Anda.", level="warning", width=WIDTH)
            tui_pause()
            continue
        elif choice == "1":
            settlement_balance(api_key, tokens, payment_items, payment_for, True)
            render_alert("Permintaan pembelian telah dikirim. Silakan cek aplikasi MyXL.", level="info", width=WIDTH)
            tui_pause()
            return True
        elif choice == "2":
            show_multipayment(api_key, tokens, payment_items, payment_for, True)
            render_alert("Selesaikan pembayaran di e-wallet pilihan Anda.", level="info", width=WIDTH)
            tui_pause()
            return True
        elif choice == "3":
            show_qris_payment(api_key, tokens, payment_items, payment_for, True)
            render_alert("Silakan scan QRIS untuk menyelesaikan pembayaran.", level="info", width=WIDTH)
            tui_pause()
            return True
        elif choice == "4":
            decoy = DecoyInstance.get_decoy("balance")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                render_alert("Gagal memuat rincian paket decoy.", level="error", width=WIDTH)
                tui_pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    render_alert(f"Menyesuaikan total amount ke: {format_rupiah(valid_amount)}", level="info", width=WIDTH)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        render_alert("Pembelian dengan decoy berhasil!", level="success", width=WIDTH)
            else:
                render_alert("Pembelian dengan decoy berhasil!", level="success", width=WIDTH)
            tui_pause()
            return True
        elif choice == "5":
            decoy = DecoyInstance.get_decoy("balance")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                render_alert("Gagal memuat rincian paket decoy.", level="error", width=WIDTH)
                tui_pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    render_alert(f"Menyesuaikan total amount ke: {format_rupiah(valid_amount)}", level="info", width=WIDTH)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        render_alert("Pembelian dengan decoy V2 berhasil!", level="success", width=WIDTH)
            else:
                render_alert("Pembelian dengan decoy V2 berhasil!", level="success", width=WIDTH)
            tui_pause()
            return True
        elif choice == "6":
            decoy = DecoyInstance.get_decoy("qris")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                render_alert("Gagal memuat paket decoy QRIS.", level="error", width=WIDTH)
                tui_pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            show_qris_payment(api_key, tokens, payment_items, "SHARE_PACKAGE", True, token_confirmation_idx=1)
            tui_pause()
            return True
        elif choice == "7":
            decoy = DecoyInstance.get_decoy("qris0")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
            if not decoy_package_detail:
                render_alert("Gagal memuat paket decoy QRIS 0.", level="error", width=WIDTH)
                tui_pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            show_qris_payment(api_key, tokens, payment_items, "SHARE_PACKAGE", True, token_confirmation_idx=1)
            tui_pause()
            return True
        elif choice == "8":
            use_decoy = tui_confirm("Gunakan paket decoy untuk loop pembelian?", default=False)
            n_times_str = tui_input("Jumlah pembelian (contoh: 3)").strip()
            delay_str = tui_input("Jeda antar pembelian dalam detik (contoh: 15)", default="15").strip()
            try:
                n_times = int(n_times_str)
                delay_sec = int(delay_str) if delay_str.isdigit() else 15
                if n_times < 1:
                    raise ValueError
            except ValueError:
                render_alert("Input angka tidak valid. Silakan coba lagi.", level="error", width=WIDTH)
                tui_pause()
                continue

            purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy,
                delay_seconds=delay_sec,
                pause_on_success=False,
                token_confirmation_idx=1
            )
            tui_pause()
            return True
        elif choice.lower() == "b":
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            render_alert("Pengambilan bonus voucher berhasil diproses.", level="success", width=WIDTH)
            tui_pause()
            return True
        elif choice.lower() == "ba":
            destination_msisdn = tui_input("Nomor tujuan bonus (mulai 628)").strip()
            bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            render_alert("Bonus berhasil dikirimkan ke nomor tujuan.", level="success", width=WIDTH)
            tui_pause()
            return True
        elif choice.lower() == "l":
            settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            render_alert("Penukaran poin loyalty berhasil diproses.", level="success", width=WIDTH)
            tui_pause()
            return True
        else:
            render_alert("Pilihan tidak valid. Silakan pilih nomor yang tertera.", level="error", width=WIDTH)
            tui_pause()

def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        render_alert("Sesi login pengguna tidak ditemukan.", level="error", width=WIDTH)
        tui_pause()
        return None
    
    clear_screen()
    render_alert(f"Mengambil katalog paket untuk family {family_code}...", level="info", width=WIDTH)
    data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    if not data:
        render_alert("Gagal memuat katalog paket dari server.", level="error", width=WIDTH)
        tui_pause()
        return None

    price_currency = "Rp"
    rc_bonus_type = data.get("package_family", {}).get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        fam_name = data.get("package_family", {}).get("name", "Family")
        render_header(f"KATALOG: {fam_name}", breadcrumb="engsel ❯ Family", width=WIDTH)
        
        fam_type = data.get("package_family", {}).get("package_family_type", "-")
        package_variants = data.get("package_variants", [])
        
        print(render_hdr_line("INFORMASI KATALOG", width=WIDTH))
        print(render_kv_line("Family Code", family_code, C_WHI, width=WIDTH))
        print(render_kv_2col("Tipe", fam_type, C_MUT, "Varian", f"{len(package_variants)} Kategori", C_PRI, col2=28, width=WIDTH))
        print(render_empty_line(width=WIDTH))
        
        packages = []
        option_number = 1
        
        for variant in package_variants:
            v_name = variant.get("name", "Varian")
            print(render_box_divider(title=v_name, width=WIDTH))
            for option in variant.get("package_options", []):
                opt_name = option.get("name", "Opsi")
                opt_price = option.get("price", 0)
                
                packages.append({
                    "number": option_number,
                    "variant_name": v_name,
                    "option_name": opt_name,
                    "price": opt_price,
                    "code": option.get("package_option_code"),
                    "option_order": option.get("order")
                })
                
                k_badge = badge(str(option_number), C_PRI)
                price_disp = f"{price_currency} {opt_price:,}".replace(",", ".")
                
                avail_opt_w = (WIDTH - 2) - len(f"  [{option_number:>2}] ") - len(price_disp) - 2
                opt_clean = truncate_str(opt_name, avail_opt_w)
                
                left_p = f"  [{option_number:>2}] {opt_clean}"
                rem = (WIDTH - 2) - len(left_p) - len(price_disp) - 1
                row = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(opt_clean) + bg_spaces(max(1, rem)) + C_AMB(price_disp) + bg_spaces(1)
                print(p_line(row, len(left_p) + max(1, rem) + len(price_disp) + 1, width=WIDTH))
                
                option_number += 1
            print(render_empty_line(width=WIDTH))

        print(render_box_divider(title="OPSI", width=WIDTH))
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor paket (1..N)", width=WIDTH))
        print()

        pkg_choice = tui_input("Pilih paket (nomor)").strip()
        if pkg_choice in ("00", "q", "exit"):
            in_package_menu = False
            return None
        
        if not pkg_choice.isdigit():
            render_alert("Input tidak valid. Masukkan nomor urut paket.", level="warning", width=WIDTH)
            tui_pause()
            continue
        
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        if not selected_pkg:
            render_alert("Paket tidak ditemukan dalam daftar.", level="error", width=WIDTH)
            tui_pause()
            continue
        
        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )
        
    return packages

def fetch_my_packages():
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            render_alert("Sesi login pengguna tidak ditemukan.", level="error", width=WIDTH)
            tui_pause()
            return None
        
        id_token = tokens.get("id_token")
        path = "api/v8/packages/quota-details"
        payload = {
            "is_enterprise": False,
            "lang": "en",
            "family_member_id": ""
        }
        
        clear_screen()
        render_alert("Mengambil data paket aktif Anda dari server...", level="info", width=WIDTH)
        res = send_api_request(api_key, path, payload, id_token, "POST")
        if res.get("status") != "SUCCESS":
            render_alert(f"Gagal mengambil data paket: {res.get('message', 'Server error')}", level="error", width=WIDTH)
            tui_pause()
            return None
        
        quotas = res.get("data", {}).get("quotas", [])
        
        clear_screen()
        render_header("PAKET AKTIF SAYA", breadcrumb="engsel ❯ Paket Saya", width=WIDTH)
        print(render_hdr_line(f"TOTAL PAKET TERDAFTAR: {len(quotas)}", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        if not quotas or len(quotas) == 0:
            content_empty = bg_spaces(2) + C_MUT("Anda tidak memiliki paket aktif saat ini.")
            print(p_line(content_empty, len("  Anda tidak memiliki paket aktif saat ini."), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            tui_pause()
            return None

        my_packages = []
        num = 1
        for quota in quotas:
            quota_code = quota.get("quota_code", "")
            group_name = quota.get("group_name", "Paket")
            quota_name = quota.get("name", "Internet")
            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")
            
            k_badge = badge(str(num), C_PRI)
            name_clean = truncate_str(f"{quota_name} ({group_name})", WIDTH - 12)
            
            row_header = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(name_clean)
            print(p_line(row_header, len(f"  [{num:>2}] {name_clean}"), width=WIDTH))

            # Benefits progress / quota bar
            benefits = quota.get("benefits", [])
            for b in benefits:
                b_name = b.get("name", "Benefit")
                d_type = b.get("data_type", "")
                rem_b = b.get("remaining", 0)
                tot_b = b.get("total", 0)

                if d_type == "DATA":
                    rem_s = format_quota_byte(rem_b)
                    tot_s = format_quota_byte(tot_b)
                    pct = int((rem_b / tot_b) * 100) if tot_b > 0 else 0
                    
                    bar_w = 14
                    filled = int((pct / 100) * bar_w)
                    empty = bar_w - filled
                    bar = "█" * filled + "░" * empty
                    
                    q_str = f"{rem_s} / {tot_s}"
                    row_b_plain = f"      [{bar}] {q_str}"
                    row_b = bg_spaces(6) + C_SUC(f"[{bar}] ") + C_AMB(q_str)
                    print(p_line(row_b, len(row_b_plain), width=WIDTH))
                elif d_type == "VOICE":
                    v_str = f"{rem_b / 60:.0f} / {tot_b / 60:.0f} Menit"
                    row_v = bg_spaces(6) + C_MUT("Nelpon: ") + C_WHI(v_str)
                    print(p_line(row_v, len(f"      Nelpon: {v_str}"), width=WIDTH))
                elif d_type == "TEXT":
                    t_str = f"{rem_b} / {tot_b} SMS"
                    row_t = bg_spaces(6) + C_MUT("SMS   : ") + C_WHI(t_str)
                    print(p_line(row_t, len(f"      SMS   : {t_str}"), width=WIDTH))

            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })
            num += 1

            if num <= len(quotas):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="AKSI", width=WIDTH))
        
        line_detail = bg_spaces(2) + badge("1..N", C_PRI) + bg_spaces(1) + C_MUT("Ketik nomor paket untuk rincian & pembelian")
        print(p_line(line_detail, len("  [1..N] Ketik nomor paket untuk rincian & pembelian"), width=WIDTH))
        
        line_unsub = bg_spaces(2) + badge("del N", C_DAN) + bg_spaces(1) + C_DAN("Berhenti berlangganan (contoh: del 1)")
        print(p_line(line_unsub, len("  [del N] Berhenti berlangganan (contoh: del 1)"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih paket/opsi", width=WIDTH))
        print()

        choice = tui_input("Pilihan Anda").strip()
        if choice in ("00", "q", "exit"):
            in_my_packages_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                render_alert("Paket tidak ditemukan.", level="error", width=WIDTH)
                tui_pause()
                continue
            show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
        elif choice.startswith("del ") or choice.startswith("del"):
            parts = choice.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_num = int(parts[1])
                del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_num), None)
                if not del_pkg:
                    render_alert("Nomor paket tidak ditemukan.", level="error", width=WIDTH)
                    tui_pause()
                    continue

                if tui_confirm(f"Yakin ingin berhenti berlangganan dari '{del_pkg['name']}'?", default=False):
                    render_alert(f"Memproses pembatalan paket {del_pkg['name']}...", level="info", width=WIDTH)
                    success = unsubscribe(
                        api_key,
                        tokens,
                        del_pkg["quota_code"],
                        del_pkg["product_subscription_type"],
                        del_pkg["product_domain"]
                    )
                    if success:
                        render_alert("Berhasil berhenti berlangganan dari paket.", level="success", width=WIDTH)
                    else:
                        render_alert("Gagal memproses pembatalan langganan dari server.", level="error", width=WIDTH)
                    tui_pause()
            else:
                render_alert("Format salah! Gunakan: del <nomor urut> (contoh: del 1)", level="warning", width=WIDTH)
                tui_pause()
        else:
            render_alert("Pilihan tidak valid. Silakan coba lagi.", level="warning", width=WIDTH)
            tui_pause()
