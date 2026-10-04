from datetime import datetime
import json
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
    render_kv_line,
    render_kv_2col,
    tui_input,
    tui_confirm,
    badge,
    status_badge,
    format_msisdn,
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
from app.client.circle import (
    get_group_data,
    get_group_members,
    create_circle,
    validate_circle_member,
    invite_circle_member,
    remove_circle_member,
    accept_circle_invitation,
    spending_tracker,
    get_bonus_data,
)
from app.service.auth import AuthInstance
from app.client.encrypt import decrypt_circle_msisdn
from app.util import normalize_msisdn

def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    render_header("BUAT CIRCLE BARU", breadcrumb="engsel ❯ Circle ❯ Buat", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    
    parent_name = tui_input("Nama Anda (Parent/Ketua)").strip()
    group_name = tui_input("Nama Circle / Komunitas").strip()
    raw_member = tui_input("Nomor Anggota Pertama (08123456789)").strip()
    member_msisdn = normalize_msisdn(raw_member)
    member_name = tui_input("Nama Anggota Pertama").strip()
    
    if not (parent_name and group_name and member_msisdn and member_name):
        render_alert("Semua data harus diisi lengkap untuk membuat Circle.", level="error", width=WIDTH)
        tui_pause()
        return

    render_alert("Membuat Circle baru di sistem MyXL...", level="info", width=WIDTH)
    create_res = create_circle(
        api_key,
        tokens,
        parent_name,
        group_name,
        member_msisdn,
        member_name
    )
    
    if create_res.get("status") == "SUCCESS":
        render_alert(f"Circle '{group_name}' berhasil dibuat!", level="success", width=WIDTH)
    else:
        render_alert(f"Gagal membuat Circle: {create_res.get('message', 'Server error')}", level="error", width=WIDTH)
    tui_pause()

def show_bonus_list(
    api_key: str,
    tokens: dict,
    parent_subs_id: str,
    family_id: str,
):
    in_circle_bonus_menu = True
    while in_circle_bonus_menu:
        clear_screen()
        render_alert("Mengambil data bonus Circle dari server...", level="info", width=WIDTH)
        bonus_data = get_bonus_data(
            api_key,
            tokens,
            parent_subs_id,
            family_id
        )
        if not bonus_data or bonus_data.get("status") != "SUCCESS":
            render_alert("Gagal mengambil data bonus Circle.", level="error", width=WIDTH)
            tui_pause()
            return
        
        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        
        clear_screen()
        render_header("BONUS CIRCLE GROUP", breadcrumb="engsel ❯ Circle ❯ Bonus", width=WIDTH)
        print(render_hdr_line(f"DAFTAR BONUS TERSEDIA ({len(bonus_list)})", width=WIDTH))
        print(render_empty_line(width=WIDTH))

        if not bonus_list:
            content_empty = bg_spaces(2) + C_MUT("Belum ada bonus yang dapat diklaim saat ini.")
            print(p_line(content_empty, len("  Belum ada bonus yang dapat diklaim saat ini."), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            tui_pause()
            return

        for idx, bonus in enumerate(bonus_list, start=1):
            b_name = bonus.get("name", "Bonus")
            b_type = bonus.get("bonus_type", "Bonus")
            k_badge = badge(str(idx), C_PRI)
            
            avail_w = (WIDTH - 2) - len(f"  [{idx:>2}] ") - 2
            b_name_trunc = truncate_str(b_name, avail_w)
            
            row1_p = f"  [{idx:>2}] {b_name_trunc}"
            row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(b_name_trunc)
            print(p_line(row1, len(row1_p), width=WIDTH))

            act_type = bonus.get("action_type", "-")
            row2_p = f"      Tipe: {b_type} | Aksi: {act_type}"
            row2 = bg_spaces(6) + C_DIM(f"Tipe: {b_type} | Aksi: {act_type}")
            print(p_line(row2, len(row2_p), width=WIDTH))

            if idx < len(bonus_list):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="PILIH BONUS", width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Circle")
        print(p_line(line_back, len("  [00] Kembali ke Menu Circle"), width=WIDTH))
        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor bonus (1..N)", width=WIDTH))
        print()

        choice = tui_input("Nomor bonus").strip()
        if choice in ("00", "q", "exit"):
            in_circle_bonus_menu = False
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(bonus_list):
            selected_bonus = bonus_list[int(choice) - 1]
            action_type = selected_bonus.get("action_type", "")
            action_param = selected_bonus.get("action_param", "")
            
            if action_type == "PLP":
                get_packages_by_family(action_param)
            elif action_type == "PDP":
                show_package_details(api_key, tokens, action_param, False)
            else:
                render_alert(f"Tipe aksi tidak didukung: {action_type} ({action_param})", level="warning", width=WIDTH)
                tui_pause()
        else:
            render_alert("Nomor bonus tidak valid.", level="error", width=WIDTH)
            tui_pause()

def show_circle_info(api_key: str, tokens: dict):
    in_circle_menu = True
    user = AuthInstance.get_active_user() or {}
    my_msisdn = str(user.get("number", ""))

    while in_circle_menu:
        clear_screen()
        render_alert("Mengambil data Circle Group dari server...", level="info", width=WIDTH)
        group_res = get_group_data(api_key, tokens)
        if not group_res or group_res.get("status") != "SUCCESS":
            render_alert("Gagal mengambil data Circle dari server.", level="error", width=WIDTH)
            tui_pause()
            return
        
        group_data = group_res.get("data", {})
        group_id = group_data.get("group_id", "")

        if not group_id:
            clear_screen()
            render_header("CIRCLE GROUP", breadcrumb="engsel ❯ Circle", width=WIDTH)
            print(render_empty_line(width=WIDTH))
            row_nc = bg_spaces(2) + C_MUT("Anda saat ini belum tergabung dalam Circle manapun.")
            print(p_line(row_nc, len("  Anda saat ini belum tergabung dalam Circle manapun."), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            print()
            
            if tui_confirm("Ingin membuat grup Circle baru?", default=False):
                show_circle_creation(api_key, tokens)
                continue
            else:
                return

        group_status = group_data.get("group_status", "ACTIVE")
        if group_status == "BLOCKED":
            render_alert("Grup Circle ini saat ini sedang DIBLOKIR oleh sistem.", level="error", width=WIDTH)
            tui_pause()
            return
        
        group_name = group_data.get("group_name", "Circle")
        owner_name = group_data.get("owner_name", "Owner")
        
        members_res = get_group_members(api_key, tokens, group_id)
        if not members_res or members_res.get("status") != "SUCCESS":
            render_alert("Gagal mengambil data anggota Circle.", level="error", width=WIDTH)
            tui_pause()
            return
        
        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if not members:
            render_alert("Tidak ada anggota yang terdaftar dalam Circle ini.", level="warning", width=WIDTH)
            tui_pause()
            return
        
        parent_member_id = ""
        parent_subs_id = ""
        parent_msisdn = ""
        for m in members:
            if m.get("member_role", "") == "PARENT":
                parent_member_id = m.get("member_id", "")
                parent_subs_id = m.get("subscriber_number", "")
                enc_m = m.get("msisdn", "")
                parent_msisdn = decrypt_circle_msisdn(api_key, enc_m) if enc_m else ""

        # Spending Tracker
        spend = 0
        target = 0
        if parent_subs_id:
            spending_res = spending_tracker(api_key, tokens, parent_subs_id, group_id)
            if spending_res.get("status") == "SUCCESS":
                s_data = spending_res.get("data", {})
                spend = s_data.get("spend", 0)
                target = s_data.get("target", 0)

        clear_screen()
        render_header("CIRCLE GROUP DASHBOARD", breadcrumb="engsel ❯ Circle", width=WIDTH)
        
        # 1. Ringkasan Info Circle
        print(render_hdr_line("INFORMASI CIRCLE", width=WIDTH))
        print(render_kv_line("Nama Circle", group_name, C_WHI, width=WIDTH))
        print(render_kv_2col("Ketua/Owner", f"{owner_name} ({format_msisdn(parent_msisdn)})", C_WHI, "Status", status_badge(group_status), C_SUC, col2=28, width=WIDTH))
        print(render_kv_2col("Belanja Tim", format_rupiah(spend), C_AMB, "Target Belanja", format_rupiah(target), C_MUT, col2=28, width=WIDTH))
        
        # Spending Progress Bar
        pct_spend = int((spend / target) * 100) if target > 0 else 0
        pct_spend = min(100, pct_spend)
        bar_w = 20
        filled = int((pct_spend / 100) * bar_w)
        empty = bar_w - filled
        bar_str = "█" * filled + "░" * empty
        row_sp = bg_spaces(2) + C_MUT("Progress Target: ") + C_PRI(f"[{bar_str}] ") + C_WHI(f"{pct_spend}%")
        print(p_line(row_sp, len(f"  Progress Target: [{bar_str}] {pct_spend}%"), width=WIDTH))
        print(render_empty_line(width=WIDTH))

        # 2. Tabel Anggota
        print(render_box_divider(title=f"DAFTAR ANGGOTA ({len(members)})", width=WIDTH))
        for idx, member in enumerate(members, start=1):
            enc_m = member.get("msisdn", "")
            m_msisdn = decrypt_circle_msisdn(api_key, enc_m) if enc_m else ""
            m_name = member.get("member_name", "Anggota")
            m_role = member.get("member_role", "MEMBER")
            m_status = member.get("status", "ACTIVE")
            
            is_me = (str(m_msisdn) == my_msisdn)
            me_tag = " (Anda)" if is_me else ""
            
            m_alloc = member.get("allocation", 0)
            m_rem = member.get("remaining", 0)
            m_used = max(0, m_alloc - m_rem)
            
            k_badge = badge(str(idx), C_WHI if is_me else C_PRI)
            num_clean = format_msisdn(m_msisdn)
            role_badge = C_PRI("[KETUA]") if m_role == "PARENT" else C_MUT(f"[{m_name}]")
            
            row1_p = f"  [{idx:>2}] {num_clean} {m_name}{me_tag}"
            row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(num_clean) + bg_spaces(1) + role_badge + (C_SUC(me_tag) if is_me else "")
            print(p_line(row1, len(row1_p), width=WIDTH))

            stat_badge_str = status_badge(m_status)
            row2_p = f"      Status: {m_status} • Kuota: {format_quota_byte(m_used)} / {format_quota_byte(m_alloc)}"
            row2 = bg_spaces(6) + C_MUT("Status: ") + stat_badge_str + C_MUT(" • Kuota: ") + C_AMB(f"{format_quota_byte(m_used)} / {format_quota_byte(m_alloc)}")
            print(p_line(row2, len(row2_p), width=WIDTH))

            if idx < len(members):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="AKSI CIRCLE", width=WIDTH))
        
        line_inv = bg_spaces(2) + badge("1", C_PRI) + bg_spaces(1) + C_WHI("Undang Anggota Baru ke Circle")
        print(p_line(line_inv, len("  [ 1] Undang Anggota Baru ke Circle"), width=WIDTH))
        
        line_bon = bg_spaces(2) + badge("2", C_SUC) + bg_spaces(1) + C_WHI("Lihat Daftar Bonus Circle")
        print(p_line(line_bon, len("  [ 2] Lihat Daftar Bonus Circle"), width=WIDTH))
        
        line_acc = bg_spaces(2) + badge("acc N", C_AMB) + bg_spaces(1) + C_MUT("Terima undangan anggota (contoh: acc 2)")
        print(p_line(line_acc, len("  [acc N] Terima undangan anggota (contoh: acc 2)"), width=WIDTH))
        
        line_del = bg_spaces(2) + badge("del N", C_DAN) + bg_spaces(1) + C_DAN("Keluarkan anggota dari Circle (contoh: del 2)")
        print(p_line(line_del, len("  [del N] Keluarkan anggota dari Circle (contoh: del 2)"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih opsi / ketik perintah", width=WIDTH))
        print()

        choice = tui_input("Perintah Circle").strip()
        if choice in ("00", "q", "exit"):
            in_circle_menu = False
            return
        elif choice == "1":
            raw_msisdn = tui_input("Nomor HP Calon Anggota (08123456789)").strip()
            msisdn_to_invite = normalize_msisdn(raw_msisdn)
            render_alert(f"Memvalidasi nomor {format_msisdn(msisdn_to_invite)}...", level="info", width=WIDTH)
            val_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if val_res.get("status") == "SUCCESS":
                if val_res.get("data", {}).get("response_code", "") != "200-2001":
                    err = val_res.get("data", {}).get("message", "Tidak memenuhi syarat")
                    render_alert(f"Tidak dapat mengundang {format_msisdn(msisdn_to_invite)}: {err}", level="error", width=WIDTH)
                    tui_pause()
                    continue
            
            member_name = tui_input("Nama Panggilan Anggota").strip()
            render_alert("Mengirim undangan Circle...", level="info", width=WIDTH)
            inv_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)
            if inv_res.get("status") == "SUCCESS" and inv_res.get("data", {}).get("response_code") == "200-00":
                render_alert(f"Undangan berhasil dikirim ke {format_msisdn(msisdn_to_invite)}!", level="success", width=WIDTH)
            else:
                err = inv_res.get("data", {}).get("message", "Gagal mengundang anggota.")
                render_alert(f"Gagal mengundang: {err}", level="error", width=WIDTH)
            tui_pause()
        elif choice == "2":
            show_bonus_list(api_key, tokens, parent_subs_id, group_id)
        elif choice.startswith("acc "):
            try:
                m_idx = int(choice.split()[1])
                if m_idx < 1 or m_idx > len(members):
                    render_alert("Nomor anggota tidak valid.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                m_to_acc = members[m_idx - 1]
                if m_to_acc.get("status") != "INVITED":
                    render_alert("Anggota tersebut tidak berstatus INVITED.", level="warning", width=WIDTH)
                    tui_pause()
                    continue
                
                m_id = m_to_acc.get("member_id", "")
                m_dec = decrypt_circle_msisdn(api_key, m_to_acc.get("msisdn", ""))
                
                if tui_confirm(f"Konfirmasi penerimaan undangan untuk {format_msisdn(m_dec)}?", default=True):
                    render_alert("Menerima undangan...", level="info", width=WIDTH)
                    acc_res = accept_circle_invitation(api_key, tokens, group_id, m_id)
                    if acc_res.get("status") == "SUCCESS":
                        render_alert(f"Undangan {format_msisdn(m_dec)} berhasil diterima!", level="success", width=WIDTH)
                    else:
                        render_alert("Gagal menerima undangan.", level="error", width=WIDTH)
                    tui_pause()
            except ValueError:
                render_alert("Format salah! Gunakan: acc <nomor urut> (contoh: acc 2)", level="warning", width=WIDTH)
                tui_pause()
        elif choice.startswith("del "):
            try:
                m_idx = int(choice.split()[1])
                if m_idx < 1 or m_idx > len(members):
                    render_alert("Nomor anggota tidak valid.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                m_to_del = members[m_idx - 1]
                if m_to_del.get("member_role") == "PARENT":
                    render_alert("Ketua/Parent Circle tidak dapat dikeluarkan!", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                is_last = (len(members) == 2)
                if is_last:
                    render_alert("Tidak dapat mengeluarkan anggota terakhir Circle.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                m_id = m_to_del.get("member_id", "")
                m_dec = decrypt_circle_msisdn(api_key, m_to_del.get("msisdn", ""))
                
                if tui_confirm(f"Yakin ingin mengeluarkan {format_msisdn(m_dec)} dari Circle?", default=False):
                    render_alert("Memproses pengeluaran anggota...", level="info", width=WIDTH)
                    del_res = remove_circle_member(api_key, tokens, m_id, group_id, parent_member_id, is_last)
                    if del_res.get("status") == "SUCCESS":
                        render_alert(f"Anggota {format_msisdn(m_dec)} berhasil dikeluarkan.", level="success", width=WIDTH)
                    else:
                        render_alert("Gagal mengeluarkan anggota dari Circle.", level="error", width=WIDTH)
                    tui_pause()
            except ValueError:
                render_alert("Format salah! Gunakan: del <nomor urut> (contoh: del 2)", level="warning", width=WIDTH)
                tui_pause()
        else:
            render_alert("Perintah tidak dikenali. Silakan coba lagi.", level="warning", width=WIDTH)
            tui_pause()
