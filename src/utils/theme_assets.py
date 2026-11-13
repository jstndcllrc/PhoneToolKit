"""Theme assets - checkmark artwork for styled checkboxes.

Qt's stylesheet engine does not support ``data:`` URIs for the ``image``
property, so a base64 SVG checkmark in QSS silently renders as an empty
coloured square. Instead we paint the checkmark once with QPainter, write it
to the writable data directory and reference it by absolute path, which works
in both development and frozen (PyInstaller) builds.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen

from utils.resources import get_data_path

# Logical size of the glyph; exported at 4x for crisp high-DPI rendering.
_WIDTH = 14
_HEIGHT = 10
_SCALE = 4

# Weight of the check stroke, in logical pixels (matches the old SVG artwork).
_STROKE = 2.5

_cache: Dict[str, str] = {}


def _render_png(color: str) -> bytes:
    """Render a rounded checkmark in ``color`` on a transparent canvas."""
    image = QImage(_WIDTH * _SCALE, _HEIGHT * _SCALE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    pen = QPen(QColor(color))
    pen.setWidthF(_STROKE * _SCALE)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(pen)
    painter.drawPolyline(
        [
            QPointF(1.0 * _SCALE, 5.6 * _SCALE),
            QPointF(4.8 * _SCALE, 9.0 * _SCALE),
            QPointF(12.6 * _SCALE, 1.4 * _SCALE),
        ]
    )
    painter.end()

    array = QByteArray()
    buffer = QBuffer(array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(array.data())


def _write_asset(target: Path, color: str) -> Path:
    """Create the asset, falling back to a home-directory copy if needed."""
    payload = _render_png(color)
    candidates = (target.parent, Path.home() / ".phonetoolkit" / "theme")
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / target.name
            destination.write_bytes(payload)
            return destination
        except OSError:
            continue
    raise OSError("No writable directory available for theme assets")


def _as_url(path: Path) -> str:
    """Build a QSS-safe ``url(...)`` for ``path``.

    Qt's stylesheet image loader only understands plain filesystem paths -
    ``file:///`` URLs (and ``data:`` URIs) silently load nothing, which is why
    the checkmark used to vanish. Double quotes keep spaces in Windows paths
    intact.
    """
    return f'url("{path.resolve().as_posix()}")'


def checkmark_url(color: str) -> str:
    """Absolute QSS ``url(...)`` for a checkmark in ``color``.

    The PNG is generated on first use and cached both in memory and on disk so
    repeated theme switches cost nothing.
    """
    key = color.lower().lstrip("#")
    if key in _cache:
        return _cache[key]

    target = get_data_path("theme") / f"checkmark_{key}.png"
    if not target.exists() or target.stat().st_size == 0:
        target = _write_asset(target, color)

    url = _as_url(target)
    _cache[key] = url
    return url
