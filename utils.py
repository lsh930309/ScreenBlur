# utils.py

import sys
import ctypes

def apply_blur(hwnd):
    """특정 창(hwnd)에 Windows의 내부 API를 사용하여 아크릴 블러 효과를 적용합니다.
    
    이 함수는 Windows 운영체제에서만 동작합니다.
    ctypes를 사용하여 user32.dll의 SetWindowCompositionAttribute 함수를 호출합니다.
    
    Args:
        hwnd (int): 블러 효과를 적용할 창의 핸들 (Window Handle).
                     PySide/PyQt에서는 `self.winId()`를 통해 얻을 수 있습니다.
    """
    # Windows 플랫폼이 아니면 함수를 즉시 종료
    if sys.platform != 'win32':
        print("블러 효과는 Windows에서만 지원됩니다.")
        return

    # --- Win32 API 구조체 정의 ---
    # SetWindowCompositionAttribute 함수에 필요한 데이터 구조를 ctypes로 정의합니다.

    class ACCENT_POLICY(ctypes.Structure):
        """블러 종류 및 색상 등 액센트 정책을 정의하는 구조체"""
        _fields_ = [
            ("AccentState", ctypes.c_uint),    # 액센트 상태 (어떤 효과를 줄 것인가)
            ("AccentFlags", ctypes.c_uint),    # 액센트 플래그 (세부 옵션)
            ("GradientColor", ctypes.c_uint), # 배경 색상 및 투명도 (RGBA)
            ("AnimationId", ctypes.c_uint)     # 애니메이션 ID
        ]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        """창 컴포지션 속성 데이터를 전달하기 위한 구조체"""
        _fields_ = [
            ("Attribute", ctypes.c_int),                     # 설정할 속성 (WCA_ACCENT_POLICY)
            ("Data", ctypes.POINTER(ACCENT_POLICY)),      # 속성 데이터 (ACCENT_POLICY 구조체 포인터)
            ("SizeOfData", ctypes.c_size_t)                 # 데이터의 크기
        ]
    
    # --- 블러 효과 설정값 --- #
    # ACCENT_ENABLE_BLURBEHIND: 창 뒤의 콘텐츠를 흐리게 만드는 효과
    # 이 외에도 ACCENT_ENABLE_ACRYLICBLURBEHIND (아크릴 효과) 등이 있지만,
    # 여기서는 가장 기본적인 블러를 사용합니다.
    ACCENT_ENABLE_BLURBEHIND = 3
    WCA_ACCENT_POLICY = 19
    
    # --- 구조체 인스턴스 생성 및 값 설정 ---
    accent = ACCENT_POLICY()
    accent.AccentState = ACCENT_ENABLE_BLURBEHIND
    
    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WCA_ACCENT_POLICY  # 액센트 정책을 설정하겠다고 지정
    data.SizeOfData = ctypes.sizeof(accent) # 데이터 크기 명시
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ACCENT_POLICY))
    
    # --- Win32 API 함수 호출 ---
    try:
        user32 = ctypes.windll.user32
        # SetWindowCompositionAttribute 함수를 호출하여 창에 블러 효과 적용
        result = user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        if not result:
            print(f"경고: 블러 효과 적용 실패 (hwnd: {hwnd})")
            print(f"      Windows 버전이 블러를 지원하지 않을 수 있습니다.")
    except AttributeError as e:
        print(f"오류: SetWindowCompositionAttribute 함수를 찾을 수 없습니다.")
        print(f"      이 기능은 Windows 10 이상에서만 지원됩니다.")
        print(f"      상세 오류: {e}")
    except Exception as e:
        print(f"오류: 블러 효과 적용 중 예상치 못한 오류 발생")
        print(f"      hwnd: {hwnd}")
        print(f"      상세 오류: {type(e).__name__}: {e}")
