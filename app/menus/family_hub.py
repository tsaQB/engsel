from datetime import datetime
import json
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
from app.client.family_hub import (
    get_family_hub_eligibility,
    get_family_hub_status,
    get_family_hub_members,
    create_family_hub_group,
    invite_family_hub_members,
    remove_family_hub_member,
    change_family_hub_group_name,
    change_family_hub_member_name,
    disband_family_hub_group,
    leave_family_hub_group,
    accept_family_hub_invitation,
    get_family_hub_activities,
    get_family_hub_packages,
)
from app.service.auth import AuthInstance
from app.util import normalize_msisdn

def format_bytes_or_str(byte_val):
    try:
        b = int(byte_val)
        if b <= 0:
            return "0 B"
        return format_quota_byte(b)
    except Exception:
        return str(byte_val)

def show_eligibility_check(api_key: str, id_token: str):
    clear_screen()
    render_header("CEK KELAYAKAN FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Cek", width=WIDTH)
    render_alert("Memeriksa kelayakan nomor Anda di sistem XL...", level="info", width=WIDTH)
    
    res = get_family_hub_eligibility(api_key, id_token)
    code = res.get("code")
    status = res.get("status")
    data = res.get("data", {})
    msg = data.get("message", res.get("message", "N/A"))
    
    clear_screen()
    render_header("HASIL KELAYAKAN FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Hasil", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    
    if code == "000" and status == "SUCCESS":
        render_alert(f"Nomor Anda MEMENUHI SYARAT (ELIGIBLE)! {msg}", level="success", width=WIDTH)
    else:
        render_alert(f"Nomor TIDAK memenuhi syarat: {msg}", level="warning", width=WIDTH)
    tui_pause()

def show_create_group(api_key: str, tokens: dict):
    clear_screen()
    render_header("BUAT GRUP FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Buat", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    print(p_line(bg_spaces(2) + C_MUT("Catatan: Anda akan menjadi Pengelola (Parent) grup ini."), len("  Catatan: Anda akan menjadi Pengelola (Parent) grup ini."), width=WIDTH))
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    print()
    
    group_name = tui_input("Nama Grup (contoh: Keluarga Bahagia)").strip()
    if not group_name or group_name in ("00", "q"):
        return
        
    parent_name = tui_input("Nama Pengelola (contoh: Ayah)").strip()
    if not parent_name:
        render_alert("Nama pengelola tidak boleh kosong.", level="error", width=WIDTH)
        tui_pause()
        return

    members = []
    if tui_confirm("Ingin langsung mengundang anggota awal?", default=False):
        raw_m = tui_input("Nomor MSISDN Anggota (08123456789)").strip()
        m_msisdn = normalize_msisdn(raw_m)
        m_name = tui_input("Nama Panggilan Anggota").strip()
        if m_msisdn and m_name:
            members.append({"msisdn": m_msisdn, "name": m_name})

    render_alert("Mengirim permintaan pembuatan grup Family Hub...", level="info", width=WIDTH)
    res = create_family_hub_group(
        api_key=api_key,
        id_token=tokens["id_token"],
        access_token=tokens["access_token"],
        group_name=group_name,
        parent_name=parent_name,
        members=members
    )

    code = res.get("code")
    status = res.get("status")
    data = res.get("data", {})
    msg = res.get("message", "Gagal membuat grup")
    
    if code == "000" and status == "SUCCESS":
        render_alert(f"Grup Family Hub '{group_name}' berhasil dibuat!", level="success", width=WIDTH)
        inv_link = data.get("invitation_link", "")
        if inv_link:
            render_alert(f"Link Undangan: {inv_link}", level="info", width=WIDTH)
    else:
        render_alert(f"Gagal membuat grup: {msg} (Kode: {code})", level="error", width=WIDTH)
    tui_pause()

def show_accept_invitation(api_key: str, tokens: dict):
    clear_screen()
    render_header("TERIMA UNDANGAN FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Undangan", width=WIDTH)
    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    print()
    
    group_id = tui_input("Group ID").strip()
    member_id = tui_input("Member ID Anda").strip()
    
    if not (group_id and member_id):
        render_alert("Group ID dan Member ID wajib diisi.", level="warning", width=WIDTH)
        tui_pause()
        return

    render_alert("Memproses penerimaan undangan...", level="info", width=WIDTH)
    res = accept_family_hub_invitation(
        api_key=api_key,
        id_token=tokens["id_token"],
        access_token=tokens["access_token"],
        group_id=group_id,
        member_id=member_id
    )

    if res.get("code") == "000" and res.get("status") == "SUCCESS":
        render_alert("Berhasil bergabung ke dalam grup Family Hub!", level="success", width=WIDTH)
    else:
        render_alert(f"Gagal menerima undangan: {res.get('message', 'Server error')}", level="error", width=WIDTH)
    tui_pause()

def show_group_activities(api_key: str, id_token: str, group_id: str):
    clear_screen()
    render_header("LOG AKTIVITAS FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Log", width=WIDTH)
    render_alert("Mengambil riwayat aktivitas grup...", level="info", width=WIDTH)
    res = get_family_hub_activities(api_key, id_token, group_id)

    activities = res.get("data", {}).get("activities", [])
    clear_screen()
    render_header("LOG AKTIVITAS FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Log", width=WIDTH)
    print(render_hdr_line(f"RIWAYAT AKTIVITAS ({len(activities)})", width=WIDTH))
    print(render_empty_line(width=WIDTH))

    if not activities:
        content_empty = bg_spaces(2) + C_MUT("Belum ada aktivitas tercatat pada grup ini.")
        print(p_line(content_empty, len("  Belum ada aktivitas tercatat pada grup ini."), width=WIDTH))
    else:
        for idx, act in enumerate(activities, 1):
            date_str = "-"
            if act.get("activity_date"):
                try:
                    ts = int(act["activity_date"]) // 1000 if int(act["activity_date"]) > 1e11 else int(act["activity_date"])
                    date_str = datetime.fromtimestamp(ts).strftime("%d %b %Y %H:%M")
                except Exception:
                    pass
            a_type = act.get("type", "Aktivitas")
            a_desc = act.get("description", "-")
            
            row1_p = f"  [{idx:>2}] {a_type} • {date_str}"
            row1 = bg_spaces(2) + badge(str(idx), C_PRI) + bg_spaces(1) + C_WHI(a_type) + bg_spaces(1) + C_DIM(f"• {date_str}")
            print(p_line(row1, len(row1_p), width=WIDTH))
            
            desc_trunc = truncate_str(a_desc, WIDTH - 8)
            row2 = bg_spaces(6) + C_MUT(desc_trunc)
            print(p_line(row2, len(f"      {desc_trunc}"), width=WIDTH))
            
            if idx < len(activities):
                print(render_empty_line(width=WIDTH))

    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    tui_pause()

def show_family_packages(api_key: str, id_token: str, access_token: str):
    clear_screen()
    render_header("PAKET BOOSTER FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Paket", width=WIDTH)
    render_alert("Mengambil katalog paket booster Family Hub...", level="info", width=WIDTH)
    res = get_family_hub_packages(api_key, id_token, access_token)

    packages = res.get("data", {}).get("packages", [])
    clear_screen()
    render_header("PAKET BOOSTER FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Paket", width=WIDTH)
    print(render_hdr_line(f"KATALOG FAMILY BOOSTER ({len(packages)})", width=WIDTH))
    print(render_empty_line(width=WIDTH))

    if not packages:
        content_empty = bg_spaces(2) + C_MUT("Tidak ada paket Family Booster khusus yang tersedia saat ini.")
        print(p_line(content_empty, len("  Tidak ada paket Family Booster khusus yang tersedia saat ini."), width=WIDTH))
    else:
        for idx, pkg in enumerate(packages, 1):
            name = pkg.get("name", pkg.get("package_name", "Paket"))
            code = pkg.get("package_option_code", pkg.get("code", "-"))
            price = pkg.get("discounted_price", pkg.get("price", 0))
            price_fmt = format_rupiah(price)

            avail_w = (WIDTH - 2) - len(f"  [{idx:>2}] ") - len(price_fmt) - 2
            name_clean = truncate_str(name, avail_w)
            
            left_p = f"  [{idx:>2}] {name_clean}"
            rem = (WIDTH - 2) - len(left_p) - len(price_fmt) - 1
            row = bg_spaces(2) + badge(str(idx), C_PRI) + bg_spaces(1) + C_WHI(name_clean) + bg_spaces(max(1, rem)) + C_AMB(price_fmt) + bg_spaces(1)
            print(p_line(row, len(left_p) + max(1, rem) + len(price_fmt) + 1, width=WIDTH))
            
            code_trunc = truncate_str(f"Code: {code}", WIDTH - 8)
            row_code = bg_spaces(6) + C_DIM(code_trunc)
            print(p_line(row_code, len(f"      {code_trunc}"), width=WIDTH))

            if idx < len(packages):
                print(render_empty_line(width=WIDTH))

    print(render_empty_line(width=WIDTH))
    print(render_box_bottom(width=WIDTH))
    tui_pause()

def family_hub_menu():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        render_alert("Silakan login terlebih dahulu.", level="error", width=WIDTH)
        tui_pause()
        return

    tokens = AuthInstance.get_active_tokens()
    api_key = AuthInstance.api_key

    while True:
        clear_screen()
        render_alert("Memeriksa status grup Family Hub...", level="info", width=WIDTH)
        status_res = get_family_hub_status(api_key, tokens["id_token"])
        status_data = status_res.get("data", {}) if status_res else {}
        group_status = status_data.get("group_status", "NONE")
        group_id = status_data.get("group_id", "")
        group_name = status_data.get("group_name", "")
        is_owner = status_data.get("is_owner", False)
        member_id = status_data.get("member_id", "")
        owner_name = status_data.get("owner_name", "")

        clear_screen()
        render_header("FAMILY HUB (KUOTA SEKELUARGA)", breadcrumb="engsel ❯ Family Hub", width=WIDTH)

        # Kasus 1: Belum ada grup
        if group_status == "NONE" or not group_id:
            num_fmt = format_msisdn(active_user.get("number", ""))
            print(render_hdr_line("STATUS KELUARGA", width=WIDTH))
            print(render_kv_line("Nomor HP", num_fmt, C_WHI, width=WIDTH))
            print(render_kv_line("Status Grup", "Belum Tergabung dalam Grup Family Hub", C_MUT, width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_divider(title="PILIHAN MENU", width=WIDTH))

            print(p_line(bg_spaces(2) + badge("1", C_PRI) + bg_spaces(1) + C_WHI("Cek Kelayakan Nomor (Check Eligibility)"), len("  [ 1] Cek Kelayakan Nomor (Check Eligibility)"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("2", C_SUC) + bg_spaces(1) + C_WHI("Buat Grup Keluarga Baru (Create Group)"), len("  [ 2] Buat Grup Keluarga Baru (Create Group)"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("3", C_AMB) + bg_spaces(1) + C_WHI("Terima Undangan Grup (Accept Invitation)"), len("  [ 3] Terima Undangan Grup (Accept Invitation)"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("4", C_PRI) + bg_spaces(1) + C_WHI("Cek Paket / Family Booster di Store"), len("  [ 4] Cek Paket / Family Booster di Store"), width=WIDTH))
            print(p_line(bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama"), len("  [00] Kembali ke Menu Utama"), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(footer="Pilih opsi", width=WIDTH))
            print()

            choice = tui_input("Pilihan menu").strip()
            if choice == "1":
                show_eligibility_check(api_key, tokens["id_token"])
            elif choice == "2":
                show_create_group(api_key, tokens)
            elif choice == "3":
                show_accept_invitation(api_key, tokens)
            elif choice == "4":
                show_family_packages(api_key, tokens["id_token"], tokens.get("access_token", ""))
            elif choice in ("00", "0", "q", "exit"):
                break
            else:
                render_alert("Pilihan tidak valid.", level="warning", width=WIDTH)
                tui_pause()
            continue

        # Kasus 2: Sudah ada grup
        members_res = get_family_hub_members(api_key, tokens["id_token"], group_id)
        fam_data = members_res.get("data", {}) if members_res else {}
        members_list = fam_data.get("members", [])
        
        pkg_info = fam_data.get("fam_hub_package") or {}
        benefit = pkg_info.get("benefit") or {}
        shared_alloc = format_bytes_or_str(benefit.get("allocation", 0))
        shared_rem = format_bytes_or_str(benefit.get("remaining", 0))

        role_label = "PENGELOLA (OWNER)" if is_owner else "ANGGOTA (MEMBER)"
        display_group_name = group_name or fam_data.get("group_name", "Grup Keluarga")

        print(render_hdr_line("INFORMASI GRUP", width=WIDTH))
        print(render_kv_line("Nama Grup", display_group_name, C_WHI, width=WIDTH))
        print(render_kv_2col("Peran Anda", role_label, C_PRI if is_owner else C_MUT, "ID Grup", group_id[:12] + "…", C_DIM, col2=28, width=WIDTH))
        
        if benefit.get("allocation"):
            print(render_kv_2col("Kuota Sisa", shared_rem, C_AMB, "Total Kuota", shared_alloc, C_MUT, col2=28, width=WIDTH))
        print(render_empty_line(width=WIDTH))

        # Tabel Anggota
        print(render_box_divider(title=f"DAFTAR ANGGOTA ({len(members_list)})", width=WIDTH))
        for idx, m in enumerate(members_list, 1):
            m_name = m.get("member_name", "Anggota")
            raw_msisdn = m.get("msisdn") or m.get("subscriber_number") or "-"
            m_msisdn = format_msisdn(raw_msisdn)
            m_role = m.get("member_role", "MEMBER")
            m_alloc = format_bytes_or_str(m.get("allocation", 0))
            m_rem = format_bytes_or_str(m.get("remaining", 0))
            m_stat = m.get("status", "ACTIVE")

            role_pill = "[PARENT]" if m_role == "PARENT" else "[MEMBER]"
            row1_p = f"  [{idx:>2}] {m_name} ({m_msisdn}) {role_pill}"
            row1 = bg_spaces(2) + badge(str(idx), C_PRI) + bg_spaces(1) + C_WHI(m_name) + bg_spaces(1) + C_DIM(f"({m_msisdn})") + bg_spaces(1) + (C_PRI(role_pill) if m_role == "PARENT" else C_MUT(role_pill))
            print(p_line(row1, len(row1_p), width=WIDTH))

            row2_p = f"      Sisa: {m_rem} / Alokasi: {m_alloc} • Status: {m_stat}"
            row2 = bg_spaces(6) + C_MUT("Sisa: ") + C_AMB(f"{m_rem} / {m_alloc}") + C_MUT(" • Status: ") + status_badge(m_stat)
            print(p_line(row2, len(row2_p), width=WIDTH))

            if idx < len(members_list):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="AKSI GRUP", width=WIDTH))
        
        m_opts = [
            ("1", "Refresh Data Grup", C_PRI),
            ("2", "Tambah / Undang Anggota Baru", C_PRI),
            ("3", "Ganti Nama Panggilan Anggota", C_MUT),
        ]
        if is_owner:
            m_opts.extend([
                ("4", "Hapus / Keluarkan Anggota", C_DAN),
                ("5", "Ganti Nama Grup", C_MUT),
                ("6", "Log Aktivitas Grup", C_PRI),
                ("7", "Katalog Paket Family Booster", C_PRI),
                ("8", "Bubarkan Grup (Disband)", C_DAN),
            ])
        else:
            m_opts.extend([
                ("4", "Log Aktivitas Grup", C_PRI),
                ("5", "Katalog Paket Family Booster", C_PRI),
                ("6", "Keluar dari Grup (Leave)", C_DAN),
            ])
        m_opts.append(("00", "Kembali ke Menu Utama", C_DAN))

        for k, lbl, fn in m_opts:
            print(p_line(bg_spaces(2) + badge(k, fn) + bg_spaces(1) + fn(lbl), len(f"  [{k:>2}] {lbl}"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Pilih opsi", width=WIDTH))
        print()

        choice = tui_input("Menu").strip()
        if choice == "1":
            continue
        elif choice == "2":
            clear_screen()
            render_header("UNDANG ANGGOTA FAMILY HUB", breadcrumb="engsel ❯ Family Hub ❯ Undang", width=WIDTH)
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            print()
            raw_new = tui_input("Nomor MSISDN Anggota Baru").strip()
            new_msisdn = normalize_msisdn(raw_new)
            new_name = tui_input("Nama Panggilan Anggota").strip()
            if not (new_msisdn and new_name):
                render_alert("Nomor dan nama wajib diisi.", level="warning", width=WIDTH)
                tui_pause()
                continue

            render_alert("Mengirim undangan Family Hub...", level="info", width=WIDTH)
            inv_res = invite_family_hub_members(
                api_key=api_key,
                id_token=tokens["id_token"],
                access_token=tokens["access_token"],
                group_id=group_id,
                member_id_parent=member_id,
                members=[{"msisdn": new_msisdn, "name": new_name}]
            )
            if inv_res.get("code") == "000" and inv_res.get("status") == "SUCCESS":
                render_alert("Undangan berhasil dikirimkan!", level="success", width=WIDTH)
            else:
                inv_msg = inv_res.get("message", "Gagal mengundang")
                render_alert(f"Gagal mengundang anggota: {inv_msg}", level="error", width=WIDTH)
            tui_pause()
        elif choice == "3":
            clear_screen()
            render_header("GANTI NAMA ANGGOTA", breadcrumb="engsel ❯ Family Hub ❯ Rename", width=WIDTH)
            for idx, m in enumerate(members_list, 1):
                print(p_line(bg_spaces(2) + badge(str(idx), C_PRI) + bg_spaces(1) + C_WHI(f"{m.get('member_name')} ({m.get('msisdn')})"), len(f"  [{idx:>2}] {m.get('member_name')} ({m.get('msisdn')})"), width=WIDTH))
            print(render_empty_line(width=WIDTH))
            print(render_box_bottom(width=WIDTH))
            print()
            sel = tui_input("Nomor anggota yang ingin diubah").strip()
            try:
                sel_idx = int(sel) - 1
                target_m = members_list[sel_idx]
                new_alias = tui_input(f"Nama baru untuk {target_m.get('member_name')}").strip()
                if new_alias:
                    rn_res = change_family_hub_member_name(
                        api_key=api_key,
                        id_token=tokens["id_token"],
                        group_id=group_id,
                        member_id=member_id,
                        target_member_id=target_m.get("member_id", ""),
                        name=new_alias
                    )
                    if rn_res.get("code") == "000" and rn_res.get("status") == "SUCCESS":
                        render_alert("Nama anggota berhasil diperbarui!", level="success", width=WIDTH)
                    else:
                        render_alert(f"Gagal mengganti nama: {rn_res.get('message', 'Error')}", level="error", width=WIDTH)
            except Exception:
                render_alert("Pilihan nomor tidak valid.", level="error", width=WIDTH)
            tui_pause()
        elif choice == "4":
            if is_owner:
                clear_screen()
                render_header("KELUARKAN ANGGOTA", breadcrumb="engsel ❯ Family Hub ❯ Hapus", width=WIDTH)
                eligible_members = [m for m in members_list if m.get("member_role") != "PARENT"]
                for idx, m in enumerate(eligible_members, 1):
                    print(p_line(bg_spaces(2) + badge(str(idx), C_DAN) + bg_spaces(1) + C_WHI(f"{m.get('member_name')} ({m.get('msisdn')})"), len(f"  [{idx:>2}] {m.get('member_name')} ({m.get('msisdn')})"), width=WIDTH))
                print(render_empty_line(width=WIDTH))
                print(render_box_bottom(width=WIDTH))
                print()
                sel = tui_input("Nomor anggota yang ingin dikeluarkan").strip()
                try:
                    sel_idx = int(sel) - 1
                    target_m = eligible_members[sel_idx]
                    if tui_confirm(f"Yakin ingin mengeluarkan {target_m.get('member_name')}?", default=False):
                        rm_res = remove_family_hub_member(
                            api_key=api_key,
                            id_token=tokens["id_token"],
                            group_id=group_id,
                            member_id=target_m.get("member_id", ""),
                            member_id_parent=member_id,
                            is_last_member=(len(members_list) <= 2)
                        )
                        if rm_res.get("code") == "000" and rm_res.get("status") == "SUCCESS":
                            render_alert("Anggota berhasil dikeluarkan dari grup.", level="success", width=WIDTH)
                        else:
                            render_alert(f"Gagal mengeluarkan: {rm_res.get('message', 'Error')}", level="error", width=WIDTH)
                except Exception:
                    render_alert("Pilihan tidak valid.", level="error", width=WIDTH)
                tui_pause()
            else:
                show_group_activities(api_key, tokens["id_token"], group_id)
        elif choice == "5":
            if is_owner:
                new_gname = tui_input("Nama grup yang baru").strip()
                if new_gname:
                    chg_res = change_family_hub_group_name(
                        api_key=api_key,
                        id_token=tokens["id_token"],
                        group_id=group_id,
                        member_id_parent=member_id,
                        name=new_gname
                    )
                    if chg_res.get("code") == "000" and chg_res.get("status") == "SUCCESS":
                        render_alert("Nama grup berhasil diubah!", level="success", width=WIDTH)
                    else:
                        render_alert(f"Gagal mengubah nama: {chg_res.get('message', 'Error')}", level="error", width=WIDTH)
                tui_pause()
            else:
                show_family_packages(api_key, tokens["id_token"], tokens.get("access_token", ""))
        elif choice == "6":
            if is_owner:
                show_group_activities(api_key, tokens["id_token"], group_id)
            else:
                if tui_confirm("Yakin ingin keluar dari grup Family Hub ini?", default=False):
                    lv_res = leave_family_hub_group(
                        api_key=api_key,
                        id_token=tokens["id_token"],
                        group_id=group_id,
                        member_id=member_id,
                        member_id_parent="",
                        is_last_member=(len(members_list) <= 1)
                    )
                    if lv_res.get("code") == "000" and lv_res.get("status") == "SUCCESS":
                        render_alert("Anda telah berhasil keluar dari grup.", level="success", width=WIDTH)
                    else:
                        render_alert(f"Gagal keluar: {lv_res.get('message', 'Error')}", level="error", width=WIDTH)
                    tui_pause()
        elif choice == "7" and is_owner:
            show_family_packages(api_key, tokens["id_token"], tokens.get("access_token", ""))
        elif choice == "8" and is_owner:
            render_alert("PERINGATAN: Membubarkan grup akan menghapus seluruh anggota dan menghentikan pembagian kuota!", level="error", width=WIDTH)
            confirm = tui_input("Ketik 'BUBARKAN' untuk konfirmasi").strip()
            if confirm == "BUBARKAN":
                dis_res = disband_family_hub_group(api_key=api_key, id_token=tokens["id_token"], group_id=group_id, member_id_parent=member_id)
                if dis_res.get("code") == "000" and dis_res.get("status") == "SUCCESS":
                    render_alert("Grup Family Hub telah dibubarkan.", level="success", width=WIDTH)
                else:
                    render_alert(f"Gagal membubarkan: {dis_res.get('message', 'Error')}", level="error", width=WIDTH)
                tui_pause()
        elif choice in ("00", "0", "q", "exit"):
            break
        else:
            render_alert("Pilihan tidak valid.", level="warning", width=WIDTH)
            tui_pause()
