# selection_overlay.py

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QBrush, QColor, QPen

class SelectionOverlay(QWidget):
    """화면 전체를 덮어 사용자로부터 특정 영역을 선택받기 위한 투명 오버레이 위젯"""
    
    # 시그널 정의: 사용자가 영역 선택을 완료했을 때 선택된 영역(QRect) 정보를 전달
    region_selected = Signal(QRect)

    def __init__(self):
        """생성자: 오버레이 창의 기본 속성을 설정합니다."""
        super().__init__()

        # --- 창 설정 ---
        # 메인 모니터 영역만 덮도록 설정 (멀티 모니터 환경에서 뷰포트 생성 제한)
        # geometry()는 메인 모니터만, virtualGeometry()는 모든 모니터 포함
        screen_geometry = QApplication.instance().primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        
        # 창의 테두리를 없애고, 항상 다른 창들 위에 표시되도록 설정
        # 배경을 투명하게 만들어 아래의 화면이 보이도록 함
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # --- 마우스 설정 ---
        # 마우스 움직임을 실시간으로 감지하기 위해 마우스 트래킹 활성화
        self.setMouseTracking(True)
        # 사용자가 선택 중임을 직관적으로 알 수 있도록 커서를 십자 모양으로 변경
        self.setCursor(Qt.CrossCursor)
        
        # --- 선택 영역 좌표 초기화 ---
        self.start_point = None  # 마우스 드래그 시작점
        self.end_point = None    # 마우스 드래그 끝점

    def paintEvent(self, event):
        """위젯이 다시 그려져야 할 때 호출되는 이벤트 핸들러. 선택 영역을 시각적으로 표시합니다."""
        painter = QPainter(self)
        
        # 1. 반투명 검은색 배경 그리기
        # 화면 전체를 어둡게 하여 사용자가 선택 영역에 집중하도록 돕는다.
        overlay_color = QColor(0, 0, 0, 120) # 검은색, 약 47% 투명도
        painter.fillRect(self.rect(), QBrush(overlay_color))
        
        # 2. 선택 영역 그리기 (드래그 중일 때)
        if self.start_point and self.end_point:
            # 시작점과 끝점으로 사각형(QRect)을 정의하고, 음수 크기를 갖지 않도록 정규화
            selection_rect = QRect(self.start_point, self.end_point).normalized()
            
            # 선택된 영역을 투명하게 만들어 원래 화면이 보이도록 함
            # CompositionMode_Clear: 해당 영역의 모든 픽셀을 지움
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(selection_rect, Qt.transparent)
            
            # 이후의 그리기를 위해 기본 모드로 복원
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # 선택 영역의 테두리를 점선으로 그려 경계를 명확히 함
            pen = QPen(Qt.white, 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        """마우스 버튼을 눌렀을 때 호출됩니다. 드래그 시작점을 기록합니다."""
        self.start_point = event.position().toPoint()
        self.end_point = self.start_point # 초기에는 시작점과 끝점을 동일하게 설정
        self.update() # paintEvent()를 다시 호출하여 화면을 갱신

    def mouseMoveEvent(self, event):
        """마우스를 누른 채로 움직일 때 호출됩니다. 드래그 끝점을 갱신합니다."""
        if self.start_point: # 마우스가 눌린 상태일 때만
            self.end_point = event.position().toPoint()
            self.update() # 화면 갱신

    def mouseReleaseEvent(self, event):
        """마우스 버튼에서 손을 뗐을 때 호출됩니다. 선택 완료 신호를 보냅니다."""
        if self.start_point and self.end_point:
            selection_rect = QRect(self.start_point, self.end_point).normalized()

            # 너비와 높이가 0보다 큰 유효한 영역이 선택되었는지 확인
            if selection_rect.width() > 0 and selection_rect.height() > 0:
                # 위젯 로컬 좌표를 전역 화면 좌표로 변환
                global_top_left = self.mapToGlobal(selection_rect.topLeft())
                global_rect = QRect(global_top_left, selection_rect.size())

                # region_selected 시그널에 선택된 영역 정보를 담아 보냄
                self.region_selected.emit(global_rect)

        self.close() # 영역 선택이 완료되면 오버레이 창을 닫음
