import sys
import subprocess
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import qdarkstyle
import tempfile
import zipfile
import io
import os
import concurrent.futures
import ctypes
import psutil
import platform
import pyopencl as cl
import requests
import tempfile
import multiprocessing
from collections import OrderedDict
from multiprocessing import freeze_support

program_dir = os.path.dirname(os.path.abspath(__file__))
tweakler_dir = os.path.join(program_dir, "Tweakler KURCALAMA")


def check_and_update_winget():
    try:
        result = subprocess.run(['winget', '--version'], capture_output=True, text=True, shell=True)
        current_version = result.stdout.strip()
        print("Winget sürümü:", current_version)

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        update_result = subprocess.run(['winget', 'upgrade', 'winget'], capture_output=True, text=True, startupinfo=startupinfo)
        updated_version = update_result.stdout.strip()
        print("Güncellenmiş sürüm:", updated_version)

        return current_version, updated_version

    except Exception as e:
        print(f"Hata oluştu: {e}")
        return None, None
    
    
class CustomDialog(QDialog):
    def __init__(self, title, message, notes):
        super().__init__()

        self.setWindowTitle(title)

        layout = QVBoxLayout()

        # Mesaj
        message_label = QLabel(message)
        layout.addWidget(message_label)

        # Notlar
        notes_text_edit = QTextEdit()
        notes_text_edit.setPlainText(notes)  # setText yerine setPlainText kullanın
        notes_text_edit.setReadOnly(True)  # Notları sadece okunabilir yapın
        layout.addWidget(notes_text_edit)

        yes_button = QPushButton("Evet")
        yes_button.clicked.connect(self.accept)
        layout.addWidget(yes_button)

        no_button = QPushButton("Hayır")
        no_button.clicked.connect(self.reject)
        layout.addWidget(no_button)

        self.setLayout(layout)
        
