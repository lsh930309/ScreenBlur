# build.py

"""
ScreenBlur 빌드 스크립트
PyInstaller를 사용하여 실행 파일을 생성하고 버전 관리를 자동화합니다.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import re

class BuildManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.release_dir = self.root_dir / "release"
        self.archive_dir = self.release_dir / "archive"
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"

        # 가상 환경 경로
        self.venv_dir = self.root_dir / ".venv"
        self.venv_python = self.venv_dir / "Scripts" / "python.exe"
        self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"

    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.release_dir.mkdir(exist_ok=True)
        self.archive_dir.mkdir(exist_ok=True)
        print(f"✓ 디렉토리 확인 완료")

    def check_venv(self):
        """가상 환경 확인"""
        if not self.venv_dir.exists():
            print("❌ .venv 가상 환경을 찾을 수 없습니다.")
            print("다음 명령으로 가상 환경을 생성하세요:")
            print("  python -m venv .venv")
            sys.exit(1)

        if not self.venv_python.exists():
            print("❌ 가상 환경의 Python을 찾을 수 없습니다.")
            sys.exit(1)

        print(f"✓ 가상 환경 확인 완료: {self.venv_dir}")

    def install_pyinstaller(self):
        """PyInstaller 설치 확인 및 설치"""
        try:
            result = subprocess.run(
                [str(self.venv_python), "-m", "pip", "show", "pyinstaller"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✓ PyInstaller가 이미 설치되어 있습니다.")
                return
        except Exception:
            pass

        print("PyInstaller를 설치합니다...")
        try:
            subprocess.run(
                [str(self.venv_pip), "install", "pyinstaller"],
                check=True
            )
            print("✓ PyInstaller 설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"❌ PyInstaller 설치 실패: {e}")
            sys.exit(1)

    def get_next_version(self):
        """다음 버전 번호 생성"""
        # release 폴더에서 기존 exe 파일 찾기
        pattern = re.compile(r"ScreenBlur_v(\d+\.\d+\.\d+)\.exe")
        versions = []

        if self.release_dir.exists():
            for file in self.release_dir.glob("*.exe"):
                match = pattern.match(file.name)
                if match:
                    versions.append(match.group(1))

        if not versions:
            return "1.0.0"

        # 가장 최신 버전 찾기
        latest = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]
        major, minor, patch = map(int, latest.split('.'))

        # 패치 버전 증가
        return f"{major}.{minor}.{patch + 1}"

    def archive_old_versions(self):
        """이전 버전을 archive 폴더로 이동"""
        if not self.release_dir.exists():
            return

        exe_files = list(self.release_dir.glob("*.exe"))

        if exe_files:
            print(f"이전 버전 {len(exe_files)}개를 아카이브로 이동합니다...")
            for exe_file in exe_files:
                dest = self.archive_dir / exe_file.name
                shutil.move(str(exe_file), str(dest))
                print(f"  → {exe_file.name}")
            print("✓ 아카이브 완료")

    def build_executable(self, version):
        """PyInstaller로 실행 파일 빌드"""
        output_name = f"ScreenBlur_v{version}"

        # PyInstaller 명령 구성
        cmd = [
            str(self.venv_python),
            "-m", "PyInstaller",
            "--name", output_name,
            "--onedir",  # onedir 모드
            "--windowed",  # GUI 모드 (콘솔 창 숨김)
            "--icon", "icon.ico",
            "--add-data", "icon.ico;.",  # 아이콘 파일 포함
            "--add-data", "python;python",  # python 폴더 포함
            "--hidden-import", "python.main_window",
            "--hidden-import", "python.viewport",
            "--hidden-import", "python.selection_overlay",
            "--hidden-import", "python.interaction_handler",
            "--hidden-import", "python.system_tray",
            "--hidden-import", "python.settings",
            "--hidden-import", "python.utils",
            "--clean",  # 빌드 전 캐시 정리
            "main.py"
        ]

        print(f"\n빌드 시작: {output_name}")
        print("=" * 60)

        try:
            result = subprocess.run(cmd, check=True)
            print("=" * 60)
            print("✓ 빌드 성공!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 빌드 실패: {e}")
            return False

    def move_to_release(self, version):
        """빌드 결과를 release 폴더로 이동"""
        output_name = f"ScreenBlur_v{version}"
        dist_folder = self.dist_dir / output_name

        if not dist_folder.exists():
            print(f"❌ 빌드 결과를 찾을 수 없습니다: {dist_folder}")
            return False

        # release 폴더로 복사
        release_folder = self.release_dir / output_name

        if release_folder.exists():
            shutil.rmtree(release_folder)

        shutil.copytree(dist_folder, release_folder)
        print(f"✓ 결과물을 release 폴더로 이동: {release_folder}")

        # 실행 파일 직접 링크 생성 (편의성)
        exe_src = release_folder / f"{output_name}.exe"
        exe_dest = self.release_dir / f"{output_name}.exe"

        if exe_src.exists():
            shutil.copy2(exe_src, exe_dest)
            print(f"✓ 실행 파일 생성: {exe_dest.name}")

        return True

    def cleanup_build_artifacts(self):
        """빌드 부산물 정리"""
        print("\n빌드 부산물을 정리합니다...")

        # build 폴더 삭제
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("  ✓ build/ 폴더 삭제")

        # dist 폴더 삭제
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("  ✓ dist/ 폴더 삭제")

        # .spec 파일 삭제
        for spec_file in self.root_dir.glob("*.spec"):
            spec_file.unlink()
            print(f"  ✓ {spec_file.name} 삭제")

        print("✓ 정리 완료")

    def build(self):
        """전체 빌드 프로세스 실행"""
        print("=" * 60)
        print("ScreenBlur 빌드 시작")
        print("=" * 60)
        print()

        # 1. 디렉토리 확인
        self.ensure_directories()

        # 2. 가상 환경 확인
        self.check_venv()

        # 3. PyInstaller 설치 확인
        self.install_pyinstaller()

        # 4. 버전 확인
        version = self.get_next_version()
        print(f"\n📦 빌드 버전: v{version}")

        # 5. 이전 버전 아카이브
        self.archive_old_versions()

        # 6. 빌드 실행
        if not self.build_executable(version):
            print("\n❌ 빌드 실패")
            sys.exit(1)

        # 7. Release 폴더로 이동
        if not self.move_to_release(version):
            print("\n❌ 결과물 이동 실패")
            sys.exit(1)

        # 8. 부산물 정리
        self.cleanup_build_artifacts()

        # 완료
        print("\n" + "=" * 60)
        print("✅ 빌드 완료!")
        print("=" * 60)
        print(f"\n📂 결과물 위치: {self.release_dir / f'ScreenBlur_v{version}'}")
        print(f"📄 실행 파일: {self.release_dir / f'ScreenBlur_v{version}.exe'}")
        print()

if __name__ == "__main__":
    builder = BuildManager()
    builder.build()
