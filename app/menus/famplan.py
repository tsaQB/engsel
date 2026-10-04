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
    format_msisdn,
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
from app.client.famplan import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn
from app.util import normalize_msisdn

def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        render_alert("Mengambil data Akrab Organizer dari server...", level="info", width=WIDTH)
        res = get_family_data(api_key, tokens)
        if not res or not res.get("data"):
            render_alert("Gagal mengambil data keluarga dari server.", level="error", width=WIDTH)
            tui_pause()
            return
        
        family_detail = res["data"]
        member_info = family_detail.get("member_info", {})
        plan_type = member_info.get("plan_type", "")
        
        if not plan_type:
            render_alert("Akun Anda bukan merupakan Pengelola (Organizer) Paket Akrab.", level="warning", width=WIDTH)
            tui_pause()
            return
        
        parent_msisdn = member_info.get("parent_msisdn", "-")
        members = member_info.get("members", [])
        empty_slots = [slot for slot in members if not slot.get("msisdn")]
        
        total_quota_byte = member_info.get("total_quota", 0)
        remaining_quota_byte = member_info.get("remaining_quota", 0)
        
        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)
        
        end_date_ts = member_info.get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%d %b %Y") if end_date_ts else "-"
        
        clear_screen()
        render_header("AKRAB ORGANIZER", breadcrumb="engsel ❯ Akrab", width=WIDTH)
        
        # 1. Ringkasan Grup
        print(render_hdr_line("INFORMASI GRUP AKRAB", width=WIDTH))
        print(render_kv_line("Paket Akrab", plan_type, C_WHI, width=WIDTH))
        print(render_kv_2col("Pengelola", format_msisdn(parent_msisdn), C_WHI, "Berlaku s/d", end_date, C_DIM, col2=28, width=WIDTH))
        print(render_kv_2col("Kuota Sisa", remaining_quota_human, C_AMB, "Total Kuota", total_quota_human, C_MUT, col2=28, width=WIDTH))
        
        # Visual Bar Kuota Bersama
        pct = int((remaining_quota_byte / total_quota_byte) * 100) if total_quota_byte > 0 else 0
        bar_w = 20
        filled = int((pct / 100) * bar_w)
        empty = bar_w - filled
        bar_str = "█" * filled + "░" * empty
        row_bar = bg_spaces(2) + C_MUT("Sisa Kuota: ") + C_SUC(f"[{bar_str}] ") + C_WHI(f"{pct}%")
        print(p_line(row_bar, len(f"  Sisa Kuota: [{bar_str}] {pct}%"), width=WIDTH))
        print(render_empty_line(width=WIDTH))

        # 2. Tabel Anggota
        filled_count = len(members) - len(empty_slots)
        print(render_box_divider(title=f"SLOT ANGGOTA ({filled_count}/{len(members)})", width=WIDTH))
        
        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "")
            is_empty = not bool(msisdn)
            
            alias = member.get("alias", "-")
            member_type = member.get("member_type", "MEMBER")
            
            quota_alloc_b = member.get("usage", {}).get("quota_allocated", 0)
            quota_used_b = member.get("usage", {}).get("quota_used", 0)
            alloc_fmt = format_quota_byte(quota_alloc_b)
            used_fmt = format_quota_byte(quota_used_b)
            
            add_chances = member.get("add_chances", 0)
            total_chances = member.get("total_add_chances", 0)

            k_badge = badge(str(idx), C_PRI if not is_empty else C_DIM)
            
            if is_empty:
                disp_name = "<Slot Kosong>"
                row1_p = f"  [{idx:>2}] {disp_name}"
                row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_DIM(disp_name)
                print(p_line(row1, len(row1_p), width=WIDTH))
            else:
                m_num = format_msisdn(msisdn)
                role_label = "[PARENT]" if member_type == "PARENT" else f"[{alias}]"
                avail_w = (WIDTH - 2) - len(f"  [{idx:>2}] {m_num} ") - 2
                role_trunc = truncate_str(role_label, avail_w)
                
                row1_p = f"  [{idx:>2}] {m_num} {role_trunc}"
                row1 = bg_spaces(2) + k_badge + bg_spaces(1) + C_WHI(m_num) + bg_spaces(1) + C_PRI(role_trunc)
                print(p_line(row1, len(row1_p), width=WIDTH))

                row2_p = f"      Pemakaian: {used_fmt} / {alloc_fmt} • Ganti: {add_chances}/{total_chances}"
                row2 = bg_spaces(6) + C_MUT("Pemakaian: ") + C_AMB(f"{used_fmt} / {alloc_fmt}") + C_DIM(f" • Ganti: {add_chances}/{total_chances}")
                print(p_line(row2, len(row2_p), width=WIDTH))

            if idx < len(members):
                print(render_empty_line(width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_divider(title="AKSI PENGELOLA", width=WIDTH))
        
        line_chg = bg_spaces(2) + badge("1", C_PRI) + bg_spaces(1) + C_WHI("Ganti / Masukkan Anggota ke Slot Kosong")
        print(p_line(line_chg, len("  [ 1] Ganti / Masukkan Anggota ke Slot Kosong"), width=WIDTH))
        
        line_lim = bg_spaces(2) + badge("limit N MB", C_AMB) + bg_spaces(1) + C_MUT("Atur batas kuota (contoh: limit 2 1024)")
        print(p_line(line_lim, len("  [limit N MB] Atur batas kuota (contoh: limit 2 1024)"), width=WIDTH))
        
        line_del = bg_spaces(2) + badge("del N", C_DAN) + bg_spaces(1) + C_DAN("Hapus anggota dari slot (contoh: del 2)")
        print(p_line(line_del, len("  [del N] Hapus anggota dari slot (contoh: del 2)"), width=WIDTH))
        
        line_back = bg_spaces(2) + badge("00", C_DAN) + bg_spaces(1) + C_DAN("Kembali ke Menu Utama")
        print(p_line(line_back, len("  [00] Kembali ke Menu Utama"), width=WIDTH))

        print(render_empty_line(width=WIDTH))
        print(render_box_bottom(footer="Ketik nomor/perintah", width=WIDTH))
        print()

        choice = tui_input("Perintah Akrab").strip()
        if choice in ("00", "q", "exit"):
            in_family_menu = False
            return
        elif choice == "1":
            slot_idx = tui_input("Nomor Slot").strip()
            target_raw = tui_input("Nomor HP Anggota Baru (contoh: 08123456789)").strip()
            target_msisdn = normalize_msisdn(target_raw)
            parent_alias = tui_input("Nama/Panggilan Anda (Pengelola)", default="Ayah").strip()
            child_alias = tui_input("Nama/Panggilan Anggota Baru", default="Anggota").strip()
            
            try:
                slot_idx_int = int(slot_idx)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    render_alert("Nomor slot tidak valid.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                if members[slot_idx_int - 1].get("msisdn"):
                    render_alert("Slot tersebut sudah terisi! Hapus terlebih dahulu jika ingin mengganti.", level="warning", width=WIDTH)
                    tui_pause()
                    continue
                
                family_member_id = members[slot_idx_int - 1]["family_member_id"]
                slot_id = members[slot_idx_int - 1]["slot_id"]
                
                render_alert(f"Memvalidasi nomor {format_msisdn(target_msisdn)}...", level="info", width=WIDTH)
                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                if validation_res.get("status", "").lower() != "success":
                    render_alert(f"Validasi nomor gagal: {validation_res.get('message', 'Nomor tidak valid')}", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                target_role = validation_res.get("data", {}).get("family_plan_role", "")
                if target_role != "NO_ROLE":
                    render_alert(f"Nomor tersebut sudah tergabung dalam grup keluarga lain dengan role {target_role}.", level="error", width=WIDTH)
                    tui_pause()
                    continue

                if not tui_confirm(f"Masukkan {format_msisdn(target_msisdn)} ke slot {slot_idx_int}?", default=True):
                    render_alert("Operasi dibatalkan.", level="info", width=WIDTH)
                    tui_pause()
                    continue
                
                render_alert("Mendaftarkan anggota ke grup Akrab...", level="info", width=WIDTH)
                change_member_res = change_member(
                    api_key,
                    tokens,
                    parent_alias,
                    child_alias,
                    slot_id,
                    family_member_id,
                    target_msisdn,
                )
                if change_member_res.get("status") == "SUCCESS":
                    render_alert("Anggota berhasil didaftarkan ke grup Akrab!", level="success", width=WIDTH)
                else:
                    render_alert(f"Gagal mendaftarkan anggota: {change_member_res.get('message', 'Server error')}", level="error", width=WIDTH)
                tui_pause()
            except ValueError:
                render_alert("Nomor slot harus berupa angka.", level="error", width=WIDTH)
                tui_pause()
        elif choice.startswith("del "):
            _, slot_num = choice.split(" ", 1)
            try:
                slot_idx_int = int(slot_num)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    render_alert("Nomor slot tidak valid.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                member = members[slot_idx_int - 1]
                if not member.get("msisdn"):
                    render_alert("Slot tersebut sudah kosong.", level="warning", width=WIDTH)
                    tui_pause()
                    continue
                
                if not tui_confirm(f"Hapus {format_msisdn(member.get('msisdn'))} dari slot {slot_idx_int}?", default=False):
                    render_alert("Penghapusan dibatalkan.", level="info", width=WIDTH)
                    tui_pause()
                    continue
                
                render_alert("Memproses penghapusan anggota...", level="info", width=WIDTH)
                family_member_id = member["family_member_id"]
                res = remove_member(api_key, tokens, family_member_id)
                if res.get("status") == "SUCCESS":
                    render_alert("Anggota berhasil dikeluarkan dari slot.", level="success", width=WIDTH)
                else:
                    render_alert(f"Gagal menghapus anggota: {res.get('message', 'Server error')}", level="error", width=WIDTH)
                tui_pause()
            except ValueError:
                render_alert("Nomor slot harus berupa angka.", level="error", width=WIDTH)
                tui_pause()
        elif choice.startswith("limit "):
            parts = choice.split()
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                slot_idx_int = int(parts[1])
                new_quota_mb = int(parts[2])
                
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    render_alert("Nomor slot tidak valid.", level="error", width=WIDTH)
                    tui_pause()
                    continue
                
                member = members[slot_idx_int - 1]
                if not member.get("msisdn"):
                    render_alert("Slot tersebut kosong, tidak dapat mengatur batas kuota.", level="warning", width=WIDTH)
                    tui_pause()
                    continue
                
                family_member_id = member["family_member_id"]
                orig_alloc = member.get("usage", {}).get("quota_allocated", 0)
                new_alloc = new_quota_mb * 1024 * 1024
                
                render_alert(f"Mengatur batas kuota slot {slot_idx_int} menjadi {new_quota_mb} MB...", level="info", width=WIDTH)
                res = set_quota_limit(api_key, tokens, orig_alloc, new_alloc, family_member_id)
                if res.get("status") == "SUCCESS":
                    render_alert(f"Batas kuota berhasil diubah menjadi {new_quota_mb} MB.", level="success", width=WIDTH)
                else:
                    render_alert(f"Gagal mengatur limit kuota: {res.get('message', 'Server error')}", level="error", width=WIDTH)
                tui_pause()
            else:
                render_alert("Format salah! Gunakan: limit <slot> <MB> (contoh: limit 2 1024)", level="warning", width=WIDTH)
                tui_pause()
        else:
            render_alert("Perintah tidak valid. Silakan coba lagi.", level="warning", width=WIDTH)
            tui_pause()