#!/usr/bin/env python3
"""
Script para ejecutar la tienda online
"""
import os
import sys
import subprocess

def main():
    # Verificar si Flask está instalado
    try:
        import flask
    except ImportError:
        print("Flask no está instalado. Instalando dependencias...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Ejecutar la aplicación
    os.system("python app.py")

if __name__ == "__main__":
    main()