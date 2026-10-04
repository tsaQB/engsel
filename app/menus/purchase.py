import requests, time
from random import randint
from app.client.engsel import get_family, get_package_details, get_package
from app.menus.tui import (
    WIDTH,
    render_header,
    render_box_bottom,
    render_box_divider,
    render_hdr_line,
    render_empty_line,
    render_alert,
    tui_pause,
    tui_confirm,
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
    C_SUC,
    p_line,
    bg_spaces,
)
from app.service.auth import AuthInstance
from app.service.decoy import DecoyInstance
from app.type_dict import PaymentItem
from app.client.purchase.balance import settlement_balance

def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            render_alert("Gagal memuat rincian paket decoy.", level="error", width=WIDTH)
            tui_pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        render_alert(f"PERINGATAN: Pastikan sisa pulsa KURANG DARI {format_rupiah(balance_treshold)}!", level="warning", width=WIDTH)
        if not tui_confirm("Apakah Anda yakin ingin melanjutkan pembelian batch?", default=False):
            render_alert("Pembelian dibatalkan oleh pengguna.", level="info", width=WIDTH)
            tui_pause()
            return None
    
    render_alert(f"Mengambil data katalog untuk family {family_code}...", level="info", width=WIDTH)
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        render_alert(f"Gagal mengambil data katalog untuk kode: {family_code}.", level="error", width=WIDTH)
        tui_pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    
    successful_purchases = []
    packages_count = sum(len(v["package_options"]) for v in variants)
    
    purchase_count = 0
    start_buying = (start_from_option <= 1)

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                continue
            
            option_name = option["name"]
            option_price = option["price"]
            
            purchase_count += 1
            render_alert(f"[{purchase_count}/{packages_count}] Membeli: {variant_name} - {option_name} ({format_rupiah(option_price)})", level="info", width=WIDTH)
            
            payment_items = []
            try:
                if use_decoy:                
                    decoy = DecoyInstance.get_decoy("balance")
                    decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                    if not decoy_package_detail:
                        render_alert("Gagal memuat paket decoy.", level="error", width=WIDTH)
                        tui_pause()
                        return False
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                render_alert(f"Gagal mengambil detail paket {variant_name} - {option_name}. Melewati.", level="warning", width=WIDTH)
                continue
            
            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )
            
            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
            
            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_package_detail["package_option"]["price"]
                
            error_msg = ""
            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "🤑",
                    False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        render_alert(f"Menyesuaikan jumlah total ke {format_rupiah(valid_amount)}", level="info", width=WIDTH)
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "SHARE_PACKAGE",
                            False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=-1
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            error_msg = ""
                            successful_purchases.append(f"{variant_name} | {option_name} - {format_rupiah(option_price)}")
                            render_alert(f"Sukses membeli {option_name}!", level="success", width=WIDTH)
                            if pause_on_success:
                                tui_pause()
                        else:
                            error_msg = res.get("message", "")
                else:
                    successful_purchases.append(f"{variant_name} | {option_name} - {format_rupiah(option_price)}")
                    render_alert(f"Sukses membeli {option_name}!", level="success", width=WIDTH)
                    if pause_on_success:
                        tui_pause()

            except Exception as e:
                render_alert(f"Kendala saat order: {e}", level="error", width=WIDTH)

            should_delay = (error_msg == "" or "Failed call ipaas purchase" in error_msg)
            if delay_seconds > 0 and should_delay:
                render_alert(f"Menunggu {delay_seconds} detik sebelum pembelian berikutnya...", level="info", width=WIDTH)
                time.sleep(delay_seconds)
                
    render_alert(f"Selesai! Berhasil membeli {len(successful_purchases)}/{packages_count} paket dari {family_name}.", level="success", width=WIDTH)
    tui_pause()

