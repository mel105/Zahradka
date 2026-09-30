"""Vytvorí ikonu Záhradka na ploche (Windows) alebo spúšťač v menu a na ploche (Linux).
Spusti ho tým Pythonom, ktorým má apka bežať (napr. ...\\Env\\Personal\\Scripts\\python.exe).
"""
import base64
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PYW = os.path.join(BASE, "zahradka.pyw")


def windows():
    exe_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(exe_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        print(f"Nenašiel som {pythonw}. Spusti skript Pythonom z env (…\\Scripts\\python.exe).")
        sys.exit(1)
    ico = os.path.join(BASE, "zahradka.ico")
    ps = f"""
$d = [Environment]::GetFolderPath('Desktop')
$s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'Záhradka.lnk'))
$s.TargetPath = '{pythonw}'
$s.Arguments = '"{PYW}"'
$s.WorkingDirectory = '{BASE}'
$s.IconLocation = '{ico}'
$s.Description = 'Záhradka – kalendár a denník záhrady'
$s.Save()
Write-Output (Join-Path $d 'Záhradka.lnk')
"""
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("Nepodarilo sa vytvoriť odkaz:\n", r.stderr)
        sys.exit(1)
    print("Odkaz vytvorený:", r.stdout.strip())
    print("Python v odkaze:", pythonw)


def linux():
    py = shutil.which("python3") or sys.executable
    desktop = f"""[Desktop Entry]
Type=Application
Name=Záhradka
Comment=Kalendár a denník záhrady
Exec={py} "{PYW}"
Icon={os.path.join(BASE, 'zahradka.png')}
Terminal=false
Categories=Utility;
"""
    apps = os.path.expanduser("~/.local/share/applications")
    os.makedirs(apps, exist_ok=True)
    ciele = [os.path.join(apps, "zahradka.desktop")]
    try:
        plocha = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True).stdout.strip()
    except OSError:
        plocha = ""
    if not plocha or not os.path.isdir(plocha):
        plocha = next((p for p in (os.path.expanduser("~/Plocha"), os.path.expanduser("~/Desktop")) if os.path.isdir(p)), "")
    if plocha:
        ciele.append(os.path.join(plocha, "zahradka.desktop"))
    for c in ciele:
        with open(c, "w", encoding="utf-8") as f:
            f.write(desktop)
        os.chmod(c, 0o755)
        try:
            subprocess.run(["gio", "set", c, "metadata::trusted", "true"], capture_output=True)
        except OSError:
            pass
        print("Vytvorené:", c)
    print("GNOME: ak sa ikona na ploche nespustí, pravý klik → Povoliť spúšťanie.")


if __name__ == "__main__":
    windows() if os.name == "nt" else linux()
