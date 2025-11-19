# main.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSharedMemory

from python.main_window import MainWindow

if __name__ == "__main__":
    """애플리케이션의 메인 진입점"""

    # QApplication 인스턴스 생성
    app = QApplication(sys.argv)

    # --- 중복 실행 방지 로직 ---
    # 애플리케이션을 식별하기 위한 고유한 키를 정의합니다.
    unique_key = "blur_viewport_unique_key_af892374"

    # 이 키로 공유 메모리(Shared Memory) 세그먼트를 확인합니다.
    shared_memory = QSharedMemory(unique_key)

    # attach()를 시도하여 이미 생성된 공유 메모리가 있는지 확인합니다.
    # attach()에 성공하면, 다른 인스턴스가 이미 실행 중이라는 의미입니다.
    if shared_memory.attach():
        print("프로그램이 이미 실행 중입니다. 새로운 인스턴스를 종료합니다.")
        sys.exit(0) # 정상 종료

    # attach()에 실패했다면, 현재 인스턴스가 첫 번째 인스턴스입니다.
    # create()를 호출하여 공유 메모리 세그먼트를 생성합니다.
    # 이 메모리는 프로그램이 종료될 때까지 유지됩니다.
    if not shared_memory.create(1): # 1바이트 크기의 세그먼트 생성
        print(f"공유 메모리 생성에 실패했습니다: {shared_memory.errorString()}")
        sys.exit(-1) # 비정상 종료

    # --- 메인 윈도우 생성 및 실행 ---
    # 애플리케이션의 메인 창(컨트롤러)을 생성하고 화면에 표시합니다.
    main_win = MainWindow()
    main_win.show()

    # 애플리케이션 이벤트 루프를 시작합니다.
    # 이 함수는 프로그램이 종료될 때까지 블로킹됩니다.
    sys.exit(app.exec())