def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            render_alert("Gagal memuat rincian paket decoy.", level="error", width=WIDTH)
            tui_pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        render_alert(f"PERINGATAN: Pastikan sisa pulsa KURANG DARI {format_rupiah(balance_treshold)}!", level="warning", width=WIDTH)
        if not tui_confirm(f"Lanjutkan pembelian {n} kali?", default=False):
            render_alert("Pembelian dibatalkan oleh pengguna.", level="info", width=WIDTH)
            tui_pause()
            return None
    
    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        render_alert(f"Gagal mengambil data family {family_code}.", level="error", width=WIDTH)
        tui_pause()
        return None

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = next((v for v in variants if v["package_variant_code"] == variant_code), None)
    if not target_variant:
        render_alert(f"Kode varian {variant_code} tidak ditemukan.", level="error", width=WIDTH)
        tui_pause()
        return None

    target_option = next((o for o in target_variant["package_options"] if o["order"] == option_order), None)
    if not target_option:
        render_alert(f"Nomor opsi {option_order} tidak ditemukan.", level="error", width=WIDTH)
        tui_pause()
        return None

    option_name = target_option["name"]
    option_price = target_option["price"]
    successful_purchases = []
    
    for i in range(n):
        render_alert(f"Percobaan {i + 1}/{n}: {target_variant['name']} - {option_name} ({format_rupiah(option_price)})", level="info", width=WIDTH)
        tokens = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    render_alert("Gagal memuat paket decoy.", level="error", width=WIDTH)
                    tui_pause()
                    return False
            
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            render_alert(f"Gagal mengambil detail paket: {e}", level="warning", width=WIDTH)
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    render_alert(f"Menyesuaikan jumlah total ke {format_rupiah(valid_amount)}", level="info", width=WIDTH)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"{target_variant['name']} | {option_name}")
                        render_alert(f"Pembelian {i + 1} berhasil!", level="success", width=WIDTH)
                        if pause_on_success:
                            tui_pause()
            else:
                successful_purchases.append(f"{target_variant['name']} | {option_name}")
                render_alert(f"Pembelian {i + 1} berhasil!", level="success", width=WIDTH)
                if pause_on_success:
                    tui_pause()
        except Exception as e:
            render_alert(f"Kendala order: {e}", level="error", width=WIDTH)

        if delay_seconds > 0 and i < n - 1:
            render_alert(f"Menunggu jeda {delay_seconds} detik...", level="info", width=WIDTH)
            time.sleep(delay_seconds)

    render_alert(f"Total berhasil: {len(successful_purchases)}/{n} untuk {option_name}.", level="success", width=WIDTH)
    tui_pause()
    return True

def purchase_n_times_by_option_code(
    n: int,
    option_code: str,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}
    
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            render_alert("Gagal memuat rincian paket decoy.", level="error", width=WIDTH)
            tui_pause()
            return False
        
        balance_treshold = decoy_package_detail["package_option"]["price"]
        render_alert(f"PERINGATAN: Pastikan sisa pulsa KURANG DARI {format_rupiah(balance_treshold)}!", level="warning", width=WIDTH)
        if not tui_confirm(f"Lanjutkan loop pembelian {n} kali?", default=False):
            render_alert("Pembelian dibatalkan.", level="info", width=WIDTH)
            tui_pause()
            return None
    
    successful_purchases = []
    
    for i in range(n):
        render_alert(f"Loop {i + 1}/{n} untuk opsi {option_code}...", level="info", width=WIDTH)
        tokens = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    render_alert("Gagal memuat paket decoy.", level="error", width=WIDTH)
                    tui_pause()
                    return False
            
            target_package_detail = get_package(api_key, tokens, option_code)
        except Exception as e:
            render_alert(f"Gagal mengambil detail paket: {e}", level="warning", width=WIDTH)
            continue
        
        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=str(randint(1000, 9999)) + " " + target_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )
        
        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=str(randint(1000, 9999)) + " " + decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    render_alert(f"Menyesuaikan jumlah total ke {format_rupiah(valid_amount)}", level="info", width=WIDTH)
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"Pembelian {i + 1}")
                        render_alert(f"Pembelian {i + 1} berhasil!", level="success", width=WIDTH)
                        if pause_on_success:
                            tui_pause()
            else:
                successful_purchases.append(f"Pembelian {i + 1}")
                render_alert(f"Pembelian {i + 1} berhasil!", level="success", width=WIDTH)
                if pause_on_success:
                    tui_pause()
        except Exception as e:
            render_alert(f"Kendala order: {e}", level="error", width=WIDTH)

        if delay_seconds > 0 and i < n - 1:
            render_alert(f"Menunggu jeda {delay_seconds} detik...", level="info", width=WIDTH)
            time.sleep(delay_seconds)

    render_alert(f"Total berhasil: {len(successful_purchases)}/{n}", level="success", width=WIDTH)
    tui_pause()
    return True
