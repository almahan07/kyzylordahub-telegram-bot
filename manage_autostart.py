import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
SHORTCUT_PATH = STARTUP_DIR / "KyzylordaHubBot.lnk"
VBS_SCRIPT = BASE_DIR / "start_bot_hidden.vbs"

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def install():
    print("=" * 60)
    print("🚀 Kyzylorda Hub ботын Windows Автозагрузкасына қосу...")
    print("=" * 60)

    if not VBS_SCRIPT.exists():
        print(f"❌ Қате: {VBS_SCRIPT} файлы табылмады!")
        return False

    vbs_creator = BASE_DIR / "_temp_create_shortcut.vbs"
    vbs_code = f"""
Set ws = CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut("{SHORTCUT_PATH}")
sc.TargetPath = "wscript.exe"
sc.Arguments = Chr(34) & "{VBS_SCRIPT}" & Chr(34)
sc.WorkingDirectory = "{BASE_DIR}"
sc.Save
"""
    try:
        vbs_creator.write_text(vbs_code.strip(), encoding="utf-8")
        subprocess.run(["cscript", "//nologo", str(vbs_creator)], check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Жарлық жасау кезінде қате: {e}")
        return False
    finally:
        if vbs_creator.exists():
            vbs_creator.unlink()

    if SHORTCUT_PATH.exists():
        print("✅ [СӘТТІ] Бот Windows Автозагрузкасына қосылды!")
        print(f"📁 Жарлық орны: {SHORTCUT_PATH}")
        print("💡 Енді ноутбук қосылған сайын бот артқы фонда автоматты түрде қосылады.")
        return True
    else:
        print("❌ Жарлық жасау мүмкін болмады.")
        return False


def uninstall():
    print("=" * 60)
    print("🗑️ Kyzylorda Hub ботын Автозагрузкадан өшіру...")
    print("=" * 60)

    if SHORTCUT_PATH.exists():
        try:
            SHORTCUT_PATH.unlink()
            print("✅ [СӘТТІ] Бот автозагрузкадан өшірілді.")
            return True
        except Exception as e:
            print(f"❌ Өшіру кезінде қате: {e}")
            return False
    else:
        print("ℹ️ Бот автозагрузкада жоқ немесе бұрын өшірілген.")
        return True


def status():
    exists = SHORTCUT_PATH.exists()
    if exists:
        print(f"🟢 Автозагрузка қосулы: {SHORTCUT_PATH}")
    else:
        print("🔴 Автозагрузка өшірулі (ноут қосылғанда бот автоматты түрде қосылмайды)")
    return exists


if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "install"
    if action == "install":
        install()
    elif action == "uninstall":
        uninstall()
    elif action == "status":
        status()
    else:
        print("Қолданылуы: python manage_autostart.py [install|uninstall|status]")
