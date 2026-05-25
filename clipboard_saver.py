"""
Clipboard Saver v8 - PyQt6
- 커스텀 타이틀바 (최소화/최대화/종료)
- 회색 톤 색상
- 심플 아이콘
- 이미지 경로 복사
요구사항: pip install PyQt6
"""

import sys, os, datetime, ctypes

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy, QLineEdit
)
from PyQt6.QtCore  import Qt, QTimer, QMimeData, QUrl, QPoint, QSize, pyqtSignal
from PyQt6.QtGui   import (
    QPixmap, QImage, QColor, QDrag, QIcon, QPalette, QCursor,
    QPainter, QBrush, QPen, QFont
)

# ── 색상 (회색 톤) ─────────────────────────────────────────────────────────────
BG     = "#2b2b2b"   # 메인 배경
BG2    = "#333333"   # 미리보기 배경
BG3    = "#3d3d3d"   # 버튼/입력 배경
ACCENT = "#c8c8c8"   # 강조 (밝은 회색)
GRAY   = "#888888"   # 보조 텍스트
LINE   = "#444444"   # 구분선
TITLE  = "#1e1e1e"   # 타이틀바

SAVE_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "ClipboardSaver")
os.makedirs(SAVE_DIR, exist_ok=True)


# ── 타이틀바 색상 ─────────────────────────────────────────────────────────────
def set_titlebar_color(hwnd, hex_color):
    try:
        r,g,b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
        c = r | (g<<8) | (b<<16)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(ctypes.c_int(c)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass


# ── 앱 아이콘 (심플 돋보기/클립 스타일) ──────────────────────────────────────
def make_icon() -> QIcon:
    size = 64
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    # 원형 배경
    p.setBrush(QBrush(QColor(BG3)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, 56, 56)
    # 클립보드 심플 아이콘
    p.setPen(QPen(QColor(ACCENT), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # 몸통
    p.drawRoundedRect(16, 20, 32, 36, 3, 3)
    # 상단 클립
    p.drawRoundedRect(24, 12, 16, 12, 2, 2)
    # 라인 2개
    p.drawLine(22, 32, 42, 32)
    p.drawLine(22, 40, 42, 40)
    p.end()
    return QIcon(px)


# ── 드래그 가능한 미리보기 ────────────────────────────────────────────────────
class DraggablePreview(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filepath = None
        self._drag_start = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.filepath and os.path.exists(self.filepath):
            px = QPixmap(self.filepath)
            self.setPixmap(px.scaled(self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if self._drag_start is None or self.filepath is None: return
        if (event.pos()-self._drag_start).manhattanLength() < QApplication.startDragDistance(): return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(self.filepath)])
        drag.setMimeData(mime)
        px = QPixmap(self.filepath)
        thumb = px.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
        drag.setPixmap(thumb)
        drag.setHotSpot(QPoint(thumb.width()//2, thumb.height()//2))
        drag.exec(Qt.DropAction.CopyAction)
        self._drag_start = None


# ── 히스토리 아이템 ───────────────────────────────────────────────────────────
class HistoryItem(QWidget):
    clicked = pyqtSignal(str, str)
    deleted = pyqtSignal(object)

    def __init__(self, pixmap: QPixmap, filepath: str, filename: str, time_str: str):
        super().__init__()
        self.filepath = filepath
        self.filename = filename
        self.setFixedWidth(148)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"background:{BG3}; border-radius:4px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2,2,2,2)
        layout.setSpacing(2)

        thumb_wrap = QWidget()
        thumb_wrap.setStyleSheet(f"background:{BG3};")
        tw_l = QHBoxLayout(thumb_wrap)
        tw_l.setContentsMargins(0,0,0,0); tw_l.setSpacing(2)

        thumb_label = QLabel()
        thumb = pixmap.scaled(132, 88, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        thumb_label.setPixmap(thumb)
        thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_label.setStyleSheet(f"background:{BG3};")
        thumb_label.mousePressEvent = lambda e: self.clicked.emit(self.filepath, self.filename)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(16,16)
        del_btn.setStyleSheet(f"""
            QPushButton {{ background:{LINE}; color:{GRAY}; border:none;
                           font-size:8px; border-radius:8px; }}
            QPushButton:hover {{ background:#cc4444; color:white; }}
        """)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(lambda: self.deleted.emit(self))

        tw_l.addWidget(thumb_label)
        tw_l.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignTop)

        time_label = QLabel(time_str)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet(f"color:{GRAY}; font-size:9px; background:{BG3};")
        time_label.mousePressEvent = lambda e: self.clicked.emit(self.filepath, self.filename)

        layout.addWidget(thumb_wrap)
        layout.addWidget(time_label)
        self.adjustSize()


# ── 커스텀 타이틀바 ───────────────────────────────────────────────────────────
class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(36)
        self.setStyleSheet(f"background:{TITLE};")
        self._drag_pos = None

        l = QHBoxLayout(self)
        l.setContentsMargins(12, 0, 8, 0)
        l.setSpacing(6)

        # 아이콘 + 타이틀 없음 (헤더에 있으므로)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon().pixmap(18, 18))
        l.addWidget(icon_lbl)
        l.addStretch()

        # 항상 위 버튼 (커스텀 핀 아이콘)
        self.top_btn = QPushButton()
        self.top_btn.setCheckable(True)
        self.top_btn.setFixedSize(28, 24)
        self.top_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; border:none; border-radius:3px; }}
            QPushButton:checked {{ background:{BG3}; }}
            QPushButton:hover {{ background:{LINE}; }}
        """)
        self.top_btn.setToolTip("항상 위")
        self.top_btn.setIcon(self._make_pin_icon(False))
        self.top_btn.setIconSize(QSize(14, 14))
        self.top_btn.clicked.connect(self._toggle_top)
        l.addWidget(self.top_btn)

        # 최소화
        min_btn = QPushButton("─")
        min_btn.setFixedSize(36, 24)
        min_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{GRAY}; border:none; font-size:14px; }}
            QPushButton:hover {{ background:{BG3}; color:white; }}
        """)
        min_btn.clicked.connect(parent.showMinimized)
        l.addWidget(min_btn)

        # 최대화
        self.max_btn = QPushButton("□")
        self.max_btn.setFixedSize(36, 24)
        self.max_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{GRAY}; border:none; font-size:13px; }}
            QPushButton:hover {{ background:{BG3}; color:white; }}
        """)
        self.max_btn.clicked.connect(self._toggle_max)
        l.addWidget(self.max_btn)

        # 종료
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background:transparent; color:{GRAY}; border:none; font-size:13px; }}
            QPushButton:hover {{ background:#cc4444; color:white; }}
        """)
        close_btn.clicked.connect(parent.close)
        l.addWidget(close_btn)

    def _make_pin_icon(self, active: bool) -> QIcon:
        px = QPixmap(14, 14)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(ACCENT) if active else QColor(GRAY)
        p.setPen(QPen(color, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(QBrush(color) if active else Qt.BrushStyle.NoBrush)
        # 핀 머리 (원)
        p.drawEllipse(3, 1, 8, 7)
        # 핀 몸통
        p.drawLine(7, 8, 7, 13)
        p.end()
        return QIcon(px)

    def _toggle_top(self, checked):
        self.top_btn.setIcon(self._make_pin_icon(checked))
        self.parent.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)
        self.parent.show()

    def _toggle_max(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.max_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.max_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.parent.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self._toggle_max()


# ── 메인 윈도우 ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 기본 타이틀바 제거
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowTitle("Clipboard Saver")
        self.setWindowIcon(make_icon())
        self.resize(500, 400)
        self.setMinimumSize(400, 300)
        self.setStyleSheet(f"QMainWindow {{ background:{BG}; }}")

        self.last_image_hash = None
        self.current_filepath = None
        self.saved_count = 0
        self.fade_step = 0
        self.fade_dir  = 1
        self.dot_visible = True
        self.save_dir = SAVE_DIR

        self._build_ui()
        self._setup_timers()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background:{BG};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        # 커스텀 타이틀바
        self.title_bar = TitleBar(self)
        root.addWidget(self.title_bar)

        # 헤더
        root.addWidget(self._make_header())
        root.addWidget(self._hline())

        # 메인 영역
        main_w = QWidget(); main_w.setStyleSheet(f"background:{BG};")
        main_l = QHBoxLayout(main_w)
        main_l.setContentsMargins(16,8,16,8)
        main_l.setSpacing(12)

        # 미리보기
        self.preview_container = QWidget()
        self.preview_container.setStyleSheet(f"background:{BG2}; border-radius:4px;")
        pc_l = QVBoxLayout(self.preview_container)
        pc_l.setContentsMargins(0,0,0,0); pc_l.setSpacing(0)

        self.preview = DraggablePreview()
        self.preview.setStyleSheet(f"background:{BG2}; color:{GRAY};")
        self.preview.setText("스크린샷을 찍거나\nCtrl+C 로 이미지를 복사하세요")
        self.preview.setFont(QFont("Courier New", 11))

        self.drag_hint = QLabel("드래그해서 탐색기로 파일 저장")
        self.drag_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_hint.setStyleSheet(f"color:{ACCENT}; background:{BG2}; font-size:9px; padding:4px;")
        self.drag_hint.hide()

        pc_l.addWidget(self.preview)
        pc_l.addWidget(self.drag_hint)

        # 히스토리
        hist_w = QWidget(); hist_w.setFixedWidth(160)
        hist_w.setStyleSheet(f"background:{BG};")
        hist_l = QVBoxLayout(hist_w)
        hist_l.setContentsMargins(0,0,0,0); hist_l.setSpacing(6)

        hist_title = QLabel("HISTORY")
        hist_title.setStyleSheet(f"color:{GRAY}; font-weight:bold; font-size:9px;")
        hist_l.addWidget(hist_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{BG}; }}
            QScrollBar:vertical {{ background:{BG3}; width:5px; border-radius:2px; }}
            QScrollBar::handle:vertical {{ background:{GRAY}; border-radius:2px; min-height:20px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        """)
        self.hist_inner = QWidget(); self.hist_inner.setStyleSheet(f"background:{BG};")
        self.hist_layout = QVBoxLayout(self.hist_inner)
        self.hist_layout.setContentsMargins(0,0,0,0); self.hist_layout.setSpacing(6)
        self.hist_layout.addStretch()
        scroll.setWidget(self.hist_inner)
        hist_l.addWidget(scroll)

        main_l.addWidget(self.preview_container, stretch=1)
        main_l.addWidget(hist_w)
        root.addWidget(main_w, stretch=1)

        root.addWidget(self._hline())
        root.addWidget(self._make_infobar())
        root.addWidget(self._hline())
        root.addWidget(self._make_pathbar())

    def _make_header(self):
        w = QWidget(); w.setFixedHeight(36); w.setStyleSheet(f"background:{BG};")
        l = QHBoxLayout(w); l.setContentsMargins(16,0,16,0)
        lbl1 = QLabel("CLIPBOARD")
        lbl1.setStyleSheet(f"color:{ACCENT}; font-weight:bold; font-size:11px;")
        lbl2 = QLabel(" SAVER")
        lbl2.setStyleSheet(f"color:{ACCENT}; font-size:11px;")
        l.addWidget(lbl1); l.addWidget(lbl2); l.addStretch()
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color:{ACCENT}; font-size:12px;")
        monitor = QLabel("monitoring")
        monitor.setStyleSheet(f"color:{GRAY}; font-size:8px;")
        l.addWidget(monitor); l.addWidget(self.status_dot)
        return w

    def _make_infobar(self):
        w = QWidget(); w.setFixedHeight(26); w.setStyleSheet(f"background:{BG};")
        l = QHBoxLayout(w); l.setContentsMargins(16,0,16,0)
        self.info_label = QLabel("waiting...")
        self.info_label.setStyleSheet(f"color:{GRAY}; font-size:9px;")
        l.addWidget(self.info_label); l.addStretch()
        return w

    def _make_folder_icon(self) -> QIcon:
        px = QPixmap(14, 14)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(GRAY), 1.5, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        # 폴더 몸통
        p.drawRoundedRect(1, 5, 12, 8, 1, 1)
        # 폴더 탭 (상단 왼쪽 작은 사각형)
        p.drawLine(1, 5, 1, 3)
        p.drawLine(1, 3, 5, 3)
        p.drawLine(5, 3, 6, 5)
        p.end()
        return QIcon(px)

    def _make_pathbar(self):
        w = QWidget(); w.setFixedHeight(34); w.setStyleSheet(f"background:{BG};")
        l = QHBoxLayout(w); l.setContentsMargins(16,6,16,6); l.setSpacing(4)

        lbl = QLabel("PATH")
        lbl.setStyleSheet(f"color:{GRAY}; font-size:8px;")
        lbl.setFixedWidth(36)

        self.path_edit = QLineEdit(self.save_dir)
        self.path_edit.setFixedHeight(22)
        self.path_edit.setStyleSheet(f"""
            QLineEdit {{ background:{BG3}; color:{GRAY}; border:1px solid {LINE};
                         border-radius:3px; padding:2px 6px; font-size:9px; }}
            QLineEdit:focus {{ border:1px solid {ACCENT}; color:{ACCENT}; }}
        """)
        self.path_edit.editingFinished.connect(self._on_path_changed)

        # 폴더 열기 (커스텀 아이콘)
        folder_btn = QPushButton()
        folder_btn.setFixedSize(22,22)
        folder_btn.setToolTip("저장 폴더 열기")
        folder_btn.setIcon(self._make_folder_icon())
        folder_btn.setIconSize(QSize(14, 14))
        folder_btn.setStyleSheet(f"""
            QPushButton {{ background:{BG3}; border:none; border-radius:3px; }}
            QPushButton:hover {{ background:{LINE}; }}
        """)
        folder_btn.clicked.connect(lambda: os.startfile(self.save_dir))

        # 경로 복사
        copy_btn = QPushButton("⧉")
        copy_btn.setFixedSize(22,22)
        copy_btn.setToolTip("이미지 경로 복사")
        copy_btn.setStyleSheet(f"""
            QPushButton {{ background:{BG3}; color:{GRAY}; border:none;
                           font-size:13px; border-radius:3px; }}
            QPushButton:hover {{ background:{LINE}; color:{ACCENT}; }}
        """)
        copy_btn.clicked.connect(self._copy_image_path)

        l.addWidget(lbl); l.addWidget(self.path_edit)
        l.addWidget(folder_btn); l.addWidget(copy_btn)
        return w

    def _hline(self):
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{LINE}; background:{LINE};")
        line.setFixedHeight(1); return line

    # ── 경로 복사 ─────────────────────────────────────────────────────────────
    def _copy_image_path(self):
        if self.current_filepath:
            QApplication.clipboard().setText(self.current_filepath)
            self.info_label.setText("✓ 경로 복사됨")
            self.info_label.setStyleSheet(f"color:{ACCENT}; font-size:9px;")
            QTimer.singleShot(2000, lambda: self.info_label.setStyleSheet(
                f"color:{GRAY}; font-size:9px;"))

    # ── 저장 경로 변경 ────────────────────────────────────────────────────────
    def _on_path_changed(self):
        new_dir = self.path_edit.text().strip()
        try:
            os.makedirs(new_dir, exist_ok=True)
            self.save_dir = new_dir
            self.path_edit.setStyleSheet(f"""
                QLineEdit {{ background:{BG3}; color:{ACCENT}; border:1px solid {ACCENT};
                             border-radius:3px; padding:2px 6px; font-size:9px; }}
            """)
            QTimer.singleShot(1500, lambda: self.path_edit.setStyleSheet(f"""
                QLineEdit {{ background:{BG3}; color:{GRAY}; border:1px solid {LINE};
                             border-radius:3px; padding:2px 6px; font-size:9px; }}
                QLineEdit:focus {{ border:1px solid {ACCENT}; color:{ACCENT}; }}
            """))
        except Exception:
            self.path_edit.setText(self.save_dir)

    # ── 타이머 ────────────────────────────────────────────────────────────────
    def _setup_timers(self):
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self._check_clipboard)
        self.clip_timer = QTimer()
        self.clip_timer.timeout.connect(self._check_clipboard)
        self.clip_timer.start(800)
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink_dot)
        self.blink_timer.start(900)
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._fade_tick)

    # ── 클립보드 감지 ─────────────────────────────────────────────────────────
    def _check_clipboard(self):
        try:
            img = QApplication.clipboard().image()
            if img.isNull(): return
            w, h = img.width(), img.height()
            pixel = img.pixel(w//2, h//2) if w>0 and h>0 else 0
            image_hash = (w, h, pixel)
            if image_hash == self.last_image_hash: return
            self.last_image_hash = image_hash
            self._on_new_image(img)
        except Exception as e:
            print(f"클립보드 오류: {e}")

    def _on_new_image(self, qimg: QImage):
        pixmap = QPixmap.fromImage(qimg)
        fname  = datetime.datetime.now().strftime("clip_%Y%m%d_%H%M%S.png")
        fpath  = os.path.join(self.save_dir, fname)
        os.makedirs(self.save_dir, exist_ok=True)
        pixmap.save(fpath, "PNG")
        self.current_filepath = fpath
        self.saved_count += 1
        self._add_history(pixmap, fpath, fname)
        self._show_preview(pixmap, fpath)
        self.info_label.setText(f"{fname}  ·  {qimg.width()} × {qimg.height()}px")
        self.info_label.setStyleSheet(f"color:{ACCENT}; font-size:9px;")
        self._start_fade()

    # ── 미리보기 ──────────────────────────────────────────────────────────────
    def _show_preview(self, pixmap: QPixmap, filepath: str):
        self.preview.filepath = filepath
        self.preview.setPixmap(pixmap.scaled(
            self.preview.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.drag_hint.show()

    # ── 히스토리 ──────────────────────────────────────────────────────────────
    def _add_history(self, pixmap: QPixmap, fpath: str, fname: str):
        item = HistoryItem(pixmap, fpath, fname,
                           datetime.datetime.now().strftime("%H:%M:%S"))
        item.clicked.connect(self._on_history_click)
        item.deleted.connect(self._on_history_delete)
        self.hist_layout.insertWidget(0, item)

    def _on_history_click(self, filepath: str, filename: str):
        if not os.path.exists(filepath): return
        pixmap = QPixmap(filepath)
        self.current_filepath = filepath
        self._show_preview(pixmap, filepath)
        self.info_label.setText(f"{filename}  ·  {pixmap.width()} × {pixmap.height()}px")
        self.info_label.setStyleSheet(f"color:{ACCENT}; font-size:9px;")

    def _on_history_delete(self, item):
        item.setParent(None); item.deleteLater()

    # ── 페이드 ────────────────────────────────────────────────────────────────
    def _start_fade(self):
        self.fade_step=0; self.fade_dir=1; self.fade_timer.start(16)

    def _fade_tick(self):
        STEPS=12
        fac=(self.fade_step/STEPS) if self.fade_dir==1 else (1-self.fade_step/STEPS)
        bg2=QColor(BG2); acc=QColor(ACCENT)
        r=int(bg2.red()+(acc.red()-bg2.red())*fac)
        g=int(bg2.green()+(acc.green()-bg2.green())*fac)
        b=int(bg2.blue()+(acc.blue()-bg2.blue())*fac)
        self.preview_container.setStyleSheet(f"background:rgb({r},{g},{b}); border-radius:4px;")
        self.fade_step+=1
        if self.fade_dir==1 and self.fade_step>STEPS:
            self.fade_dir=-1; self.fade_step=0
        elif self.fade_dir==-1 and self.fade_step>STEPS:
            self.preview_container.setStyleSheet(f"background:{BG2}; border-radius:4px;")
            self.fade_timer.stop()

    def _blink_dot(self):
        self.dot_visible = not self.dot_visible
        self.status_dot.setStyleSheet(
            f"color:{ACCENT if self.dot_visible else BG}; font-size:12px;")

    # ── 창 크기 조절 (테두리 없을 때) ─────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, lambda: set_titlebar_color(int(self.winId()), TITLE))


# ── 엔트리포인트 ──────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.Base,          QColor(BG2))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG3))
    palette.setColor(QPalette.ColorRole.Text,          QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.Button,        QColor(BG3))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor(ACCENT))
    app.setPalette(palette)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
