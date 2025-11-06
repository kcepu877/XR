import os
import configparser
import random
import sys
import time
from datetime import datetime
from app.menus.util import pause, clear_sc
from app.menus.util_helper import print_panel, get_rupiah, clear_screen
from app.client.engsel import get_balance, get_profile, get_quota
from app.client.engsel2 import get_tiering_info, segments
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.family_grup import show_family_menu
from app.menus.donate import show_donate_menu
from app.menus.theme import show_theme_menu
from app.config.theme_config import get_theme
from app.menus.points import run_point_exchange
from app.menus.special import show_special_for_you_menu
from app.menus.bundle import show_bundle_menu
from app.menus.purchase import purchase_by_family, purchase_loop
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.family_grup import show_family_menu
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import MINIMAL_DOUBLE_HEAD
from rich.align import Align
from rich.text import Text

console = Console()
theme = get_theme()
cached_user_context = None
last_fetch_time = 0

def ensure_git():
    root_path = os.path.dirname(os.path.abspath(__file__))
    git_folder = os.path.join(root_path, ".git")
    git_config = os.path.join(git_folder, "config")
    expected_url = "https://github.com/kcepu877/xr"

    if not os.path.exists(git_folder):
        text = Text()
        text.append("❌ Script ini hanya bisa dijalankan dari hasil git clone.\n", style="bold red")
        text.append("Pastikan Anda meng-clone dari repository resmi.\n", style="yellow")
        text.append(f"  git clone {expected_url}", style="bold green")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    if not os.path.exists(git_config):
        text = Text()
        text.append("❌ Script ini tidak memiliki konfigurasi git yang valid.\n", style="bold red")
        text.append("File .git/config tidak ditemukan.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    config = configparser.RawConfigParser(strict=False)
    config.read(git_config)

    if not config.sections():
        text = Text()
        text.append("❌ Gagal membaca konfigurasi git.\n", style="bold red")
        text.append("File .git/config mungkin rusak atau tidak valid.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    if 'remote "origin"' not in config:
        text = Text()
        text.append("❌ Repo ini tidak memiliki remote origin.\n", style="bold red")
        text.append("Pastikan Anda meng-clone dari repository resmi.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    origin_url = config['remote "origin"'].get("url", "").strip()

    if origin_url != expected_url:
        text = Text()
        text.append("⚠️ Repo ini tidak berasal dari sumber resmi.\n", style="bold yellow")
        text.append(f"URL saat ini: {origin_url}\n", style="yellow")
        text.append("Silakan clone ulang dari:\n", style="yellow")
        text.append(f"  git clone {expected_url}", style="bold green")
        console.print(Panel(text, title="Validasi", border_style="yellow"))
        sys.exit(1)

def fetch_user_context(force_refresh=False):
    global cached_user_context, last_fetch_time
    now = time.time()

    if not force_refresh and cached_user_context and now - last_fetch_time < 60:
        return cached_user_context

    active_user = AuthInstance.get_active_user()
    if not active_user:
        return None

    api_key = AuthInstance.api_key
    tokens = active_user["tokens"]
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    balance_data = get_balance(api_key, id_token)
    balance_remaining = balance_data.get("remaining", 0)
    balance_expired_at = balance_data.get("expired_at", 0)

    quota = get_quota(api_key, id_token) or {}
    remaining = quota.get("remaining", 0)
    total = quota.get("total", 0)
    has_unlimited = quota.get("has_unlimited", False)

    if total > 0 or has_unlimited:
        remaining_gb = remaining / 1e9
        total_gb = total / 1e9
        display_quota = (
            f"{remaining_gb:.2f}/{total_gb:.2f} GB (Unlimited)"
            if has_unlimited else f"{remaining_gb:.2f}/{total_gb:.2f} GB"
        )
    else:
        display_quota = "-"

    profile_data = get_profile(api_key, access_token, id_token)
    sub_id = profile_data["profile"].get("subscriber_id", "-")
    sub_type = profile_data["profile"].get("subscription_type", "-")

    point_info = "Points: N/A | Tier: N/A"
    if sub_type == "PREPAID":
        tiering_data = get_tiering_info(api_key, tokens)
        tier = tiering_data.get("tier", 0)
        current_point = tiering_data.get("current_point", 0)
        point_info = f"Points: {current_point} | Tier: {tier}"

    segments_data = segments(api_key, id_token, access_token, balance_remaining) or {}

    cached_user_context = {
        "api_key": api_key,
        "tokens": tokens,
        "number": active_user["number"],
        "subscriber_id": sub_id,
        "subscription_type": sub_type,
        "balance": balance_remaining,
        "balance_expired_at": balance_expired_at,
        "point_info": point_info,
        "display_quota": display_quota,
        "segments": segments_data
    }
    last_fetch_time = now
    return cached_user_context


def show_main_menu(profile):
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    pulsa_str = get_rupiah(profile["balance"])
    theme = get_theme()

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_row(" Nomor", f": 📞 [bold]{profile['number']}[/]")
    info_table.add_row(" Type", f": 🧾 {profile['subscription_type']} ({profile['subscriber_id']})")
    info_table.add_row(" Pulsa", f": 💰 Rp [{theme['text_money']}]{pulsa_str}[/{theme['text_money']}]")
    info_table.add_row(" Aktif", f": ⏳ [{theme['text_date']}]{expired_at_dt}[/{theme['text_date']}]")
    info_table.add_row(" Tiering", f": 🏅 [{theme['text_date']}]{profile['point_info']}[/{theme['text_date']}]")

    console.print(Panel(info_table, title=f"[{theme['text_title']}]✨Informasi Akun✨[/]", border_style=theme["border_info"], padding=(1, 2), expand=True))

    menu = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu.add_column("Kode", style=theme["text_key"], justify="right", width=6)
    menu.add_column("Menu", style=theme["text_body"])
    menu.add_row("1", "🔐 Login/Ganti akun")
    menu.add_row("2", "📑 Lihat Paket Saya")
    menu.add_row("3", "🔥 Beli Paket Hot Promo")
    menu.add_row("4", "🔥 Beli Paket Hot Promo-2")
    menu.add_row("5", "💵 Beli Paket via Option Code")
    menu.add_row("6", "💴 Beli Paket via Family Code")
    menu.add_row("7", "🔁 Beli Semua Paket di Family Code")
    menu.add_row("8", "💾 Simpan/Kelola Family Code")
    menu.add_row("9", "👨‍👩‍👧‍👦 Family Plan/Akrab Organizer")
    menu.add_row("10", "🌀 Circle Info")
    menu.add_row("11", "🏪 Store Segments")
    menu.add_row("12", "📚 Store Family List")
    menu.add_row("13", "🛒 Store Packages")          
    menu.add_row("N", "🔔 Notifikasi")
    menu.add_row("00", "⭐ Bookmark Paket")
    menu.add_row("77", f"[{theme['border_warning']}]📢 Info Unlock Code [/]")  
    menu.add_row("88", f"[{theme['text_sub']}]🎨 Ganti Tema CLI [/]")
    menu.add_row("99", f"[{theme['text_err']}]⛔ Tutup aplikasi [/]")

    console.print(Panel(menu, title=f"[{theme['text_title']}]📋 Menu Utama[/]", border_style=theme["border_primary"], padding=(0, 1), expand=True))

 def build_profile():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        return None

    balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
    profile_data = get_profile(AuthInstance.api_key, active_user["tokens"]["access_token"], active_user["tokens"]["id_token"])
    sub_type = profile_data["profile"]["subscription_type"]

    point_info = "Points: N/A | Tier: N/A"
    if sub_type == "PREPAID":
        tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
        tier = tiering_data.get("tier", 0)
        current_point = tiering_data.get("current_point", 0)
        point_info = f"Points: {current_point} | Tier: {tier}"

    return {
        "number": active_user["number"],
        "subscriber_id": profile_data["profile"]["subscriber_id"],
        "subscription_type": sub_type,
        "balance": balance.get("remaining"),
        "balance_expired_at": balance.get("expired_at"),
        "point_info": point_info
    }

def main():
    while True:
        active_user = AuthInstance.get_active_user()
        if not active_user:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print_panel("⚠️ Error", "Tidak ada akun yang dipilih.")
            continue

        profile = build_profile()
        if not profile:
            print_panel("⚠️ Error", "Gagal membangun profil pengguna.")
            continue

        clear_screen()
        theme = get_theme()
        show_main_menu(profile)
        choice = console.input(f"[{theme['text_sub']}]💥Pilih menu:[/{theme['text_sub']}] ").strip().lower()

        if choice == "1":
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print_panel("⚠️ Error", "Tidak ada akun yang dipilih.")

        elif choice == "2":
            fetch_my_packages()

        elif choice == "3":
            show_hot_menu()

        elif choice == "4":
            show_hot_menu2()

        elif choice == "5":
            option_code = console.input(f"[{theme['text_sub']}]Masukkan Option Code:[/{theme['text_sub']}] ").strip()
            if option_code != "99":
                show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)

        elif choice == "6":
            family_code = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
            if family_code != "99":
                get_packages_by_family(family_code)

        elif choice == "7":
            family_code = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
            if family_code == "99":
                continue
            start_from_option = console.input(f"[{theme['text_sub']}]Mulai dari nomor option (default 1):[/{theme['text_sub']}] ").strip()
            try:
                start_from_option = int(start_from_option)
            except ValueError:
                start_from_option = 1
            use_decoy = console.input(f"[{theme['text_sub']}]Gunakan decoy? (y/n):[/{theme['text_sub']}] ").strip().lower() == 'y'
            pause_on_success = console.input(f"[{theme['text_sub']}]Pause setiap sukses? (y/n):[/{theme['text_sub']}] ").strip().lower() == 'y'
            delay_seconds = console.input(f"[{theme['text_sub']}]Delay antar pembelian (detik):[/{theme['text_sub']}] ").strip()
            try:
                delay_seconds = int(delay_seconds)
            except ValueError:
                delay_seconds = 0
            purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)

        elif choice == "8":
            show_family_menu()

        elif choice == "9":
            show_family_info(AuthInstance.api_key, active_user["tokens"])

        elif choice == "10":
            show_circle_info(AuthInstance.api_key, active_user["tokens"])

        elif choice == "11":
            is_enterprise = console.input(f"[{theme['text_sub']}]Enterprise store? (y/n):[/{theme['text_sub']}] ").strip().lower() == 'y'
            show_store_segments_menu(is_enterprise)

        elif choice == "12":
            is_enterprise = console.input(f"[{theme['text_sub']}]Enterprise? (y/n):[/{theme['text_sub']}] ").strip().lower() == 'y'
            show_family_list_menu(profile['subscription_type'], is_enterprise)

        elif choice == "13":
            is_enterprise = console.input(f"[{theme['text_sub']}]Enterprise? (y/n):[/{theme['text_sub']}] ").strip().lower() == 'y'
            show_store_packages_menu(profile['subscription_type'], is_enterprise)

        elif choice == "77":
            show_donate_menu()

        elif choice == "88":
            show_theme_menu()

        elif choice == "00":
            show_bookmark_menu()

        elif choice == "n":
            show_notification_menu()

        elif choice == "s":
            enter_sentry_mode()

        elif choice == "99":
            console.print(Panel("👋 Sampai jumpa!", border_style=theme["border_err"]))
            sys.exit(0)

        else:
            print_panel("⚠️ Error", "Pilihan tidak valid.")

             
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_panel("👋 Keluar", "Aplikasi dihentikan oleh pengguna.")
        sys.exit(0)