class CustomDialog2(QDialog):
    def __init__(self, title, message):
        super(CustomDialog2, self).__init__()

        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(message)
        layout.addWidget(label)

        ok_button = QPushButton("Tamam")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def show_dialog(self):
        self.exec_()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log_text = QTextEdit()
        self.setWindowTitle("Program Yöneticisi")
        self.setGeometry(100, 100, 750, 600)
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        self.create_menu()
        self.search_results = None
        self.version_label = None
        

        tabs = [("Programlar", self.add_programs_tab),
                ("Chocolatey", self.add_choco_tab),
                ("Tweakler", self.add_tweaks_tab),
                ("Güncelleştirmeler", self.add_updates_tab),
                ("Program Kaldırma", self.add_uninstall_tab),
                ("Hakkında", self.add_about_tab),
                ("Sistem Bilgileri", self.add_system_info_tab)
                ]
        for title, method in tabs:
            self.add_tab(title, method)
            
        self.apply_windows_theme()

    def add_tab(self, title, add_content_method):
        tab = QWidget()
        self.tab_widget.addTab(tab, title)
        add_content_method(tab)
        
    def add_choco_tab(self, tab):
        layout = QVBoxLayout()
        chocoprograms_list = [
            "Discord", "Steam", "Afterburner", "Google Drive", "Notebook-FanControl", "BlueStacks",
            "FX Sound", "Lively Wallpaper", "Winrar", "Vlc Media Player", "HWInfo",
            "Spacedesk Windows Driver", "Nvidia Gaming Experience", "Nvidia Display Driver", "Whatsapp",
            "MS Zoom", "Opera GX Browser", "Spotify", "Apple iTunes", "Deezer", "Youtube Music Desktop",
            "Epic Games", "Skype", "Adobe Acrobat (64bit)", "LibreOffice", "Google Chrome", "Cloudflare WARP",
            "7Zip", "AIDA 64 Extreme Portable", "Recuva", "Rufus Portable", "Brave Browser", "Teamviewer", "QBitTorrent",
            "CCleaner Portable"
        ]
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        checkboxes = []
        for program in chocoprograms_list:
            checkbox = QCheckBox(program)
            checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)
            
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        
        button_layout = QHBoxLayout()
        
        install_choco_button = QPushButton("Chocolatey'i kur")
        install_choco_button.clicked.connect(self.install_choco)
        button_layout.addWidget(install_choco_button)
        
        choco_kur_button = QPushButton("Chocolatey ile Kur")
        choco_kur_button.clicked.connect(lambda: self.install_choco_programs(checkboxes))
        button_layout.addWidget(choco_kur_button)
        
        layout.addWidget(scroll_area)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)
        
    def install_choco(self):
        subprocess.run(["powershell", "-Command", "Set-ExecutionPolicy", "Bypass", "-Scope", "Process",
                            "-Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"])
        
        
    def install_choco_programs(self, checkboxes):
        for checkbox in checkboxes:
            if checkbox.isChecked():
                program_name = checkbox.text().replace(" ", "").lower()
                try:
                    if program_name == "discord":
                        command = f"choco install discord -y"
                    elif program_name == "afterburner":
                        command = f"choco install msiafterburner -y"
                    elif program_name == "steam":
                        command = f"choco install steam -y"
                    elif program_name == "notebook-fancontrol":
                        command = f"choco install nbfc -y"
                    elif program_name == "bluestacks":
                        command = f"choco install bluestacks -y"
                    elif program_name == "fxsound":
                        command = f"choco install fxsound -y"
                    elif program_name == "livelywallpaper":
                        command = f"choco install lively -y"
                    elif program_name == "winrar":
                        command = f"choco install winrar -y"
                    elif program_name == "vlcmediaplayer":
                        command = f"choco install vlc -y"
                    elif program_name == "hwinfo":
                        command = f"choco install hwinfo.portable -y"
                    elif program_name == "spacedeskwindowsdriver":
                        command = f"choco install spacedesk-server -y"
                    elif program_name == "nvidiagamingexperience":
                        command = f"choco install nvidia-geforce-now -y"
                    elif program_name == "nvidiadisplaydriver":
                        command = f"choco install nvidia-display-driver -y"
                    elif program_name == "whatsapp":
                        command = f"choco install whatsapp --version 2.2306.9 -y"
                    elif program_name == "mszoom":
                        command = f"choco install zoom -y"
                    elif program_name == "operagxbrowser":
                        command = f"choco install opera-gx -y"
                    elif program_name == "spotify":
                        command = f"choco install spotify -y"
                    elif program_name == "appleitunes":
                        command = f"choco install itunes -y"
                    elif program_name == "deezer":
                        command = f"choco install deezer -y"
                    elif program_name == "youtubemusicdesktop":
                        command = f"choco install th-ch-youtube-music -y"
                    elif program_name == "epicgames":
                        command = f"choco install epicgameslauncher -y"
                    elif program_name == "skype":
                        command = f"choco install skype -y"
                    elif program_name == "adobereader64bit":
                        command = f"choco install adobereader -y"
                    elif program_name == "libreoffice":
                        command = f"choco install libreoffice-fresh -y"
                    elif program_name == "googlechrome":
                        command = f"choco install googlechrome -y"
                    elif program_name == "cloudflarewarp":
                        command = f"choco install warp -y"
                    elif program_name == "7zip":
                        command = f"choco install 7zip -y"
                    elif program_name == "aida64extremeportable":
                        command = f"choco install aida64-extreme.portable -y"
                    elif program_name == "recuva":
                        command = f"choco install recuva -y"
                    elif program_name == "rufusportable":
                        command = f"choco install rufus.portable -y"
                    elif program_name == "bravebrowser":
                        command = f"choco install brave -y"
                    elif program_name == "teamviewer":
                        command = f"choco install teamviewer9"
                    elif program_name == "qbittorrent":
                        command = f"choco install qbittorrent -y"
                    elif program_name == "ccleanerportable":
                        command = f"choco install ccleaner.portable -y"
                    elif program_name == "googledrive":
                        command = f"choco install googledrive -y"
                    # Diğer programlar için benzer şekilde ekleyin
                    else:
                        print(f"{program_name} için uygun kurulum komutu bulunamadı.")
                        return

                    subprocess.run(command, check=True, shell=True)
                    QMessageBox.information(self, "Kurulum Tamamlandı", f"{program_name} başarıyla kuruldu!")
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "Hata", f"{program_name} kurulumunda bir hata oluştu: {e}")
    def add_programs_tab(self, tab):
        layout = QVBoxLayout()
        programs_list = [
            "Discord", "Steam", "Afterburner", "Notebook-FanControl", "BlueStacks",
            "Visual Studio programlari -Hepsi bir arada- (Oyunlar icin)", "FxSound",
            "Lively Wallpaper", "Winrar", "Vlc Media Player", "HWInfo",
            "Spacedesk Windows Driver", "Nvidia Gaming Experience", "Whatsapp", "MS Zoom", "Opera GX Browser",
            "Spotify", "Apple iTunes", "Deezer", "Youtube Music Desktop", "Epic Games", "Skype",
            "Adobe Acrobat (64bit)", "Yandex Disk", "LibreOffice", "LOL EUW", "Chrome", "Cloudflare WARP",
            "7Zip", "AIDA 64 Extreme", "Recuva", "Rufus", "Brave Browser", "Teamviewer", "QBitTorrent", "CCleaner", "DirectX"
        ]
        


        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()


        checkboxes = []
        for program in programs_list:
            checkbox = QCheckBox(program)
            checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)
        
        button_layout = QHBoxLayout()

        search_program_button = QPushButton("Program Ara")
        search_program_button.clicked.connect(self.open_program_search_windows)
        button_layout.addWidget(search_program_button)
        
        
        
        kur_button = QPushButton("Kur")
        kur_button.clicked.connect(lambda: self.install_programs(checkboxes))
        button_layout.addWidget(kur_button)
        
        
        layout.addWidget(scroll_area)
        layout.addLayout(button_layout)
        
        tab.setLayout(layout)



    def open_program_search_windows(self):
        self.search_results = QTextEdit()
        search_dialog = QDialog(self)
        search_dialog.setWindowTitle("Program Ara")
        search_dialog.setModal(False)
        
        
        layout = QVBoxLayout()
        
        search_input = QLineEdit()
        search_button = QPushButton("Ara")
        search_results = QTextEdit()
        
        layout.addWidget(search_input)
        layout.addWidget(search_button)
        layout.addWidget(search_results)
        

        search_dialog.setLayout(layout)
        search_dialog.resize(600, 500)
        search_dialog.show()
        
        
        search_button.clicked.connect(lambda: self.search_programs(search_input.text(), search_results))
        

    def run_subprocess_powershell(self, command):
        subprocess.run(["powershell.exe", "-Command", command], check=True, shell=True)


    def search_programs(self, search_term, results_textedit):
        command = f"winget search --name {search_term} --source winget"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            lines = output.splitlines()
            if lines:
                formatted_output = "\n".join(f"- {line}" for line in lines)
                results_textedit.setPlainText(formatted_output)
                
                reply = QMessageBox.question(self, 'Kurulum Onayı','Kurulum başlatılsın mı?', QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    selected_program = search_term
                    self.install_selected_program_from_search(selected_program)
            else:
                results_textedit.setPlainText("Program bulunamadı.")
        except subprocess.CalledProcessError as e:
            results_textedit.setPlainText(f"Hata: {e.output}")
    
    
    def install_selected_program_from_search(self, selected_program):
        try:
            result = subprocess.run(["winget", "install", selected_program, "--source", "winget"], capture_output=True, text=True)
            if result.returncode == 0:
                QMessageBox.information(self, "Kurulum Tamamlandı", f"{selected_program} programının kurulumu tamamlandı!")
            else:
                QMessageBox.critical(self, "Hata", f"{selected_program} kurulamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"{selected_program} kurulamadı. Hata: {str(e)}")
    
        

    def install_selected_from_list(self):
        selected_text = self.search_results.textCursor().selectedText()
        selected_program = selected_text.split('- ')[-1].strip()
        self.install_selected_program(selected_program)
        
    def install_programs(self, checkboxes):
        selected_programs = [checkbox.text().lower().replace(" ", "") for checkbox in checkboxes if checkbox.isChecked()]
        self.log_text.clear()

        program_actions = OrderedDict([
            ("DirectX", self.install_directx),
            ("Visual Studio programlari -Hepsi bir arada- (Oyunlar icin)", self.install_visual),
                ])
            # Diğer program işlemlerini buraya ekleyin
        

        for checkbox in checkboxes:
            if checkbox.isChecked():
                program_name = checkbox.text().lower().replace(" ", "")
                action = program_actions.get(program_name, lambda: self.run_subprocess_powershell(
                    f"winget install {program_name} --source winget"))
                action()

        QMessageBox.information(self, "Kurulum Tamamlandı", "Seçilen programların kurulumu tamamlandı!")
    def install_directx(self):
        url = 'https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe'
        temp_directory = tempfile.mkdtemp()
        file_name = os.path.join(temp_directory, 'dxwebsetup.exe')
        
        try:
            with open(file_name, 'wb') as file:
                file.write(requests.get(url).content)
            os.startfile(file_name)
            
        except Exception as e:
            print(f"Hata: {e}")
            
    def install_visual(self):
        versions = {
            "2008": "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x64.exe",
            "2010": "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe",
            "2012": "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe",
            "2013": "https://aka.ms/highdpimfc2013x64enu",
            "2015-2022": "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        }
        temp_directory = tempfile.mkdtemp()
        
        for version, url in versions.items():
            file_name = os.path.join(temp_directory, f"vcredist_{version}_x64.exe")
            
            try: #indirme işlevi.
                response = requests.get(url)
                with open (file_name, "wb") as file:
                    file.write(response.content)
                subprocess.run([file_name])
                
            except Exception as e:
                print(f"Hata: {e}")
        
    def add_tweaks_tab(self, tab):
        layout = QVBoxLayout()
        tweaks_list = [
            "UWT 5.1 (Ultimate Windows Tweaker 5.1)",
            "Chocolatey",
            "DNS Jumper",
            "BloatyNosy",
            "Linus Titus Uzman Ayarlari",
            "Sağ Tık Güç Seceneklerini Ayarlama Özelliği Ekleme",
            "Sağ Tık Güç Seçeneklerini Ayarlama Özelliği İptali",
            "Güç Seçeneklerine CPU Frekansı Ayarı Getirme/Kaldırma",
            "Msi Utility V3",
            "SSD Booster",
            "Optimizer",
            "InsPolicyx64",
            "WingetUI Installer (Başlaması için 2dk kadar bekleyin!)",
            "SDIO Driver",
            "AppCopier",
            "Custom Resolution Utility (CRU)"
            # Diğer tweakler buraya eklenebilir
        ]
        num_processes = multiprocessing.cpu_count()
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_processes) as executor:
            executor.map(self.apply_tweaks, tweaks_list)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        checkboxes = []
        for tweak in tweaks_list:
            checkbox = QCheckBox(tweak)
            checkboxes.append(checkbox)
            scroll_layout.addWidget(checkbox)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_widget)

        apply_button = QPushButton("Uygula")
        apply_button.clicked.connect(lambda: self.apply_tweaks(checkboxes))

        layout.addWidget(scroll_area)
        layout.addWidget(apply_button, alignment=Qt.Alignment(0x84))

        tab.setLayout(layout)

    def apply_tweaks(self, checkboxes):
        selected_tweaks = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]
        for tweak in selected_tweaks:
            if tweak == "UWT 5.1 (Ultimate Windows Tweaker 5.1)":
                uwt_url = "https://www.thewindowsclub.com/downloads/UWT5.zip"
                temp_file_path = os.path.join(tempfile.gettempdir(), "UWT5.zip")
                response = requests.get(uwt_url)
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    
                # Klasörü çıkarmak için geçici bir yol oluştur
                extracted_folder_path = os.path.join(tempfile.gettempdir(), "UWT5_extracted")
                os.makedirs(extracted_folder_path, exist_ok=True)
    
                # Tüm dosyaları belirtilen klasöre çıkar
                zip_file.extractall(path=extracted_folder_path)
    
                # Çıkartılan klasör içinde dosyayı bul
                uwt_exe_path = None
                for root, dirs, files in os.walk(extracted_folder_path):
                    for file in files:
                        if file == "Ultimate Windows Tweaker 5.1.exe":
                            uwt_exe_path = os.path.join(root, file)
                            break
                if uwt_exe_path:
                    subprocess.Popen([uwt_exe_path], shell=True)
                else:
                    print("Ultimate Windows Tweaker 5.1.exe dosyası bulunamadı.")
            elif tweak == "Custom Resolution Utility (CRU)":
                cru_url = "https://www.monitortests.com/download/cru/cru-1.5.2.zip"
                response = requests.get(cru_url)
                temp_folder = tempfile.mkdtemp()
                zip_file_path = os.path.join(temp_folder, "cru-1.5.2.zip")
                with open (zip_file_path, "wb") as file:
                    file.write(response.content)
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)
                exe_files = [f for f in os.listdir(temp_folder) if f.endswith(".exe")]
                if exe_files:
                    exe_path = os.path.join(temp_folder, exe_files[0])
                    subprocess.Popen([exe_path], shell=True)
                else:
                    print("cru.exe dosyası bulunamadı.")
            elif tweak == "SSD Booster":
                ssd_url = "https://files1.majorgeeks.com/10afebdbffcd4742c81a3cb0f6ce4092156b4375/drives/SSDBooster.exe"
                response = requests.get(ssd_url)
                filename = ssd_url.split('/')[-1]
                temp_file_path = os.path.join(tempfile.gettempdir(), filename)
                with open(temp_file_path, 'wb') as file:
                    file.write(response.content)
                if os.path.exists(temp_file_path):
                    subprocess.Popen([temp_file_path], shell=True)
            elif tweak == "AppCopier":
                copier_url = "https://github.com/builtbybel/Appcopier/releases/download/0.30.0/appcopier_setup.msi"
                response = requests.get(copier_url)
                filename = copier_url.split('/')[-1]
                temp_file_path = os.path.join(tempfile.gettempdir(), filename)
                with open(temp_file_path, 'wb') as file:
                    file.write(response.content)
                if os.path.exists(temp_file_path):
                    subprocess.Popen([temp_file_path], shell=True)
            elif tweak == "Optimizer":
                optimizer_url = "https://github.com/hellzerg/optimizer/releases/download/16.4/Optimizer-16.4.exe"
                response = requests.get(optimizer_url)
                temp_folder = tempfile.mkdtemp()
                filename = os.path.basename(optimizer_url)
                file_path = os.path.join(temp_folder, filename)
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                if os.path.exists(file_path):
                    subprocess.Popen([file_path], shell=True)
            elif tweak == "Msi Utility V3":
                util_path = os.path.join(tweakler_dir, "msiutil.exe")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", util_path, None, None, 1)
            elif tweak == "Chocolatey":
                subprocess.run(["powershell", "-Command", "Set-ExecutionPolicy", "Bypass", "-Scope", "Process",
                                "-Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"])
                self.log_text.append("Chocolatey tweak uygulandı")
            elif tweak == "BloatyNosy":
                bloatnosy_url = "https://github.com/builtbybel/Bloatynosy/releases/download/1.4.0/BloatynosyApp.zip"
                response = requests.get(bloatnosy_url)
                temp_folder = tempfile.mkdtemp()
                zip_file_path = os.path.join(temp_folder, "BloatynosyApp.zip")
                with open (zip_file_path, "wb") as file:
                    file.write(response.content)
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)
                exe_files = [f for f in os.listdir(temp_folder) if f.endswith(".exe")]
                if exe_files:
                    exe_path = os.path.join(temp_folder, exe_files[0])
                    subprocess.Popen([exe_path], shell=True)
                else:
                    print("BloatyNosy.exe dosyası bulunamadı.")
            elif tweak == "DNS Jumper":
                dns_jumper_url = "https://www.sordum.org/files/download/dns-jumper/DnsJumper.zip"
                response = requests.get(dns_jumper_url)
                temp_folder =tempfile.mkdtemp()
                zip_file_path = os.path.join(temp_folder, "DnsJumper.zip")
                with open(zip_file_path, 'wb') as file:
                    file.write(response.content)
                with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_folder)
                inner_folder = os.path.join(temp_folder, os.listdir(temp_folder)[0])
                exe_files = [f for f in os.listdir(inner_folder) if f.endswith(".exe")]
                if exe_files:
                    exe_path = os.path.join(inner_folder, exe_files[0])
                    subprocess.Popen([exe_path], shell=True)
                else:
                    print("DnsJumper.exe dosyası bulunamadı.")
            elif tweak == "Linus Titus Uzman Ayarlari":
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command",
                                "Invoke-WebRequest -Uri 'https://christitus.com/win' | Invoke-Expression"])
                self.log_text.append("Linus Titus Uzman Ayarlari tweak uygulandı")
            elif tweak == "Sağ Tık Güç Seceneklerini Ayarlama Özelliği Ekleme":
                registry_path = os.path.join(tweakler_dir, "sagtikguc.reg")
                os.startfile(registry_path)
                self.log_text.append("Sağ Tık Güç Seceneklerini Ayarlama Özelliği Ekleme tweak'i uygulandı")
            elif tweak == "Sağ Tık Güç Seceneklerini Ayarlama Özelliği İptali":
                registry_cancel_path = os.path.join(tweakler_dir, "sagtikguciptal.reg")
                os.startfile(registry_cancel_path)
                self.log_text.append("Sağ Tık Güç Seceneklerini Ayarlama Özelliği İptali tweak'i uygulandı")
            elif tweak == "Güç Seçeneklerine CPU Frekansı Ayarı Getirme/Kaldırma":
                frequency_path = os.path.join(tweakler_dir, "cpufrekansaktifdeaktif.vbe")
                os.startfile(frequency_path)
                self.log_text.append("Güç Seçeneklerine CPU Frekansı Ayarı Getirme/Kaldırma tweak'i uygulandı")
            elif tweak == "InsPolicyx64":
                policy_url = "https://de1-dl.techpowerup.com/files/glDrCh3RQJ1R7oNdRe59vw/1704503396/Interrupt_Affinity_Policy_Tool.zip"
                temp_file_path = os.path.join(tempfile.gettempdir(), "Interrupt_Affinity_Policy_Tool.zip")
                response = requests.get(policy_url)
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                extracted_path =None
                zip_file.extractall(temp_file_path)
                for file in zip_file.namelist():
                    if "intPolicy_x64.exe" in file:
                        extracted_path = os.path.join(temp_file_path, file)
                        break
                if extracted_path:
                    subprocess.Popen([extracted_path], shell=True)
            elif tweak == "WingetUI Installer (Başlaması için 2dk kadar bekleyin!)":
                program_name = "SomePythonThings.WingetUIStore"
                subprocess.run(["winget", "install", program_name])
            elif tweak == "SDIO Driver":
                sdio_url = "https://www.glenn.delahoy.com/downloads/sdio/SDIO_1.12.18.759.zip"
                temp_file_path = os.path.join(tempfile.gettempdir(), "SDIO_1.12.18.759.zip")
                response = requests.get(sdio_url)
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                extracted_path =None
                zip_file.extractall(temp_file_path)
                for file in zip_file.namelist():
                    if "SDIO_x64_R759.exe" in file:
                        extracted_path = os.path.join(temp_file_path, file)
                        break  # İlgili dosya bulunduğunda döngüyü sonlandır
    
                if extracted_path:
                    subprocess.Popen([extracted_path], shell=True)
                
                
                QMessageBox.information(self, "Tweakler Uygulandı", "Seçilen tweakler uygulandı!")

                self.update_available = False  # Güncelleme kontrolü için bir bayrak

    def add_updates_tab(self, tab):
        layout = QVBoxLayout()

        check_updates_button = QPushButton("Güncelleştirmeleri Denetle")
        check_updates_button.clicked.connect(self.check_updates)
        layout.addWidget(check_updates_button)

        self.update_label = QLabel("")  # Güncelleme çıktısını göstereceğimiz etiket
        self.update_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(self.update_label)

        self.apply_updates_button = QPushButton("Güncelleştirmeleri Uygula")
        self.apply_updates_button.clicked.connect(self.apply_updates)
        self.apply_updates_button.setEnabled(False)  # Başlangıçta devre dışı bırakıldı
        layout.addWidget(self.apply_updates_button, alignment=Qt.AlignRight)

        tab.setLayout(layout)

    def check_updates(self):
        result = subprocess.run(["winget", "upgrade"], capture_output=True, text=True)
        output = result.stdout

        self.update_output = output
        
        cleaned_output = output.replace('-', '').replace('\\', '').replace('|', '').replace('/', '')
        self.update_label.setText(cleaned_output)
        # Eğer güncelleme varsa, güncelleme butonunu etkinleştir
        if "No updates found" not in output:
            self.update_available = True
            self.apply_updates_button.setEnabled(True)

    def apply_updates(self):
        if self.update_available:
            subprocess.run(["winget", "upgrade", "--all"])
            self.update_label.setText("Güncellemeler uygulandı!")
            self.update_available = False  # Güncelleme uygulandıktan sonra bayrağı sıfırla
            self.apply_updates_button.setEnabled(False)  # Butonu tekrar devre dışı bırak

            # Kullanıcıya güncellemelerin tamamlandığını bildiren bir ileti kutusu göster
            QMessageBox.information(self, "Güncelleme Tamamlandı", "Güncelleştirmeler başarıyla tamamlandı!")

    def get_installed_programs(self):
        installed_programs = []
        uninstall_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"

        # HKEY_LOCAL_MACHINE altındaki programlar



    def listeyi_guncelle(self):
        self.program_list.clear()

        installed_programs = self.get_installed_programs()
        self.program_list.addItems(installed_programs)

    def add_uninstall_tab(self, tab):
        layout = QVBoxLayout()

        self.program_list = QListWidget()  # Yüklü programları listelemek için QListWidget kullanıyoruz
        self.populate_program_list()  # Yüklü programları listelemek için fonksiyonu çağırıyoruz
        layout.addWidget(self.program_list)

        remove_button = QPushButton("Seçilen Programı Kaldır")
        remove_button.clicked.connect(self.remove_selected_program)
        layout.addWidget(remove_button)

        update_list_button = QPushButton("Listeyi Güncelle")
        update_list_button.clicked.connect(self.listeyi_guncelle)
        layout.addWidget(update_list_button)

        tab.setLayout(layout)

    def populate_program_list(self):
        installed_programs = self.get_installed_programs()
        self.program_list.addItems(installed_programs)

    def remove_selected_program(self):
        selected_program = self.program_list.currentItem().text()
        confirm = QMessageBox.question(
            self, "Programı Kaldır", f"{selected_program} programını kaldırmak istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No)

        if confirm == QMessageBox.Yes:
            try:
                result = subprocess.run(["winget", "uninstall", selected_program, "--force"], capture_output=True,
                                        text=True)
                if result.returncode == 0:
                    QMessageBox.information(
                        self, "Başarılı", f"{selected_program} başarıyla kaldırıldı.")
                    self.listeyi_guncelle()  # Kaldırıldıktan sonra program listesini yenile
                else:
                    QMessageBox.critical(
                        self, "Hata", f"{selected_program} kaldırılamadı.")
            except Exception as e:
                QMessageBox.critical(
                    self, "Hata", f"Program kaldırma sırasında bir hata oluştu: {str(e)}")
        else:
            QMessageBox.information(
                self, "İşlem İptal Edildi", "Program kaldırma işlemi iptal edildi.")

    def add_about_tab(self, tab):
        layout = QVBoxLayout()
        about_label = self._extracted_from_add_about_tab_3(
            "Program Yöneticisi, kullanıcıların kolayca programları yönetmelerine olanak tanıyan bir araçtır."
            "Bu arayüz, program kurulumunu, tweak uygulamayı, güncellemeleri yapmayı ve programları kaldırmayı kolaylaştırır. Katkıları için forum.yazbel.com Asif'e teşekkürler.",
            layout,
        )
        about_label.setWordWrap(True)
        
        contact_label = self._extracted_from_add_about_tab_3(
            "İletişim ve Öneriler\n\n"
            "Herhangi bir geri bildiriminiz, öneriniz veya sorunuz varsa lütfen bize ulaşın.\n"
            "E-posta: kemal.saydut@gmail.com\n\n"
            "Programı geliştirmemize yardımcı olacak tüm geri bildirimleri bekliyoruz. Teşekkür ederiz!",
            layout,
        )
        tab.setLayout(layout)
        
        
        self.version_label = self._extracted_from_add_about_tab_3(
        "Program Versiyonu: 10.5.1", layout
        )
        self.version_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        
        version_check_button = QPushButton("Program Sürüm Kontrolü")
        version_check_button.clicked.connect(lambda: self.prog_ver_check(self.version_label))
        layout.addWidget(version_check_button)

        tab.setLayout(layout)


    def _extracted_from_add_about_tab_3(self, arg0, layout):
        about_text = arg0
        result = QLabel(about_text)
        layout.addWidget(result)
        return result
    


    def find_uninstaller(self):
        program_directory = os.path.dirname(sys.argv[0])
        uninstallers = [f for f in os.listdir(program_directory) if f.startswith("unins") and f.endswith('.exe')]
        print(uninstallers, program_directory)
        if uninstallers:
            return os.path.join(program_directory, uninstallers[0])
        return None

    def create_uninstall_script(self, current_exe_path, python_executable):
        uninstall_script_content = f'@echo off\n'
        uninstall_script_content += f'rem Uninstall script generated by YourClass\n'

        # Find the uninstaller
        uninstaller_path = self.find_uninstaller()
        if uninstaller_path:
            uninstall_script_content += f'"{uninstaller_path}" /S\n'  # Sessiz kaldırma işlemi
            print(f"Uninstaller path added to uninstall script: {uninstaller_path}")
        else:
            print("Uninstaller not found.")

        # Call the update function after uninstaller
        uninstall_script_content += f'call :run_update_script\n'
        uninstall_script_content += f'exit\n'
        uninstall_script_content += f':run_update_script\n'
        uninstall_script_content += f'call "{self.create_update_script(current_exe_path, python_executable)}"\n'

        uninstall_script_path = os.path.join(tempfile.gettempdir(), "uninstall_script.bat")
        with open(uninstall_script_path, 'w') as uninstall_script_file:
            uninstall_script_file.write(uninstall_script_content)

        # Run the uninstall script
        subprocess.run([uninstall_script_path], shell=True, check=True)
        
        #program kendini kapatır
        print("program kapatılıyor...")
        sys.exit()
        

    def create_update_script(self, temp_exe_path, python_executable):
        update_script_content = f'@echo off\n'
        update_script_content += f'start "" "{temp_exe_path}"\n'  # Yeni sürümü başlat
        update_script_content += f'exit\n'

        update_script_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
        with open(update_script_path, 'w') as update_script_file:
            update_script_file.write(update_script_content)

        return update_script_path

    def run_update_script(self, bat_path_uninstall, bat_path_update):
        try:
            subprocess.run([bat_path_uninstall], shell=True)
            subprocess.run([bat_path_update], shell=True)
            return True
        except Exception as e:
            print(f"Hata: {e}")
            return False

    def download_update(self, url, dest_path):
        try:
            response = requests.get(url, stream=True)
            with open(dest_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
        except Exception as e:
            print(f"Hata: {e}")

    def extract_zip(self, zip_path, extract_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        return extract_path

    def get_single_exe_in_directory(self, directory):
        exe_files = [f for f in os.listdir(directory) if f.endswith('.exe')]
        if len(exe_files) == 1:
            return os.path.join(directory, exe_files[0])
        else:
            raise ValueError("Dizinde tek bir exe dosyası olmalı.")

    def extract_release_notes(self, version_txt_content):
        release_notes = []
        lines = version_txt_content.split('\n')
    
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith('*'):
                release_notes.append(stripped_line.lstrip('*').strip())
    
        return '\n'.join(release_notes) if release_notes else "Yenilik notları bulunamadı."


    def prog_ver_check(self, version_label):
        gitlab_url = "https://gitlab.com/saydut/program-and-tweak-manager/-/raw/main/version.txt?ref_type=heads"

        local_version = version_label.text().split(":")[-1].strip()

        try:
            response = requests.get(gitlab_url)
            remote_version_info = response.text.strip().split('\n')
            remote_version = remote_version_info[0]
            release_notes_start = response.text.find('*')
            release_notes = response.text[release_notes_start:].split('link=')[0].strip()
            update_link_start = response.text.find('link=')
            update_link = response.text[update_link_start + 5:].strip()

            if remote_version > local_version:
                notes_response = requests.get(gitlab_url)
                release_notes = self.extract_release_notes(notes_response.text)

                dialog = CustomDialog(
                    f"Yeni Sürüm ({remote_version})", 
                    "Yeni bir sürüm mevcut!\n"
                    "Güncelleme işlemi:\n"
                    "Eski sürümün kaldırılması ve ardından yeni sürümün kurulması adımlarını içerir.\n "
                    "Bu işlem sırasında mevcut ayarlarınız ve verileriniz etkilenmeyecektir.\n"
                    "Devam etmek istiyor musunuz?\n\n", 
                    release_notes
                    )




                if dialog.exec_() == QDialog.Accepted:
                    print("Güncelleme işlemleri burada başlayacak.")
                    temp_zip_path_update = os.path.join(tempfile.gettempdir(), "temp_update.zip")
                    temp_exe_path_update = os.path.join(tempfile.gettempdir(), "temp_update.exe")

                    self.download_update(update_link, temp_zip_path_update)
                    extracted_path_uninstall = self.extract_zip(temp_zip_path_update, tempfile.gettempdir())
                    exe_path_uninstall = self.get_single_exe_in_directory(extracted_path_uninstall)

                    bat_path_uninstall = self.create_uninstall_script(exe_path_uninstall, sys.executable)

                    # Burada uninstall scriptini çalıştırın
                    subprocess.run([bat_path_uninstall], shell=True)

                    self.download_update(update_link, temp_zip_path_update)
                    extracted_path_update = self.extract_zip(temp_zip_path_update, tempfile.gettempdir())
                    exe_path_update = self.get_single_exe_in_directory(extracted_path_update)

                    bat_path_update = self.create_update_script(exe_path_update, sys.executable)

                    # Burada update scriptini çalıştırın
                    self.run_update_script(bat_path_uninstall, bat_path_update)
            else:
                dialog = CustomDialog2("Program Sürüm Kontrolü", "Program zaten güncel")
                dialog.show_dialog()
        except requests.RequestException as e:
            print(f"Hata: {e}")

    def run_subprocess(self, command, log_output=True):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if log_output:
                output = result.stdout
                self.log_text.append(output)
                self.log_text.repaint()
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return None
    
    def add_system_info_tab(self, tab):
        layout = QVBoxLayout()

        system_info_label = QLabel("Sistem Bilgileri:")
        layout.addWidget(system_info_label)

        # Sistem bilgilerini göstermek için bir QTextEdit bileşeni
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)  # Kullanıcı tarafından düzenlenemez yapıyor
        layout.addWidget(self.system_info_text)

        refresh_button = QPushButton("Bilgileri Yenile")
        refresh_button.clicked.connect(self.refresh_system_info)
        layout.addWidget(refresh_button)

        tab.setLayout(layout)
        self.refresh_system_info()

    def add_gpu_info_to_system_tab(self, tab):
        layout = tab.layout()  # var olan layoutu alıyoruz
        try:
            gpu_info_text = QTextEdit()
            gpu_info_text.setReadOnly(True)
            gpu_info_text.setPlainText(self.get_gpu_info())  # gpu bilgisi ekleme
            layout.addWidget(gpu_info_text)

        except Exception as e:
            print(f"Hata: {str(e)}")

    def get_gpu_info(self):
        try:
            platforms = cl.get_platforms()
            devices = [platform.get_devices(device_type=cl.device_type.GPU) for platform in platforms]

            gpu_info = []
            for idx, platform in enumerate(platforms):
                gpu_info.append(f"Platform {idx + 1}: {platform.name}")
                for device in devices[idx]:
                    gpu_info.extend(
                        (
                            f"Device Name: {device.name}",
                            f"Device Version: {device.version}",
                            f"Device Type: {cl.device_type.to_string(device.type)}",
                            f"Device Global Memory: {device.global_mem_size // 1024 ** 3} GB",
                            f"Device Local Memory: {device.local_mem_size // 1024} KB",
                            f"Device Max Clock Frequency: {device.max_clock_frequency} MHz",
                            "-" * 30,
                        )
                    )
            return "\n".join(gpu_info)
        except ImportError:
            return "PyOpenCL kütüphanesi bulunamadı. Lütfen yükleyin."
        except Exception as e:
            return f"Hata: {str(e)}"

    def refresh_system_info(self):

        freeze_support()

        cpu_info += f"Işlemci Sayısı: {psutil.cpu_count(logical=False)}\n"
        cpu_info += f"İş Parçacığı Sayısı: {psutil.cpu_count(logical=True)}\n\n"

        mem_info = psutil.virtual_memory()
        mem_total = round(mem_info.total / (1024 ** 3), 2)
        mem_available = round(mem_info.available / (1024 ** 3), 2)
        mem_percent = mem_info.percent
        mem_info_str = f"Bellek: {mem_available} GB / {mem_total} GB kullanıldı ({mem_percent}%)\n\n"

        os_info = f"İşletim Sistemi: {platform.uname().system} {platform.uname().release}\n\n"

        disk_usage = psutil.disk_usage('/')
        disk_info = f"Toplam Depolama: {disk_usage.total / (1024 ** 3):.2f} GB\n"
        disk_info += f"Kullanılan Alan: {disk_usage.used / (1024 ** 3):.2f} GB\n"
        disk_info += f"Boş Alan: {disk_usage.free / (1024 ** 3):.2f} GB\n\n"

        network_info = psutil.net_if_addrs()
        network_str = "Ağ Bağlantıları:\n"
        for interface, addrs in network_info.items():
            network_str += f"Interface: {interface}\n"
            for addr in addrs:
                if hasattr(addr, 'family') and addr.family == getattr(psutil, 'AF_INET', None):
                    network_str += f"IP Adresi: {addr.address}\n"
                    network_str += f"Alt Ağ Maskesi: {addr.netmask}\n"
        network_str += "\n"

        gpu_info = self.get_gpu_info()
        system_info = cpu_info + mem_info_str + os_info + disk_info + network_str + gpu_info
        self.system_info_text.setText(system_info)



    def create_menu(self):
        main_menu = self.menuBar()
        view_menu = main_menu.addMenu('Temalar')

        dark_theme_action = QAction('Karanlık Tema', self)
        dark_theme_action.setStatusTip('Karanlık Tema Uygula')
        dark_theme_action.triggered.connect(self.apply_dark_theme)
        view_menu.addAction(dark_theme_action)

        light_theme_action = QAction('Açık Tema', self)
        light_theme_action.setStatusTip('Açık Tema Uygula')
        light_theme_action.triggered.connect(self.apply_light_theme)
        view_menu.addAction(light_theme_action)
        
        

    def apply_dark_theme(self):
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    def apply_light_theme(self):
        self.setStyleSheet('')
        

    def apply_windows_theme(self):
        # Windows temasını kontrol et
        is_dark_mode = self.is_dark_mode()
        if is_dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()

    def is_dark_mode(self):
        # Windows Registry üzerinden tema kontrolü
        try:
            registry_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            value_name = 'AppsUseLightTheme'
            key = ctypes.c_void_p()

            result = ctypes.windll.advapi32.RegOpenKeyExW(
                ctypes.c_uint32(0x80000001),  # HKEY_CURRENT_USER
                ctypes.c_wchar_p(registry_path),
                0,
                0x20019,  # KEY_READ | KEY_WOW64_64KEY
                ctypes.byref(key)
            )

            if result != 0:
                raise Exception("Error opening registry key")

            value = ctypes.c_uint32()
            value_size = ctypes.c_uint32(ctypes.sizeof(value))
            result = ctypes.windll.advapi32.RegQueryValueExW(
                key,
                ctypes.c_wchar_p(value_name),
                None,
                None,
                ctypes.byref(value),
                ctypes.byref(value_size)
            )

            ctypes.windll.advapi32.RegCloseKey(key)

            if result == 0:
                return value.value == 0
            else:
                raise Exception("Error querying registry value")

        except Exception as e:
            print(f"Error detecting theme: {e}")
            return False

    def is_light_mode(self):
        # Windows açık tema kontrolü
        try:
            registry_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            value_name = 'AppsUseLightTheme'
            key = ctypes.c_void_p()

            result = ctypes.windll.advapi32.RegOpenKeyExW(
                ctypes.c_uint32(0x80000001),  # HKEY_CURRENT_USER
                ctypes.c_wchar_p(registry_path),
                0,
                0x20019,  # KEY_READ | KEY_WOW64_64KEY
                ctypes.byref(key)
            )

            if result != 0:
                raise Exception("Error opening registry key")

            value = ctypes.c_uint32()
            value_size = ctypes.c_uint32(ctypes.sizeof(value))
            result = ctypes.windll.advapi32.RegQueryValueExW(
                key,
                ctypes.c_wchar_p(value_name),
                None,
                None,
                ctypes.byref(value),
                ctypes.byref(value_size)
            )

            ctypes.windll.advapi32.RegCloseKey(key)

            if result == 0:
                return value.value == 1
            else:
                raise Exception("Error querying registry value")

        except Exception as e:
            print(f"Error detecting theme: {e}")
            return False

def run_app():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        
    console_window = ctypes.windll.kernel32.GetConsoleWindow()
    if console_window != 0:
        ctypes.windll.user32.ShowWindow(console_window, 1) #1 ve 0 konsol görünürlüğü
        
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.lastWindowClosed.connect(app.quit)  # Uygulama kapatılığında sonlandırma işlevi.
    (app.exec_())


if __name__ == "__main__":
    freeze_support()
    app = QApplication(sys.argv)
    
    #kontroller
    current_version = updated_version = check_and_update_winget()
    if current_version:
        print("Winget sürümü:", current_version)
        if updated_version:
            print("Güncellenmiş sürüm:", updated_version)
    
    main_window = MainWindow()  # Ana pencereyi oluştur
    main_window.show()  # Ana pencereyi göster
    # The above code is exiting the program and starting the event loop.
    sys.exit(app.exec_())  # Event loop'u başlat