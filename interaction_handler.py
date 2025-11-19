# interaction_handler.py

from PySide6.QtWidgets import QWidget, QMenu
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

class InteractionHandler(QWidget):
    """마우스 입력을 받아 뷰포트를 제어하는 투명한 창"""
    def __init__(self, blur_window):
        super().__init__()
        self.blur_window = blur_window

        # --- 창 설정: 보이지 않지만 마우스 이벤트를 받을 수 있도록 ---
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        
        # [수정] WA_TranslucentBackground는 마우스 입력을 통과시키므로 절대 사용하면 안 됨
        # self.setAttribute(Qt.WA_TranslucentBackground)

        # [대안] 창 전체 투명도를 조절하여 눈에 보이지 않게 만듦
        # 0.0은 OS가 창을 무시할 수 있으므로 0에 가까운 값을 사용
        self.setWindowOpacity(0.01)

    # --- 이벤트 핸들러 ---
    def contextMenuEvent(self, event):
        """우클릭 시 컨텍스트 메뉴를 표시합니다."""
        context_menu = QMenu(self)

        always_on_top_action = QAction("항상 위에 표시", self, checkable=True)
        always_on_top_action.setChecked(self.blur_window.is_always_on_top)

        lock_position_action = QAction("위치 잠금", self, checkable=True)
        lock_position_action.setChecked(self.blur_window.is_position_locked)

        lock_size_action = QAction("크기 잠금", self, checkable=True)
        lock_size_action.setChecked(self.blur_window.is_size_locked)

        always_on_top_action.triggered.connect(self.blur_window.set_always_on_top)
        lock_position_action.triggered.connect(self.blur_window.set_position_lock)
        lock_size_action.triggered.connect(self.blur_window.set_size_lock)

        close_action = QAction("뷰포트 닫기", self)
        close_action.triggered.connect(self.blur_window.close)

        context_menu.addAction(always_on_top_action)
        context_menu.addAction(lock_position_action)
        context_menu.addAction(lock_size_action)
        context_menu.addSeparator()
        context_menu.addAction(close_action)

        context_menu.exec(event.globalPos())
        
    def mousePressEvent(self, event):
        """마우스 드래그 시작 위치를 기록합니다."""
        if self.blur_window.is_position_locked or event.button() != Qt.LeftButton:
            return
        self._drag_start_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """자신과 블러 창을 함께 움직입니다."""
        if self.blur_window.is_position_locked or not hasattr(self, '_drag_start_position'):
            return
        
        delta = event.globalPosition().toPoint() - self._drag_start_position
        
        self.move(self.pos() + delta)
        self.blur_window.move(self.blur_window.pos() + delta)
        
        self._drag_start_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        """드래그 상태를 초기화합니다."""
        if hasattr(self, '_drag_start_position'):
            del self._drag_start_position