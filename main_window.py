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
        self.setGeometry(100, 100, 300, 200)

        self.selection_overlay = None
        self.viewport = None
        self.interaction_handler = None

        # 트레이 아이콘에 메인 윈도우의 아이콘을 전달
        self.tray_icon = SystemTrayIcon(app_icon, self)
        self.tray_icon.show_window_requested.connect(self.show_from_tray)
        self.tray_icon.show()

        main_layout = QVBoxLayout(self)

        # 뷰포트 생성 버튼
        self.create_viewport_button = QPushButton("새 뷰포트 생성")
        self.create_viewport_button.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-size: 14px;")

        # 설정 그룹
        settings_group = QGroupBox("설정")
        settings_layout = QFormLayout()
        self.check_minimize_to_tray = QCheckBox("닫기 시 트레이로 최소화")
        self.check_minimize_to_tray.setChecked(True)  # 기본값: 활성화
        settings_layout.addRow(self.check_minimize_to_tray)
        settings_group.setLayout(settings_layout)

        # 프로그램 종료 버튼
        self.quit_button = QPushButton("프로그램 종료")
        self.quit_button.setStyleSheet("background-color: #e74c3c; color: white; padding: 5px;")

        main_layout.addWidget(self.create_viewport_button)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(self.quit_button)

        # --- 시그널-슬롯 연결 ---
        self.create_viewport_button.clicked.connect(self.start_viewport_selection)
        self.quit_button.clicked.connect(self.quit_application)

    def quit_application(self):
        self._is_quitting = True
        self.close_viewport()
        QApplication.instance().quit()

    def start_viewport_selection(self):
        """뷰포트 선택 모드를 시작합니다. 메인 창을 숨기고 오버레이를 표시합니다."""
        # 메인 창을 숨겨서 선택 영역에 집중하도록 함
        self.hide()

        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.region_selected.connect(self.create_viewport)
        # 뷰포트 생성 후에는 메인 GUI를 다시 표시하지 않음 (트레이에서만 접근 가능)
        # 선택이 취소된 경우(뷰포트 생성 없이 finished만 호출)에만 다시 표시
        self.selection_overlay.finished.connect(self._on_selection_finished)
        self.selection_overlay.show()

    def _on_selection_finished(self):
        """선택 작업 완료 시 호출. 뷰포트가 생성되지 않은 경우에만 메인 GUI 표시."""
        # 뷰포트가 생성되지 않았다면 메인 GUI를 다시 표시
        if not self.viewport:
            self.show()
        
    def create_viewport(self, rect: QRect):
        """선택된 영역에 블러 뷰포트를 생성합니다."""
        # 좌표 유효성 검증
        if rect.width() <= 0 or rect.height() <= 0:
            print(f"경고: 유효하지 않은 뷰포트 크기 - width: {rect.width()}, height: {rect.height()}")
            return

        # 극단적인 좌표 검증 (오류 방지)
        if rect.x() < -10000 or rect.y() < -10000 or rect.x() > 10000 or rect.y() > 10000:
            print(f"경고: 유효하지 않은 좌표 범위 - x: {rect.x()}, y: {rect.y()}")
            return

        # 이전 뷰포트가 있다면 명시적으로 삭제
        if self.viewport:
            self.viewport.close()
            self.viewport.deleteLater()
            self.viewport = None
        if self.interaction_handler:
            self.interaction_handler.close()
            self.interaction_handler.deleteLater()
            self.interaction_handler = None

        # 뷰포트 생성 (항상 위에 표시는 기본 활성화)
        self.viewport = Viewport()
        # InteractionHandler 생성 시 main_window 참조 전달
        self.interaction_handler = InteractionHandler(self.viewport, self)

        self.viewport.setGeometry(rect)
        self.interaction_handler.setGeometry(rect)

        # destroyed 시그널 대신 커스텀 closing 시그널 사용 (타이밍 이슈 방지)
        self.viewport.closing.connect(self.interaction_handler.close)
        self.viewport.closing.connect(self.on_viewport_closed)

        self.viewport.show()
        self.interaction_handler.show()

    def close_viewport(self):
        """현재 뷰포트를 닫습니다."""
        if self.viewport:
            self.viewport.close()

    def on_viewport_closed(self):
        """뷰포트가 닫혔을 때 호출되는 콜백."""
        self.viewport = None
        self.interaction_handler = None

    def show_from_tray(self):
        """트레이 아이콘에서 메인 창을 표시합니다."""
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        """메인 창 닫기 이벤트 핸들러."""
        if self._is_quitting:
            # 프로그램 종료 시
            self.close_viewport()
            event.accept()
        else:
            # 일반 닫기 시
            if self.check_minimize_to_tray.isChecked():
                # 트레이로 최소화 옵션이 활성화되어 있으면 숨김
                event.ignore()
                self.hide()
            else:
                # 옵션이 비활성화되어 있으면 완전히 종료
                self._is_quitting = True
                self.close_viewport()
                event.accept()
                QApplication.instance().quit()