# main_window.py

import os
import sys
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QGroupBox,
                               QCheckBox, QFormLayout, QApplication, QHBoxLayout)
from PySide6.QtCore import QRect
from PySide6.QtGui import QCloseEvent, QIcon

from viewport import Viewport
from selection_overlay import SelectionOverlay
from system_tray import SystemTrayIcon
from interaction_handler import InteractionHandler

def resource_path(relative_path):
    """PyInstaller 환경에서 올바른 리소스 경로를 반환합니다.

    PyInstaller로 패키징된 경우 임시 폴더(_MEIPASS)에서 실행되므로
    리소스 파일 경로를 올바르게 찾기 위해 이 함수를 사용합니다.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 환경: 임시 디렉토리 사용
        return os.path.join(sys._MEIPASS, relative_path)
    # 개발 환경: 현재 디렉토리 사용
    return os.path.join(os.path.abspath("."), relative_path)

class MainWindow(QWidget):
    """메인 애플리케이션 창 클래스"""
    def __init__(self):
        """생성자: UI 초기화 및 시그널-슬롯 연결"""
        super().__init__()
        
        self._is_quitting = False

        # --- 아이콘 설정 ---
        # PyInstaller 환경 대응: 올바른 리소스 경로 사용
        app_icon = QIcon(resource_path("icon.ico"))
        self.setWindowIcon(app_icon)

        self.setWindowTitle("블러 뷰포트 컨트롤러")
        self.setGeometry(100, 100, 350, 300)
        
        self.selection_overlay = None
        self.viewport = None
        self.interaction_handler = None

        # 트레이 아이콘에 메인 윈도우의 아이콘을 전달
        self.tray_icon = SystemTrayIcon(app_icon, self)
        self.tray_icon.show_window_requested.connect(self.show_from_tray)
        self.tray_icon.show()
        
        main_layout = QVBoxLayout(self)
        viewport_control_layout = QHBoxLayout()
        self.create_viewport_button = QPushButton("새 뷰포트 생성")
        self.create_viewport_button.setStyleSheet("background-color: #3498db; color: white; padding: 5px;")
        self.close_viewport_button = QPushButton("뷰포트 닫기")
        self.close_viewport_button.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")
        viewport_control_layout.addWidget(self.create_viewport_button)
        viewport_control_layout.addWidget(self.close_viewport_button)
        properties_group = QGroupBox("뷰포트 속성")
        properties_layout = QFormLayout()
        self.check_always_on_top = QCheckBox("항상 위에 표시")
        self.check_always_on_top.setChecked(True)
        self.check_interaction_lock = QCheckBox("상호작용 잠금")
        self.check_interaction_lock.setChecked(False)
        self.check_lock_position = QCheckBox("위치 잠금")
        self.check_lock_size = QCheckBox("크기 잠금")
        properties_layout.addRow(self.check_always_on_top)
        properties_layout.addRow(self.check_interaction_lock)
        properties_layout.addRow(self.check_lock_position)
        properties_layout.addRow(self.check_lock_size)
        properties_group.setLayout(properties_layout)
        self.quit_button = QPushButton("프로그램 종료")
        main_layout.addLayout(viewport_control_layout)
        main_layout.addWidget(properties_group)
        main_layout.addWidget(self.quit_button)
        
        # --- 시그널-슬롯 연결 ---
        self.create_viewport_button.clicked.connect(self.start_viewport_selection)
        self.close_viewport_button.clicked.connect(self.close_viewport)
        self.quit_button.clicked.connect(self.quit_application)
        
        self.check_always_on_top.toggled.connect(self.handle_always_on_top_toggled)
        self.check_interaction_lock.toggled.connect(self.toggle_interaction_visibility)
        self.check_lock_position.toggled.connect(self.handle_position_lock_toggled)
        self.check_lock_size.toggled.connect(self.handle_size_lock_toggled)

    def quit_application(self):
        self._is_quitting = True
        self.close_viewport()
        QApplication.instance().quit()

    def start_viewport_selection(self):
        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.region_selected.connect(self.create_viewport)
        self.selection_overlay.show()
        
    def create_viewport(self, rect: QRect):
        print(f"[DEBUG] create_viewport called with rect: {rect}")
        print(f"[DEBUG] Rect details - x: {rect.x()}, y: {rect.y()}, width: {rect.width()}, height: {rect.height()}")

        # 좌표 유효성 검증 (멀티 모니터 환경 대응)
        # virtualGeometry()는 음수 좌표를 반환할 수 있음
        if rect.width() <= 0 or rect.height() <= 0:
            print(f"경고: 유효하지 않은 뷰포트 크기 - width: {rect.width()}, height: {rect.height()}")
            return

        # 극단적인 음수 좌표 검증 (오류 방지)
        if rect.x() < -10000 or rect.y() < -10000 or rect.x() > 10000 or rect.y() > 10000:
            print(f"경고: 유효하지 않은 좌표 범위 - x: {rect.x()}, y: {rect.y()}")
            return

        print(f"[DEBUG] Validation passed, creating viewport...")

        # 이전 뷰포트가 있다면 명시적으로 삭제
        if self.viewport:
            self.viewport.close()
            self.viewport.deleteLater()
            self.viewport = None
        if self.interaction_handler:
            self.interaction_handler.close()
            self.interaction_handler.deleteLater()
            self.interaction_handler = None

        self.viewport = Viewport()
        self.interaction_handler = InteractionHandler(self.viewport)

        self.viewport.setGeometry(rect)
        self.interaction_handler.setGeometry(rect)
        print(f"[DEBUG] Viewport geometry set to: {self.viewport.geometry()}")
        print(f"[DEBUG] InteractionHandler geometry set to: {self.interaction_handler.geometry()}")

        self.viewport.destroyed.connect(self.interaction_handler.close)
        self.viewport.destroyed.connect(self.on_viewport_closed)

        self.update_viewport_from_ui()

        self.viewport.show()
        self.interaction_handler.show()  # 컨트롤러 표시 (필수!)
        print(f"[DEBUG] Viewport and InteractionHandler shown")

        # show() 호출 후 실제 geometry 확인
        print(f"[DEBUG] After show() - Viewport actual geometry: {self.viewport.geometry()}")
        print(f"[DEBUG] After show() - Viewport isVisible: {self.viewport.isVisible()}")
        print(f"[DEBUG] After show() - Viewport pos: {self.viewport.pos()}")

    def toggle_interaction_visibility(self, checked):
        if self.interaction_handler:
            self.interaction_handler.setVisible(not checked)

    def close_viewport(self):
        if self.viewport:
            self.viewport.close()

    def on_viewport_closed(self):
        self.viewport = None
        self.interaction_handler = None

    def show_from_tray(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        if self._is_quitting:
            self.close_viewport()
            event.accept()
        else:
            event.ignore()
            self.hide()
        
    def update_viewport_from_ui(self):
        if not self.viewport: return
        self.viewport.set_always_on_top(self.check_always_on_top.isChecked())
        self.viewport.set_position_lock(self.check_lock_position.isChecked())
        self.viewport.set_size_lock(self.check_lock_size.isChecked())
        self.toggle_interaction_visibility(self.check_interaction_lock.isChecked())

    def handle_always_on_top_toggled(self, checked):
        if self.viewport:
            self.viewport.set_always_on_top(checked)

    def handle_position_lock_toggled(self, checked):
        if self.viewport:
            self.viewport.set_position_lock(checked)

    def handle_size_lock_toggled(self, checked):
        if self.viewport:
            self.viewport.set_size_lock(checked)