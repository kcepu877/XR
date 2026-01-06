import io
import qrcode

from app2.config.imports import *
from app2.menus.util import clear_screen, pause, live_loading, simple_number

console = Console()


def generate_qr_ascii(data: str) -> str:
    """Generate ASCII representation of a QR code."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()


def show_info_menu():
    """Display donation and support information with QRIS code."""
    clear_screen()
    ensure_git()
    theme = get_theme()
    qris_url = (
        "00020101021126610014COM.GO-JEK.WWW01189360091436578035570210G6578035570303UMI"
        "51440014ID.CO.QRIS.WWW0215ID10243445558740303UMI5204549953033605802ID5922WARUNG DIGITAL, BNGKLN6009BANGKALAN"
        "61056911262070703A016304DEE7"
    )

    with live_loading("Menyiapkan QRIS...", theme):
        qr_code_ascii = generate_qr_ascii(qris_url)

    console.print(Panel(
        Align.center("Dukung Pengembangan myXL CLI", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
     ))
    simple_number()

    donate_info = Text()
    donate_info.append(
        "Butuh kode unlock untuk menambah akun lebih banyak? Hubungi Telegram (@seaker877).\n\n",
        style=theme["text_body"]
    )
    donate_info.append(
        "Untuk mendukung pengembangan tool ini, Anda dapat memberikan donasi melalui metode berikut:\n\n",
        style=theme["text_body"]
    )
    donate_info.append("- Dana: 0878-6116-7414\n", style=theme["text_body"])
    donate_info.append("  A/N Saiful\n", style=theme["text_body"])
    donate_info.append("- QRIS tersedia di bawah.\n\n", style=theme["text_body"])
    donate_info.append("Terima kasih atas dukungan Anda.", style=theme["text_sub"])

    console.print(Panel(
        Align.left(donate_info),
        title=f"[{theme['text_title']}]Informasi Donasi[/]",
        border_style=theme["border_primary"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    console.print(Panel(
        Align.center(qr_code_ascii),
        title=f"[{theme['text_title']}]Scan QRIS[/]",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    pause()
