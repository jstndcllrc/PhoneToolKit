"""App Icon Provider for PhoneToolKit
Generates and caches high-DPI icons for Android applications
"""
import logging
from typing import Dict, Optional
from pathlib import Path

from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont,
    QLinearGradient, QPainterPath
)
from PySide6.QtCore import Qt, QRectF

from utils.resources import get_resource_path

logger = logging.getLogger(__name__)

# Global memory cache for generated QIcons
_ICON_CACHE: Dict[str, QIcon] = {}

# Material design color palette for dynamic app squircle generation
PALETTE = [
    "#E91E63", "#9C27B0", "#673AB7", "#3F51B5", "#2196F3",
    "#03A9F4", "#00BCD4", "#009688", "#4CAF50", "#8BC34A",
    "#FF9800", "#FF5722", "#795548", "#607D8B", "#0056D2",
    "#00897B", "#3949AB", "#D81B60", "#8E24AA", "#1E88E5"
]


def _get_color_for_name(text: str) -> str:
    """Deterministic color selection based on package name hash"""
    val = sum(ord(c) * (i + 1) for i, c in enumerate(text))
    return PALETTE[val % len(PALETTE)]


def _create_base_pixmap(size: int = 48) -> tuple:
    """Helper to initialize an antialiased QPainter on a transparent QPixmap"""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    return pm, p


def _render_tile(p: QPainter, size: int, bg_color: str, secondary_color: Optional[str] = None, is_circle: bool = False):
    """Draw background rounded squircle or circle"""
    p.setPen(Qt.PenStyle.NoPen)
    if secondary_color:
        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0, QColor(bg_color))
        grad.setColorAt(1, QColor(secondary_color))
        p.setBrush(grad)
    else:
        p.setBrush(QColor(bg_color))

    if is_circle:
        p.drawEllipse(2, 2, size - 4, size - 4)
    else:
        radius = int(size * 0.25)
        p.drawRoundedRect(2, 2, size - 4, size - 4, radius, radius)


def _draw_symbol(p: QPainter, size: int, symbol: str, text_color: str = "#ffffff", font_size: int = 16):
    """Draw text glyph or emoji centered inside icon"""
    p.setPen(QColor(text_color))
    font = QFont("Segoe UI", font_size, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, symbol)


