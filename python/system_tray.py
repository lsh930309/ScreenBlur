# system_tray.py

import sys
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal

class SystemTrayIcon(QSystemTrayIcon):
    """시스템 트레이 아이콘 및 컨텍스트 메뉴를 관리하는 클래스"""
    
    show_window_requested = Signal()

    def __init__(self, icon: QIcon, parent=None):
        """생성자: 트레이 아이콘과 메뉴를 초기화합니다."""
        super().__init__(parent)
        
        # --- 아이콘 설정 ---
        # main_window에서 생성된 아이콘을 전달받아 설정
        self.setIcon(icon)
        
        # 마우스를 아이콘 위에 올렸을 때 표시될 툴팁 설정
        self.setToolTip("블러 뷰포트 컨트롤러")
        
        # --- 컨텍스트 메뉴 (마우스 오른쪽 버튼 클릭 시) --- 
        menu = QMenu()
        
        show_action = QAction("컨트롤러 표시", self)
        show_action.triggered.connect(self.show_window_requested.emit)
        
        quit_action = QAction("종료", self)
        # 앱의 quit_application 슬롯에 연결하여 정상 종료되도록 함
        if parent and hasattr(parent, 'quit_application'):
            quit_action.triggered.connect(parent.quit_application)
        else:
            quit_action.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(show_action)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        self.activated.connect(self.on_activated)

    def on_activated(self, reason):
        """트레이 아이콘 활성화(클릭 등) 시 호출되는 메서드"""
        if reason == self.ActivationReason.Trigger:
            self.show_window_requested.emit()