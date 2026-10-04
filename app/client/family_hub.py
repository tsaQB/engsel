from app.client.engsel import send_api_request
from app.client.encrypt import encrypt_circle_msisdn

def _ensure_encrypted_msisdn(api_key: str, msisdn: str) -> str:
    if not msisdn:
        return ""
    if len(msisdn) > 20:
        return msisdn
    return encrypt_circle_msisdn(api_key, msisdn)

def get_family_hub_eligibility(api_key: str, id_token: str) -> dict:
    """Cek kelayakan nomor untuk membuat grup Family Hub"""
    payload = {
        "type": "CREATE_GROUP",
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/check-eligibility", payload, id_token)

def get_family_hub_status(api_key: str, id_token: str) -> dict:
    """Cek status grup Family Hub nomor saat ini (NONE, ACTIVE, WAITING_CONFIRMATION)"""
    payload = {
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/status", payload, id_token)

def get_family_hub_members(api_key: str, id_token: str, group_id: str) -> dict:
    """Ambil informasi grup dan detail seluruh anggota beserta kuotanya"""
    payload = {
        "family_id": group_id,
        "is_get_from_cache": False,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "sharings/api/v8/family-hub/members", payload, id_token)

def create_family_hub_group(
    api_key: str,
    id_token: str,
    access_token: str,
    group_name: str,
    parent_name: str,
    members: list
) -> dict:
    """
    Buat grup Family Hub baru.
    members: list of dict [{"msisdn": "628...", "name": "Nama"}]
    """
    enc_members = []
    for m in members:
        enc_members.append({
            "msisdn": _ensure_encrypted_msisdn(api_key, m.get("msisdn", "")),
            "name": m.get("name", "")
        })

    payload = {
        "access_token": access_token,
        "group_name": group_name,
        "parent_name": parent_name,
        "members": enc_members,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/create", payload, id_token)

def invite_family_hub_members(
    api_key: str,
    id_token: str,
    access_token: str,
    group_id: str,
    member_id_parent: str,
    members: list
) -> dict:
    """
    Undang anggota baru ke dalam grup Family Hub yang sudah ada.
    members: list of dict [{"msisdn": "628...", "name": "Nama"}]
    """
    enc_members = []
    for m in members:
        enc_members.append({
            "msisdn": _ensure_encrypted_msisdn(api_key, m.get("msisdn", "")),
            "name": m.get("name", "")
        })

    payload = {
        "access_token": access_token,
        "group_id": group_id,
        "member_id_parent": member_id_parent,
        "members": enc_members,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/members/invite", payload, id_token)

def remove_family_hub_member(
    api_key: str,
    id_token: str,
    group_id: str,
    member_id: str,
    member_id_parent: str,
    is_last_member: bool = False
) -> dict:
    """Hapus / keluarkan anggota dari grup Family Hub"""
    payload = {
        "group_id": group_id,
        "member_id": member_id,
        "member_id_parent": member_id_parent,
        "is_last_member": is_last_member,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/members/remove", payload, id_token)

def leave_family_hub_group(
    api_key: str,
    id_token: str,
    group_id: str,
    member_id: str,
    member_id_parent: str,
    is_last_member: bool = False
) -> dict:
    """Keluar dari grup Family Hub"""
    payload = {
        "group_id": group_id,
        "member_id": member_id,
        "member_id_parent": member_id_parent,
        "is_last_member": is_last_member,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/leave", payload, id_token)

def disband_family_hub_group(
    api_key: str,
    id_token: str,
    group_id: str,
    member_id_parent: str
) -> dict:
    """Membubarkan grup Family Hub (hanya pengelola/owner)"""
    payload = {
        "group_id": group_id,
        "member_id_parent": member_id_parent,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/disband", payload, id_token)

def change_family_hub_group_name(
    api_key: str,
    id_token: str,
    group_id: str,
    member_id_parent: str,
    name: str
) -> dict:
    """Ganti nama grup Family Hub"""
    payload = {
        "group_id": group_id,
        "member_id_parent": member_id_parent,
        "name": name,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/change-name", payload, id_token)

def change_family_hub_member_name(
    api_key: str,
    id_token: str,
    group_id: str,
    member_id: str,
    target_member_id: str,
    name: str
) -> dict:
    """Ganti nama panggilan anggota di grup"""
    payload = {
        "group_id": group_id,
        "member_id": member_id,
        "target_member_id": target_member_id,
        "name": name,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/members/change-name", payload, id_token)

def accept_family_hub_invitation(
    api_key: str,
    id_token: str,
    access_token: str,
    group_id: str,
    member_id: str
) -> dict:
    """Menerima undangan untuk bergabung ke grup Family Hub"""
    payload = {
        "access_token": access_token,
        "group_id": group_id,
        "member_id": member_id,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/accept-invitation", payload, id_token)

def get_family_hub_activities(api_key: str, id_token: str, group_id: str) -> dict:
    """Ambil riwayat aktivitas dan pemakaian kuota grup"""
    payload = {
        "group_id": group_id,
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/groups/activity", payload, id_token)

def get_family_hub_packages(api_key: str, id_token: str, access_token: str = "") -> dict:
    """Ambil daftar paket / Family Booster yang tersedia di store"""
    payload = {
        "is_enterprise": False,
        "lang": "id"
    }
    if access_token:
        payload["access_token"] = access_token
    return send_api_request(api_key, "store/api/v8/segments/family-hub", payload, id_token)

def validate_family_hub_member(api_key: str, id_token: str, msisdn: str) -> dict:
    """Validasi apakah nomor calon anggota memenuhi syarat"""
    payload = {
        "msisdn": _ensure_encrypted_msisdn(api_key, msisdn),
        "is_enterprise": False,
        "lang": "id"
    }
    return send_api_request(api_key, "family-hub/api/v8/members/validate", payload, id_token)
