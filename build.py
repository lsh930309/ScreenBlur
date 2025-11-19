# build.py

"""
ScreenBlur 빌드 및 패키징 스크립트
PyInstaller를 사용하여 실행 파일을 생성하고,
Portable 버전(zip)과 Setup 버전(exe)을 자동으로 패키징합니다.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
import re
import zipfile

class BuildManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.release_dir = self.root_dir / "release"
        self.portable_dir = self.release_dir / "portable"
        self.setup_dir = self.release_dir / "setup"
        self.portable_archive_dir = self.portable_dir / "archives"
        self.setup_archive_dir = self.setup_dir / "archives"
        self.build_dir = self.root_dir / "build"
        self.dist_dir = self.root_dir / "dist"

        # 가상 환경 경로
        self.venv_dir = self.root_dir / ".venv"
        self.venv_python = self.venv_dir / "Scripts" / "python.exe"
        self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"

        # Inno Setup 기본 경로
        self.inno_setup_path = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")

    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.release_dir.mkdir(exist_ok=True)
        self.portable_dir.mkdir(exist_ok=True)
        self.setup_dir.mkdir(exist_ok=True)
        self.portable_archive_dir.mkdir(exist_ok=True)
        self.setup_archive_dir.mkdir(exist_ok=True)
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

    def get_version_from_user(self):
        """사용자로부터 버전 입력 받기"""
        # 기존 버전 찾기
        pattern = re.compile(r"screenblur_v(\d+\.\d+\.\d+)_portable\.zip")
        versions = []

        if self.portable_dir.exists():
            for file in self.portable_dir.glob("*.zip"):
                match = pattern.match(file.name)
                if match:
                    versions.append(match.group(1))

        if versions:
            latest = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]
            major, minor, patch = map(int, latest.split('.'))
            suggested_version = f"{major}.{minor}.{patch + 1}"
        else:
            suggested_version = "1.0.0"

        print(f"\n현재 최신 버전: {latest if versions else '없음'}")
        print(f"제안 버전: {suggested_version}")

        while True:
            version_input = input(f"빌드할 버전을 입력하세요 (Enter={suggested_version}): ").strip()

            if not version_input:
                version = suggested_version
                break

            # 버전 형식 검증
            if re.match(r'^\d+\.\d+\.\d+$', version_input):
                version = version_input
                break
            else:
                print("❌ 잘못된 버전 형식입니다. (예: 1.0.0)")

        return version

    def archive_old_versions(self):
        """이전 버전을 archives 폴더로 이동"""
        moved_count = 0

        # Portable 버전 아카이브
        if self.portable_dir.exists():
            zip_files = [f for f in self.portable_dir.glob("*.zip") if f.is_file()]
            for zip_file in zip_files:
                dest = self.portable_archive_dir / zip_file.name
                shutil.move(str(zip_file), str(dest))
                print(f"  → {zip_file.name} (portable)")
                moved_count += 1

        # Setup 버전 아카이브
        if self.setup_dir.exists():
            setup_files = [f for f in self.setup_dir.glob("*.exe") if f.is_file()]
            for setup_file in setup_files:
                dest = self.setup_archive_dir / setup_file.name
                shutil.move(str(setup_file), str(dest))
                print(f"  → {setup_file.name} (setup)")
                moved_count += 1

        if moved_count > 0:
            print(f"✓ {moved_count}개 파일 아카이브 완료")

    def build_executable(self, version):
        """PyInstaller로 실행 파일 빌드"""
        output_name = "ScreenBlur"

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

        print(f"\n빌드 시작: {output_name} v{version}")
        print("=" * 60)

        try:
            result = subprocess.run(cmd, check=True)
            print("=" * 60)
            print("✓ 빌드 성공!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 빌드 실패: {e}")
            return False

    def create_portable_package(self, version):
        """Portable 버전 ZIP 파일 생성"""
        print(f"\nPortable 버전 패키징 중...")

        dist_folder = self.dist_dir / "ScreenBlur"
        if not dist_folder.exists():
            print(f"❌ 빌드 결과를 찾을 수 없습니다: {dist_folder}")
            return False

        zip_filename = f"screenblur_v{version}_portable.zip"
        zip_path = self.portable_dir / zip_filename

        # ZIP 파일 생성
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_folder):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(dist_folder.parent)
                    zipf.write(file_path, arcname)

        print(f"✓ Portable 버전 생성: {zip_filename}")
        print(f"   파일 크기: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        return True

    def create_setup_package(self, version):
        """Inno Setup을 사용하여 Setup 버전 생성"""
        print(f"\nSetup 버전 패키징 중...")

        # Inno Setup 확인
        if not self.inno_setup_path.exists():
            print(f"⚠️  Inno Setup을 찾을 수 없습니다: {self.inno_setup_path}")
            print("   Inno Setup이 설치되어 있지 않거나 다른 경로에 설치되어 있습니다.")

            # 사용자에게 경로 입력 받기
            custom_path = input("Inno Setup ISCC.exe 경로를 입력하세요 (건너뛰려면 Enter): ").strip()

            if custom_path:
                self.inno_setup_path = Path(custom_path)
                if not self.inno_setup_path.exists():
                    print("❌ 입력한 경로에서 Inno Setup을 찾을 수 없습니다.")
                    return False
            else:
                print("⏭️  Setup 버전 생성을 건너뜁니다.")
                return False

        # Inno Setup 스크립트 실행
        iss_file = self.root_dir / "installer.iss"
        if not iss_file.exists():
            print(f"❌ Inno Setup 스크립트를 찾을 수 없습니다: {iss_file}")
            return False

        try:
            cmd = [
                str(self.inno_setup_path),
                f"/DMyAppVersion={version}",
                str(iss_file)
            ]

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ Setup 버전 생성 완료")

            # 생성된 setup 파일 찾기
            setup_filename = f"screenblur_v{version}_setup.exe"
            setup_file = self.setup_dir / setup_filename

            if setup_file.exists():
                print(f"   파일 크기: {setup_file.stat().st_size / 1024 / 1024:.2f} MB")

            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Setup 생성 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False

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
        print("ScreenBlur 빌드 및 패키징")
        print("=" * 60)
        print()

        # 1. 디렉토리 확인
        self.ensure_directories()

        # 2. 가상 환경 확인
        self.check_venv()

        # 3. PyInstaller 설치 확인
        self.install_pyinstaller()

        # 4. 버전 입력
        version = self.get_version_from_user()
        print(f"\n📦 빌드 버전: v{version}")

        # 5. 이전 버전 아카이브
        print(f"\n이전 버전을 아카이브로 이동합니다...")
        self.archive_old_versions()

        # 6. 빌드 실행
        if not self.build_executable(version):
            print("\n❌ 빌드 실패")
            sys.exit(1)

        # 7. Portable 버전 생성
        portable_success = self.create_portable_package(version)

        # 8. Setup 버전 생성
        setup_success = self.create_setup_package(version)

        # 9. 부산물 정리
        self.cleanup_build_artifacts()

        # 완료
        print("\n" + "=" * 60)
        print("✅ 빌드 및 패키징 완료!")
        print("=" * 60)

        if portable_success:
            print(f"\n📦 Portable 버전: release/portable/screenblur_v{version}_portable.zip")

        if setup_success:
            print(f"💿 Setup 버전: release/setup/screenblur_v{version}_setup.exe")

        print(f"\n📁 이전 버전: release/portable/archives, release/setup/archives")
        print()

if __name__ == "__main__":
    builder = BuildManager()
    builder.build()
