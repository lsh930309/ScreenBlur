# settings.py

import os
import json
from pathlib import Path

class SettingsManager:
    """애플리케이션 설정을 관리하는 클래스"""

    def __init__(self):
        """설정 파일 경로 초기화 및 설정 로드"""
        # APPDATA 경로에 애플리케이션 폴더 생성
        appdata = os.getenv('APPDATA')
        if appdata:
            self.settings_dir = Path(appdata) / "ScreenBlur"
        else:
            # APPDATA가 없는 경우 현재 디렉토리 사용 (fallback)
            self.settings_dir = Path.home() / ".screenblur"

        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.settings_dir / "settings.json"

        # 기본 설정
        self.default_settings = {
            "minimize_to_tray": True
        }

        # 설정 로드
        self.settings = self.load_settings()

    def load_settings(self):
        """설정 파일에서 설정을 로드합니다."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # 기본값과 병합 (새로운 설정이 추가된 경우 대비)
                    return {**self.default_settings, **settings}
            except Exception as e:
                print(f"설정 로드 실패: {e}")
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()

    def save_settings(self):
        """현재 설정을 파일에 저장합니다."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def get(self, key, default=None):
        """설정 값을 가져옵니다."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """설정 값을 변경하고 저장합니다."""
        self.settings[key] = value
        self.save_settings()
