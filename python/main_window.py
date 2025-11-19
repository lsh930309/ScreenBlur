# main_window.py

import os
import sys
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QGroupBox,
                               QCheckBox, QFormLayout, QApplication, QHBoxLayout, QLabel)
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QCloseEvent, QIcon, QPalette

from .viewport import Viewport
from .selection_overlay import SelectionOverlay
from .system_tray import SystemTrayIcon
from .interaction_handler import InteractionHandler
from .settings import SettingsManager

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

        # 설정 관리자 초기화
        self.settings = SettingsManager()

        # --- 아이콘 설정 ---
        # PyInstaller 환경 대응: 올바른 리소스 경로 사용
        app_icon = QIcon(resource_path("icon.ico"))
        self.setWindowIcon(app_icon)

        self.setWindowTitle("Screen Blur")

        self.selection_overlay = None
        self.viewport = None
        self.interaction_handler = None

        # 트레이 아이콘에 메인 윈도우의 아이콘을 전달
        self.tray_icon = SystemTrayIcon(app_icon, self)
        self.tray_icon.show_window_requested.connect(self.show_from_tray)
        self.tray_icon.show()

        # --- UI 구성 ---
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 타이틀
        title_label = QLabel("화면 가리개")
        title_font = title_label.font()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        # 버튼 레이아웃 (가리개 생성 + 모든 가리개 닫기)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 가리개 생성 버튼 (초록색 배경)
        self.create_viewport_button = QPushButton("가리개 생성")
        self.create_viewport_button.setMinimumHeight(40)
        self.create_viewport_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        # 모든 가리개 닫기 버튼 (빨간색 배경)
        self.close_all_button = QPushButton("모든 가리개 닫기")
        self.close_all_button.setMinimumHeight(40)
        self.close_all_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)

        button_layout.addWidget(self.create_viewport_button)
        button_layout.addWidget(self.close_all_button)

        # 체크박스 옵션들 (그룹 없이 심플하게)
        self.check_lock = QCheckBox("가리개 위치 고정")
        self.check_lock.setChecked(False)

        self.check_minimize_to_tray = QCheckBox("닫기 시 트레이로 최소화")
        self.check_minimize_to_tray.setChecked(self.settings.get("minimize_to_tray", True))

        # 프로그램 종료 버튼 (주황색 배경, bold)
        self.quit_button = QPushButton("프로그램 종료")
        self.quit_button.setMinimumHeight(40)
        quit_font = self.quit_button.font()
        quit_font.setBold(True)
        self.quit_button.setFont(quit_font)
        self.quit_button.setStyleSheet("""
            QPushButton {
                background-color: #ff8c00;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e67e00;
            }
            QPushButton:pressed {
                background-color: #cc7000;
            }
        """)

        # 레이아웃에 위젯 추가
        main_layout.addWidget(title_label)
        main_layout.addLayout(button_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.check_lock)
        main_layout.addWidget(self.check_minimize_to_tray)
        main_layout.addStretch()
        main_layout.addWidget(self.quit_button)

        # --- 시그널-슬롯 연결 ---
        self.create_viewport_button.clicked.connect(self.start_viewport_selection)
        self.check_lock.toggled.connect(self.handle_lock_toggled)
        self.close_all_button.clicked.connect(self.close_viewport)
        self.check_minimize_to_tray.toggled.connect(self.handle_minimize_to_tray_toggled)
        self.quit_button.clicked.connect(self.quit_application)

        # --- UI 레이아웃 기반 최적 크기 자동 계산 및 고정 ---
        self.adjustSize()  # 레이아웃이 필요로 하는 크기로 창 크기 조정
        optimal_size = self.size()  # 조정된 크기 가져오기
        self.setFixedSize(optimal_size)  # 해당 크기로 고정

    def quit_application(self):
        """애플리케이션을 종료합니다."""
        self._is_quitting = True
        self.close_viewport()
        QApplication.instance().quit()

    def handle_lock_toggled(self, checked):
        """고정 체크박스 상태 변경 핸들러."""
        if self.viewport:
            self.viewport.set_lock(checked)

    def handle_minimize_to_tray_toggled(self, checked):
        """트레이 최소화 옵션 변경 핸들러 - 설정 저장."""
        self.settings.set("minimize_to_tray", checked)

    def start_viewport_selection(self):
        """가리개 선택 모드를 시작합니다. 메인 창을 숨기고 오버레이를 표시합니다."""
        # 메인 창을 숨겨서 선택 영역에 집중하도록 함
        self.hide()

        self.selection_overlay = SelectionOverlay()
        self.selection_overlay.region_selected.connect(self.create_viewport)
        # 선택 작업 완료 시 메인 GUI를 항상 다시 표시
        self.selection_overlay.finished.connect(self.show)
        self.selection_overlay.show()

    def create_viewport(self, rect: QRect):
        """선택된 영역에 블러 가리개를 생성합니다."""
        # 좌표 유효성 검증
        if rect.width() <= 0 or rect.height() <= 0:
            print(f"경고: 유효하지 않은 가리개 크기 - width: {rect.width()}, height: {rect.height()}")
            return

        # 극단적인 좌표 검증 (오류 방지)
        if rect.x() < -10000 or rect.y() < -10000 or rect.x() > 10000 or rect.y() > 10000:
            print(f"경고: 유효하지 않은 좌표 범위 - x: {rect.x()}, y: {rect.y()}")
            return

        # 이전 가리개가 있다면 명시적으로 삭제
        if self.viewport:
            self.viewport.close()
            self.viewport.deleteLater()
            self.viewport = None
        if self.interaction_handler:
            self.interaction_handler.close()
            self.interaction_handler.deleteLater()
            self.interaction_handler = None

        # 가리개 생성 (항상 위에 표시는 기본 활성화)
        self.viewport = Viewport()
        # InteractionHandler 생성 시 main_window 참조 전달
        self.interaction_handler = InteractionHandler(self.viewport, self)

        self.viewport.setGeometry(rect)
        self.interaction_handler.setGeometry(rect)

        # destroyed 시그널 대신 커스텀 closing 시그널 사용 (타이밍 이슈 방지)
        self.viewport.closing.connect(self.interaction_handler.close)
        self.viewport.closing.connect(self.on_viewport_closed)

        # 현재 고정 상태를 가리개에 적용
        self.viewport.set_lock(self.check_lock.isChecked())

        self.viewport.show()
        self.interaction_handler.show()

    def close_viewport(self):
        """현재 가리개를 닫습니다."""
        if self.viewport:
            self.viewport.close()

    def on_viewport_closed(self):
        """가리개가 닫혔을 때 호출되는 콜백."""
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