def _generate_specific_icon(package: str) -> Optional[QIcon]:
    """Generate specialized authentic vector icons for major apps"""
    size = 48
    pkg = package.lower()

    # YouTube
    if "youtube" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FF0000")
        # Draw white play triangle
        p.setBrush(QColor("#FFFFFF"))
        path = QPainterPath()
        path.moveTo(19, 15)
        path.lineTo(33, 24)
        path.lineTo(19, 33)
        path.closeSubpath()
        p.drawPath(path)
        p.end()
        return QIcon(pm)

    # Google Chrome
    if "chrome" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FFFFFF", is_circle=True)
        # Draw Chrome circular color segments
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#EA4335"))
        p.drawPie(3, 3, size - 6, size - 6, 90 * 16, 120 * 16)
        p.setBrush(QColor("#FBBC05"))
        p.drawPie(3, 3, size - 6, size - 6, 210 * 16, 120 * 16)
        p.setBrush(QColor("#34A853"))
        p.drawPie(3, 3, size - 6, size - 6, 330 * 16, 120 * 16)
        # Center blue circle with white ring
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(14, 14, 20, 20)
        p.setBrush(QColor("#4285F4"))
        p.drawEllipse(17, 17, 14, 14)
        p.end()
        return QIcon(pm)

    # Facebook
    if "com.facebook.katana" in pkg or "com.facebook.lite" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#1877F2")
        _draw_symbol(p, size, "f", font_size=24)
        p.end()
        return QIcon(pm)

    # Messenger
    if "com.facebook.orca" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#0084FF", secondary_color="#A033FF")
        _draw_symbol(p, size, "⚡", font_size=18)
        p.end()
        return QIcon(pm)

    # Instagram
    if "instagram" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#833AB4", secondary_color="#FD1D1D")
        _draw_symbol(p, size, "📷", font_size=18)
        p.end()
        return QIcon(pm)

    # WhatsApp
    if "whatsapp" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#25D366", is_circle=True)
        _draw_symbol(p, size, "📞", font_size=18)
        p.end()
        return QIcon(pm)

    # Telegram
    if "telegram" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#24A1DE", is_circle=True)
        _draw_symbol(p, size, "✈", font_size=18)
        p.end()
        return QIcon(pm)

    # TikTok
    if "tiktok" in pkg or "musically" in pkg or "trill" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#000000")
        _draw_symbol(p, size, "🎵", font_size=18)
        p.end()
        return QIcon(pm)

    # Spotify
    if "spotify" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#1ED760", is_circle=True)
        p.setPen(QColor("#000000"))
        f = QFont("Segoe UI", 16, QFont.Weight.Bold)
        p.setFont(f)
        p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "((•))")
        p.end()
        return QIcon(pm)

    # Netflix
    if "netflix" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#000000")
        _draw_symbol(p, size, "N", text_color="#E50914", font_size=22)
        p.end()
        return QIcon(pm)

    # X / Twitter
    if "twitter" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#000000")
        _draw_symbol(p, size, "𝕏", font_size=20)
        p.end()
        return QIcon(pm)

    # Discord
    if "discord" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#5865F2")
        _draw_symbol(p, size, "🎮", font_size=18)
        p.end()
        return QIcon(pm)

    # Gmail
    if "com.google.android.gm" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FFFFFF")
        _draw_symbol(p, size, "M", text_color="#EA4335", font_size=22)
        p.end()
        return QIcon(pm)

    # Google Maps
    if "com.google.android.apps.maps" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#34A853")
        _draw_symbol(p, size, "📍", font_size=20)
        p.end()
        return QIcon(pm)

    # Google Photos
    if "photos" in pkg and "google" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FFFFFF")
        _draw_symbol(p, size, "🌸", font_size=20)
        p.end()
        return QIcon(pm)

    # Google Search
    if "googlequicksearchbox" in pkg or "com.google.android.google" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FFFFFF")
        _draw_symbol(p, size, "G", text_color="#4285F4", font_size=22)
        p.end()
        return QIcon(pm)

    # GCash
    if "gcash" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#005CE6")
        _draw_symbol(p, size, "G", font_size=22)
        p.end()
        return QIcon(pm)

    # Maya
    if "paymaya" in pkg or "maya" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#00D084")
        _draw_symbol(p, size, "M", text_color="#000000", font_size=22)
        p.end()
        return QIcon(pm)

    # Shopee
    if "shopee" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#EE4D2D")
        _draw_symbol(p, size, "🛍", font_size=18)
        p.end()
        return QIcon(pm)

    # Lazada
    if "lazada" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#0F146D")
        _draw_symbol(p, size, "♥", text_color="#FF007A", font_size=20)
        p.end()
        return QIcon(pm)

    # Payjoy (Finance Lock)
    if "payjoy" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#C8102E")
        _draw_symbol(p, size, "🔒", font_size=18)
        p.end()
        return QIcon(pm)

    # Home Credit (Finance Lock)
    if "homecredit" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#EB0029")
        _draw_symbol(p, size, "HC", font_size=16)
        p.end()
        return QIcon(pm)

    # BillEase (Finance Lock)
    if "billease" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#0D47A1")
        _draw_symbol(p, size, "B", font_size=22)
        p.end()
        return QIcon(pm)

    # Salmon (Finance Lock)
    if "salmon" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#FF6F61")
        _draw_symbol(p, size, "🔒", font_size=18)
        p.end()
        return QIcon(pm)

    # Tala
    if "tala" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#009688")
        _draw_symbol(p, size, "T", font_size=22)
        p.end()
        return QIcon(pm)

    # Android Settings
    if "settings" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#37474F")
        _draw_symbol(p, size, "⚙", font_size=22)
        p.end()
        return QIcon(pm)

    # Camera
    if "camera" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#212121")
        _draw_symbol(p, size, "📷", font_size=18)
        p.end()
        return QIcon(pm)

    # Phone / Dialer
    if "dialer" in pkg or "phone" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#2E7D32")
        _draw_symbol(p, size, "📞", font_size=18)
        p.end()
        return QIcon(pm)

    # Messages / SMS
    if "mms" in pkg or "messaging" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#1976D2")
        _draw_symbol(p, size, "💬", font_size=18)
        p.end()
        return QIcon(pm)

    # Calculator
    if "calculator" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#EF6C00")
        _draw_symbol(p, size, "±", font_size=22)
        p.end()
        return QIcon(pm)

    # Clock
    if "deskclock" in pkg or "clock" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#3949AB", is_circle=True)
        _draw_symbol(p, size, "⏱", font_size=18)
        p.end()
        return QIcon(pm)

    # Contacts
    if "contacts" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#00897B")
        _draw_symbol(p, size, "👤", font_size=18)
        p.end()
        return QIcon(pm)

    # File Manager
    if "documentsui" in pkg or "filemanager" in pkg or "files" in pkg:
        pm, p = _create_base_pixmap(size)
        _render_tile(p, size, "#F57F17")
        _draw_symbol(p, size, "📁", font_size=18)
        p.end()
        return QIcon(pm)

    return None


def get_package_icon(package_name: str, label: str = "", is_system: bool = False) -> QIcon:
    """Get high-DPI icon for a given package name with fast caching"""
    if package_name in _ICON_CACHE:
        return _ICON_CACHE[package_name]

    try:
        # 1. Check if custom icon PNG exists in resources/icons/
        local_icon = get_resource_path(f"icons/{package_name}.png")
        if local_icon.exists():
            icon = QIcon(str(local_icon))
            _ICON_CACHE[package_name] = icon
            return icon

        # 2. Check for specialized app drawer
        icon = _generate_specific_icon(package_name)
        if icon:
            _ICON_CACHE[package_name] = icon
            return icon

        # 3. Categorical icon generation
        size = 48
        pm, p = _create_base_pixmap(size)
        pkg_lower = package_name.lower()

        # Check if Finance / Lock app
        if any(term in pkg_lower for term in ("payjoy", "salmon", "homecredit", "billease", "credit", "loan", "lock", "mdm", "knox")):
            _render_tile(p, size, "#D32F2F")
            _draw_symbol(p, size, "🔒", font_size=18)
        # Check if System app
        elif is_system or package_name.startswith("com.android."):
            _render_tile(p, size, "#455A64")
            _draw_symbol(p, size, "⚙", font_size=20)
        # Standard User app with initial letter badge
        else:
            bg_color = _get_color_for_name(package_name)
            _render_tile(p, size, bg_color)
            initial = (label or package_name.split(".")[-1]).strip()[:1].upper() or "A"
            _draw_symbol(p, size, initial, font_size=20)

        p.end()
        icon = QIcon(pm)
        _ICON_CACHE[package_name] = icon
        return icon

    except Exception as e:
        logger.error(f"Error creating icon for {package_name}: {e}")
        return QIcon()
