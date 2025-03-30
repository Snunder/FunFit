from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import sys
import subprocess

class PostInstallCommand(install):
    """Post-installation for shortcut creation."""
    def run(self):
        install.run(self)
        self.create_desktop_shortcut()

    def create_desktop_shortcut(self):
        try:
            if sys.platform == "win32":
                self._create_windows_shortcut()
            elif sys.platform == "darwin":
                self._create_macos_shortcut()
            elif sys.platform == "linux":
                self._create_linux_shortcut()
        except Exception as e:
            print(f"Error creating shortcut: {e}")

    def _create_windows_shortcut(self):
        import winshell
        from win32com.client import Dispatch
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "FunFit.lnk")
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = "cmd.exe"
        shortcut.Arguments = '/c funfit'
        shortcut.WorkingDirectory = os.path.expanduser("~")
        shortcut.Description = "Run FunFit in terminal"
        shortcut.IconLocation = os.path.join(os.path.dirname(__file__), "src", "FunFit", "GUI", "icon_window.png")
        shortcut.save()

    def _create_macos_shortcut(self):
        desktop = os.path.expanduser("~/Desktop")
        script_content = """#!/bin/bash
        funfit
        """
        shortcut_path = os.path.join(desktop, "FunFit.command")
        with open(shortcut_path, 'w') as f:
            f.write(script_content)
        os.chmod(shortcut_path, 0o755)

    def _create_linux_shortcut(self):
        desktop = os.path.expanduser("~/Desktop")
        shortcut_path = os.path.join(desktop, "FunFit.desktop")
        icon_path = os.path.join(os.path.dirname(__file__), "src", "FunFit", "GUI", "icon_window.png")
        shortcut_content = f"""[Desktop Entry]
Name=FunFit
Exec=gnome-terminal -- bash -c "funfit; exit"
Icon={icon_path}
Terminal=false
Type=Application
Categories=Science;
"""
        
        with open(shortcut_path, 'w') as f:
            f.write(shortcut_content)
        os.chmod(shortcut_path, 0o755)


setup(
    name="FunFit",
    version="0.1.0",
    author="Sander J. Linde | Magnus V. Nielsen",
    author_email="sanderlinde@hotmail.com | vejby.magnus@gmail.com",
    description="FunFit is a standalone software package designed to analyse SPM topography data.",  # Short description
    license="GPLv3",  # License
    long_description=open("README.md").read(),  # Long description from README
    long_description_content_type="text/markdown",
    url="https://github.com/Snunder/FunFit",  # GitHub repository URL
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    cmdclass={
        'install': PostInstallCommand,  # Trigger shortcut creation
    },
    package_data={
        "FunFit": ["GUI/*.png", "GUI/*.qss", "Functions/*.py"],
    },
    install_requires=[  # List of dependencies
        "numpy>=2.1.1",
        "matplotlib>=3.9.2",
        "PyQt6>=6.8.0.2",
        "scipy>=1.14.1",
        "scikit-learn>=1.5.2",
        "setuptools>=67.6.1",
        "pyobjc>=11.0; sys_platform=='darwin'",
        'winshell; sys_platform == "win32"',
        'pywin32; sys_platform=="win32"',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "gui_scripts": [
            "funfit=FunFit.FunFit_main:main",  # Create a GUI executable
        ],
    },
)