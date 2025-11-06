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


def show_main_menu(profile, display_quota, segments):
    clear_screen()
    ensure_git()
    theme = get_theme()
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d %H:%M:%S")
    pulsa_str = get_rupiah(profile["balance"])

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_row(" Nomor", f": 📞 [bold {theme['text_body']}]{profile['number']}[/]")
    info_table.add_row(" Type", f": 🧾 [{theme['text_body']}]{profile['subscription_type']} ({profile['subscriber_id']})[/]")
    info_table.add_row(" Pulsa", f": 💰 Rp [{theme['text_money']}]{pulsa_str}[/]")
    info_table.add_row(" Kuota", f": 📊 [{theme['text_date']}]{display_quota}[/]")
    info_table.add_row(" Tiering", f": 🏅 [{theme['text_date']}]{profile['point_info']}[/]")
    info_table.add_row(" Masa Aktif", f": ⏳ [{theme['text_date']}]{expired_at_dt}[/]")

    console.print(Panel(info_table, title=f"[{theme['text_title']}]✨Informasi Akun✨[/]", title_align="center", border_style=theme["border_info"], padding=(1, 2), expand=True))

    special_packages = segments.get("special_packages", [])
    if special_packages:
        best = random.choice(special_packages)

        name = best.get("name", "-")
        diskon_percent = best.get("diskon_percent", 0)
        diskon_price = best.get("diskon_price", 0)
        original_price = best.get("original_price", 0)
        emoji_diskon = "💸" if diskon_percent >= 50 else ""
        emoji_kuota = "🔥" if best.get("kuota_gb", 0) >= 100 else ""

        special_text = (
            f"[bold {theme['text_title']}]🔥🔥🔥 Paket Special Untukmu! 🔥🔥🔥[/{theme['text_title']}]\n\n"
            f"[{theme['text_body']}]{emoji_kuota} {name}[/{theme['text_body']}]\n"
            f"Diskon {diskon_percent}% {emoji_diskon} "
            f"Rp[{theme['text_err']}][strike]{get_rupiah(original_price)}[/strike][/{theme['text_err']}] ➡️ "
            f"Rp[{theme['text_money']}]{get_rupiah(diskon_price)}[/{theme['text_money']}]"
        )

        panel_width = console.size.width
        console.print(
            Panel(
                Align.center(special_text),
                border_style=theme["border_warning"],
                padding=(0, 2),
                width=panel_width
            )
        )

        console.print(Align.center(
            f"[{theme['text_sub']}]Pilih [S] untuk lihat semua paket spesial[/{theme['text_sub']}]"
        ))

    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=theme["text_key"], width=6)
    menu_table.add_column("Aksi", style=theme["text_body"])
    #menu_table.add_row("S", "🎁 Lihat Paket Special For You")
    menu_table.add_row("1", "🔐 Login/Ganti akun")
    menu_table.add_row("2", "📑 Lihat Paket Saya")
    menu_table.add_row("3", "📜 Riwayat Transaksi")
    menu_table.add_row("4", "🎁 Tukar Point Reward")
    menu_table.add_row("5", "🔥 Beli Paket Hot Promo")
    menu_table.add_row("6", "🔥 Beli Paket Hot Promo-2")
    menu_table.add_row("7", "🔍 Beli Paket Berdasarkan Family Code")
    menu_table.add_row("8", "💾 Simpan/Kelola Family Code")
    menu_table.add_row("9", "🛒 Spesial For You")
    menu_table.add_row("10", "🛒 Bonus aktivasi")
    menu_table.add_row("11", "🛒 Bonus Flex Rp.0")
    menu_table.add_row("12", "🛒 Kuota Bersama Rp 0")
    menu_table.add_row("13", "🛒 Addon Hotrod/Xcs 8gb")
    menu_table.add_row("14", "🛒 Xcs Flex Ori")
    menu_table.add_row("15", "🛒 EduCoference Ori")
    menu_table.add_row("16", "🛒 Mastif Bundling Setahun")
    menu_table.add_row("17", "🛒 Paket XL Point")
    menu_table.add_row("18", "🛒 Paket Bonus MyRewards")
    menu_table.add_row("19", "🛒 Addon XCP 2GB")
    menu_table.add_row("20", "🛒 Addon XCP 15GB")
    menu_table.add_row("21", "🛒 Bebas Puas")
    menu_table.add_row("22", "🛒 XCP OLD 10GB")
    menu_table.add_row("23", "🛒 XCP VIP")
    menu_table.add_row("24", "🛒 Akrab 2Kb New")
    menu_table.add_row("25", "🛒 XCP GIFT")
    menu_table.add_row("26", "🛒 Addon XCP 1GB")
    menu_table.add_row("27", "🛒 Pilkada Damai Kuota")
    menu_table.add_row("28", "🛒 Bonus Akrab Rp 0")
    menu_table.add_row("29", "🛒 XC FLEX LENGKAP")
    menu_table.add_row("30", "🛒 Unli Turbo Xcs/Hotrod")
    menu_table.add_row("31", "🛒 Addon XCP 6GB")
    menu_table.add_row("32", "🛒 Family Hide Addon Prepaid")
    menu_table.add_row("33", "🛒 Add Slot Akrab")
    menu_table.add_row("34", "🛒 Akrab Full Versi")
    menu_table.add_row("35", "🛒 Akrab Big")
    menu_table.add_row("36", "🛒 Booster Akrab")
    menu_table.add_row("37", "🛒 Addon Akrab")
    menu_table.add_row("38", "🛒 XCS 8GB & 14GB")
    menu_table.add_row("39", "🛒 New Comer XCS 2GB & 4GB")
    menu_table.add_row("40", "🛒 XC FLEX LENGKAP V2")
    menu_table.add_row("41", "🛒 Paket Harian Rp 0")
    menu_table.add_row("42", "🛒 Paket Youtube Bonus")
    menu_table.add_row("43", "🛒 Xtra Combo Mini")
    menu_table.add_row("44", "🛒 Xcp 15gb")      
    menu_table.add_row("", "")
    menu_table.add_row("45", "🧪 Beli/Buat Paket Bundle (multi)")
    menu_table.add_row("46", "🛒 Beli Semua Paket dalam Family Code")
    menu_table.add_row("47", "🔁 Order berulang dari Family Code")
    menu_table.add_row("48", "👨‍👩‍👧‍👦 Family Plan / Akrab Organizer")
    menu_table.add_row("00", "⭐ Bookmark Paket")
    menu_table.add_row("", "")
    menu_table.add_row("77", f"[{theme['border_warning']}]📢 Info Unlock Code [/]")  
    menu_table.add_row("88", f"[{theme['text_sub']}]🎨 Ganti Tema CLI [/]")          
    menu_table.add_row("99", f"[{theme['text_err']}]⛔ Tutup aplikasi [/]")

    console.print(Panel(menu_table, title=f"[{theme['text_title']}]✨ Menu Utama ✨[/]", title_align="center", border_style=theme["border_primary"], padding=(0, 1), expand=True))


