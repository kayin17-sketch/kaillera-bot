#!/usr/bin/env python3
"""Script de verificación del entorno."""

import sys
from pathlib import Path


def check_python_version():
    """Verifica la versión de Python."""
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ requerido")
        return False
    
    print("✅ Versión de Python compatible")
    return True


def check_dependencies():
    """Verifica las dependencias instaladas."""
    dependencies = [
        ('yaml', 'pyyaml'),
        ('cv2', 'opencv-python'),
        ('pynput', 'pynput'),
        ('pyautogui', 'pyautogui'),
        ('mss', 'mss'),
        ('numpy', 'numpy'),
        ('PIL', 'pillow'),
        ('requests', 'requests'),
    ]
    
    all_ok = True
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - no instalado")
            all_ok = False
    
    return all_ok


def check_config():
    """Verifica el archivo de configuración."""
    config_path = Path("config/settings.yaml")
    example_path = Path("config/settings.yaml.example")
    
    if config_path.exists():
        print("✅ config/settings.yaml existe")
        return True
    else:
        print("⚠️  config/settings.yaml no existe")
        if example_path.exists():
            print("   Puedes copiar config/settings.yaml.example y editarlo")
        return False


def check_directories():
    """Verifica que los directorios necesarios existan."""
    dirs = [
        Path("config"),
        Path("output"),
        Path("output/videos"),
        Path("output/inputs"),
        Path("output/network"),
        Path("logs"),
    ]
    
    all_ok = True
    for d in dirs:
        if d.exists():
            print(f"✅ {d}/ existe")
        else:
            print(f"⚠️  {d}/ no existe, creando...")
            try:
                d.mkdir(parents=True, exist_ok=True)
                print(f"✅ {d}/ creado")
            except Exception as e:
                print(f"❌ Error creando {d}/: {e}")
                all_ok = False
    
    return all_ok


def main():
    """Ejecuta todas las verificaciones."""
    print("=" * 50)
    print("VERIFICACIÓN DEL ENTORNO - KAILLERA BOT")
    print("=" * 50)
    print()
    
    print("1. Verificando versión de Python...")
    python_ok = check_python_version()
    print()
    
    print("2. Verificando dependencias...")
    deps_ok = check_dependencies()
    print()
    
    print("3. Verificando configuración...")
    config_ok = check_config()
    print()
    
    print("4. Verificando directorios...")
    dirs_ok = check_directories()
    print()
    
    print("=" * 50)
    if python_ok and deps_ok and dirs_ok:
        if not config_ok:
            print("⚠️  SETUP INCOMPLETO - Configura settings.yaml")
        else:
            print("✅ SETUP COMPLETO - Listo para usar")
    else:
        print("❌ SETUP INCOMPLETO - Revisa los errores arriba")
        print("\nPara instalar dependencias:")
        print("  pip install -e .")
    print("=" * 50)


if __name__ == "__main__":
    main()
