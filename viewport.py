# viewport.py

import sys
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent

from utils import apply_blur

class Viewport(QWidget):
    """화면의 특정 영역을 흐리게 표시하는 가리개 위젯"""

    # 시그널 정의: 가리개가 닫히기 직전에 발생
    closing = Signal()

    def __init__(self):
        """생성자: 가리개 창의 시각적 속성만 설정합니다."""
        super().__init__()

        # --- 상태 변수 초기화 ---
        self.is_locked = False  # 위치/크기 잠금 통합
        self._blur_applied = False  # 블러 효과 적용 여부

        # --- 창 기본 속성 설정 ---
        # 항상 위에 표시는 필수 기능이므로 항상 활성화
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 이 창은 항상 마우스 이벤트를 통과시킴
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setGeometry(200, 200, 500, 400)

    # --- 외부에서 호출될 슬롯(Setter) 메서드들 ---
    def set_lock(self, checked):
        """'고정' 상태를 설정합니다 (위치와 크기 모두 고정)."""
        self.is_locked = checked

    def showEvent(self, event):
        """가리개가 표시될 때 블러 효과를 적용합니다."""
        super().showEvent(event)
        if not self._blur_applied:
            # 윈도우가 완전히 생성된 후 블러 효과 적용
            apply_blur(self.winId())
            self._blur_applied = True

    def closeEvent(self, event: QCloseEvent):
        """가리개가 닫히기 전에 closing 시그널을 발생시킵니다."""
        self.closing.emit()
        event.accept()

    # 모든 마우스/네이티브 이벤트 핸들러는 제거됨
    # 이 위젯은 더 이상 직접적인 마우스 상호작용을 처리하지 않음