def main():
    global cached_user_context, last_fetch_time

    while True:
        user_context = fetch_user_context()

        if not user_context:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
                cached_user_context = None
                last_fetch_time = 0
                clear_screen()
                continue
            else:
                print_panel("⚠️ Error", "Tidak ada akun yang dipilih.")
                pause()
                continue

        theme = get_theme()
        show_main_menu(user_context, user_context["display_quota"], user_context["segments"])
        choice = console.input(f"[{theme['text_sub']}]Pilih menu:[/{theme['text_sub']}] ").strip().lower()

        match choice:
            case "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                    cached_user_context = None
                    last_fetch_time = 0
                    clear_screen()
                else:
                    print_panel("⚠️ Error", "Tidak ada akun yang dipilih.")
                    pause()

            case "2":
                fetch_my_packages()

            case "3":
                show_transaction_history(user_context["api_key"], user_context["tokens"])

            case "4":
                run_point_exchange(user_context["tokens"])

            case "5":
                show_hot_menu()

            case "6":
                show_hot_menu2()

            case "7":
                family_code = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
                if family_code != "99":
                    get_packages_by_family(family_code)

            case "8":
                show_family_menu()
                
            case "9":
                # Spesial For You  
                get_packages_by_family("6fda76ee-e789-4897-89fb-9114da47b805")
            case "10":
                # Bonus aktivasi  
                get_packages_by_family("0069ab97-3e54-41ef-87ea-807621d1922c")
            case "11":
                # Bonus Flex Rp.0  
                get_packages_by_family("1b42d4f6-a76e-4986-aa5c-e2979da952f4")
            case "12":
                # Kuota Bersama Rp 0  
                get_packages_by_family("434a1449-1d18-43f8-b059-10b3d5e3f5c3")
            case "13":
                # Addon Hotrod/Xcs 8gb  
                get_packages_by_family("74eb925a-4a05-4ede-b04b-edd90786419b")
            case "14":
                # Xcs Flex Ori  
                get_packages_by_family("4a1acab0-da54-462c-84b1-25fd0efa9318")
            case "15":
                # EduCoference Ori  
                get_packages_by_family("5d63dddd-4f90-4f4c-8438-2f005c20151f")
            case "19":
                # Mastif Bundling Setahun  
                get_packages_by_family("6bcc96f4-f196-4e8f-969f-e45a121d21bd")
            case "17":
                # Paket XL Point  
                get_packages_by_family("784be350-9364-4f03-8efa-e7cf31e8baa2")
            case "18":
                # Paket Bonus MyRewards   
                get_packages_by_family("07461ed8-8a81-4d89-a8f2-4dd0271efdde")
            case "19":
                # Addon XCP 2GB   
                get_packages_by_family("580c1f94-7dc4-416e-96f6-8faf26567516")
            case "20":
                # Addon XCP 15GB  
                get_packages_by_family("45c3a622-8c06-4bb1-8e56-bba1f3434600")
            case "21":
                # Bebas Puas  
                get_packages_by_family("d0a349a7-0b3a-4552-bc1d-3fd9ac0a17ee")
            case "22":
                # XCP OLD 10GB  
                get_packages_by_family("364d5764-77d3-41b8-9c22-575b555bf9df")
            case "23":
                # XCP VIP  
                get_packages_by_family("23b71540-8785-4abe-816d-e9b4efa48f95")
            case "24":
                # Akrab 2Kb New  
                get_packages_by_family("4889cc43-55c9-47dd-8f7e-d3ac9fae6022")
            case "25":
                # XCP GIFT  
                get_packages_by_family("0895946e-d277-4218-914c-b663c09debf7")
            case "26":
                # Addon XCP 1GB  
                get_packages_by_family("8080ddcf-18c5-4d6d-86a4-89eb8ca5f2d1")
            case "27":
                # Pilkada Damai Kuota  
                get_packages_by_family("e3b2c02e-0e2f-4275-a6de-84fb9efab992")
            case "28":
                # Bonus Akrab Rp 0  
                get_packages_by_family("a677d649-3c5a-46c2-a043-cb69ac841208")
            case "29":
                # XC FLEX LENGKAP  
                get_packages_by_family("3a6a256f-1524-4dc3-a989-35584f31c265")
            case "30":
                # Unli Turbo Xcs/Hotrod  
                get_packages_by_family("08a3b1e6-8e78-4e45-a540-b40f06871cfe")
            case "31":
                # Addon XCP 6GB  
                get_packages_by_family("5412b964-474e-42d3-9c86-f5692da627db")
            case "32":
                # Family Hide Addon Prepaid  
                get_packages_by_family("31c9605f-1a3a-4410-ae45-362650bb507d")
            case "33":
                # Add Slot Akrab  
                get_packages_by_family("86d86765-65a6-4ece-8056-ab2b220429e4")
            case "34":
                # Akrab Full Versi  
                get_packages_by_family("f4fd69c7-12a4-4047-a1f2-f4072a7c543e")
            case "35":
                # Akrab Big  
                get_packages_by_family("6e469cb2-443d-402f-ba77-681b032ead6a")
            case "36":
                # Booster Akrab  
                get_packages_by_family("5452eed8-91f3-4e9c-b7bb-0985759d5440")
            case "37":
                # Addon Akrab  
                get_packages_by_family("c5dbcb2d-31cc-462c-afe8-b3a767c6d404")
            case "38":
                # XCS 8GB & 14GB  
                get_packages_by_family("3e6d45f1-f314-4acd-a75b-be40c0726198")
            case "39":
                # New Comer XCS 2GB & 4GB  
                get_packages_by_family("6bc5a34d-7901-4bf9-8629-5bd7de28c89f")
            case "40":
                # XC FLEX LENGKAP V2  
                get_packages_by_family("3c71892a-852c-4a0f-8cb5-9cf731e26508")
            case "41":
                # Paket Harian Rp 0  
                get_packages_by_family("96d99f87-8963-40e4-a522-8bea86504fee")
            case "42":
                # Paket Youtube Bonus  
                get_packages_by_family("1fe292a5-5fef-430e-917b-e0eaeeb89f93")
            case "43":
                # Xtra Combo Mini  
                get_packages_by_family("ad176860-49d4-4bdd-9161-ab38dc6a631b")
            case "44":
                # xcp 15gp  
                get_packages_by_family("864d43cb-7f32-46ad-aed5-6e199fad851f")
            
            case "45":
                show_bundle_menu()

            case "46":
                clear_sc()
                console.print(Panel(
                    Align.center("🛒 Beli Semua Paket Yang ada dalam Family Code", vertical="middle"),
                    border_style=theme["border_info"],
                    padding=(1, 2),
                    expand=True
                ))

                family_code = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
                if not family_code or family_code == "99":
                    print_panel("Info", "Pembelian dibatalkan.")
                    pause()
                    continue

                use_decoy = console.input(f"[{theme['text_sub']}]Gunakan paket decoy? (y/n):[/{theme['text_sub']}] ").strip().lower() == "y"
                pause_on_success = console.input(f"[{theme['text_sub']}]Pause setiap pembelian sukses? (y/n):[/{theme['text_sub']}] ").strip().lower() == "y"

                confirm_text = Text.from_markup(
                    f"Family Code: [bold]{family_code}[/]\n"
                    f"Gunakan Decoy: {'Ya' if use_decoy else 'Tidak'}\n"
                    f"Pause per pembelian: {'Ya' if pause_on_success else 'Tidak'}\n\n"
                    f"[{theme['text_sub']}]Lanjutkan pembelian semua paket dalam family code ini?[/{theme['text_sub']}]"
                )
                console.print(Panel(confirm_text, title="📦 Konfirmasi", border_style=theme["border_warning"], padding=(1, 2), expand=True))
                if console.input(f"[{theme['text_sub']}]Lanjutkan? (y/n):[/{theme['text_sub']}] ").strip().lower() != "y":
                    print_panel("Info", "Pembelian dibatalkan.")
                    pause()
                    continue

                purchase_by_family(family_code, use_decoy, pause_on_success)

            case "47":
                clear_sc()
                console.print(Panel(
                    Align.center("🔁 Loop Pembelian Paket", vertical="middle"),
                    border_style=theme["border_info"],
                    padding=(1, 2),
                    expand=True
                ))
            
                family_code = console.input(f"[{theme['text_sub']}]Masukkan Family Code:[/{theme['text_sub']}] ").strip()
                if not family_code or family_code == "99":
                    print_panel("Info", "Pembelian dibatalkan.")
                    pause()
                    continue
            
                use_decoy = console.input(f"[{theme['text_sub']}]Gunakan paket decoy? (y/n):[/{theme['text_sub']}] ").strip().lower() == "y"
            
                try:
                    order = int(console.input(f"[{theme['text_sub']}]Urutan dari list Family Code:[/{theme['text_sub']}] ").strip())
                    delay = int(console.input(f"[{theme['text_sub']}]Delay antar pembelian (detik):[/{theme['text_sub']}] ").strip() or "0")
                    how_many = int(console.input(f"[{theme['text_sub']}]Berapa kali ulang pembelian:[/{theme['text_sub']}] ").strip())
            
                    confirm_text = Text.from_markup(
                        f"Family Code: [bold]{family_code}[/]\n"
                        f"Urutan: [bold]{order}[/]\n"
                        f"Jumlah Ulang: [bold]{how_many}[/]\n"
                        f"Delay: [bold]{delay} detik[/]\n"
                        f"Gunakan Decoy: {'Ya' if use_decoy else 'Tidak'}"
                    )
                    console.print(Panel(confirm_text, title="📦 Konfirmasi", border_style=theme["border_warning"], padding=(1, 2), expand=True))
                    if console.input(f"[{theme['text_sub']}]Lanjutkan pembelian berulang? (y/n):[/{theme['text_sub']}] ").strip().lower() != "y":
                        print_panel("Info", "Pembelian dibatalkan.")
                        pause()
                        continue
            
                    for i in range(how_many):
                        console.print(Panel(
                            f"[bold]{i+1}/{how_many}[/] - [cyan]Eksekusi pembelian...[/]",
                            title="🔁 Loop",
                            border_style=theme["border_info"],
                            padding=(0, 1),
                            expand=True
                        ))
                        result = purchase_loop(
                            family_code=family_code,
                            order=order,
                            use_decoy=use_decoy,
                            delay=delay,
                            pause_on_success=True
                        )
                        if result is False:
                            print_panel("⛔ Dihentikan", "Loop pembelian dihentikan oleh pengguna.")
                            break
            
                except ValueError:
                    print_panel("⚠️ Error", "Input angka tidak valid.")
                    pause()

            case "48":
                show_family_info(user_context["api_key"], user_context["tokens"])

            case "00":
                show_bookmark_menu()

            case "77":
                show_donate_menu()

            case "88":
                show_theme_menu()

            case "99":
                print_panel("👋 Sampai Jumpa", "Aplikasi ditutup")
                sys.exit(0)

            case "s":
                special_packages = user_context.get("segments", {}).get("special_packages", [])
                if special_packages:
                    result = show_special_for_you_menu(user_context["tokens"], special_packages)
                    if result in ("MAIN", "BACK"):
                        continue
                else:
                    print_panel("Info", "Tidak ada paket Special For You yang tersedia saat ini.")
                    pause()

            case _:
                print_panel("⚠️ Error", "Pilihan tidak valid.")
                pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_panel("👋 Keluar", "Aplikasi dihentikan oleh pengguna.")
        sys.exit(0)
