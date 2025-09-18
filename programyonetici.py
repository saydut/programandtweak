import sys
import subprocess
import tempfile
import zipfile
import io
import os
import ctypes
import psutil
import platform
import requests
import json
import winreg
import wmi
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget,
                             QVBoxLayout, QLabel, QCheckBox, QPushButton,
                             QScrollArea, QTextEdit, QMessageBox, QAction,
                             QDialog, QLineEdit, QHBoxLayout, QListWidget, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import qdarkstyle

# --- Global Değişkenler ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TWEAKLER_DIR = os.path.join(BASE_DIR, "Tweakler Kurcalama")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# --- Arka Plan İşlemcisi (Worker) Sınıfları ---

class Worker(QThread):
    """Genel amaçlı, fonksiyonları arka planda çalıştıran thread."""
    finished = pyqtSignal(object)
    progress = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(self.progress.emit, *self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.progress.emit(f"Hata: {e}")
            self.finished.emit(None)

class SubprocessWorker(QThread):
    """Subprocess komutlarını arka planda çalıştıran ve çıktıyı canlı olarak yayınlayan thread."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        self.progress.emit(f"Komut çalıştırılıyor: {self.command}")
        try:
            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                self.progress.emit(line.strip())
            process.wait()
            self.finished.emit(process.returncode)
        except Exception as e:
            self.progress.emit(f"Komut çalıştırılırken hata oluştu: {e}")
            self.finished.emit(-1)

# --- Özel Dialog Pencereleri ---

class CustomDialog(QDialog):
    """Yenilik notlarını ve onay butonlarını içeren özel dialog."""
    def __init__(self, title, message, notes):
        super().__init__()
        self.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))
        notes_text_edit = QTextEdit()
        notes_text_edit.setPlainText(notes)
        notes_text_edit.setReadOnly(True)
        layout.addWidget(notes_text_edit)
        button_layout = QHBoxLayout()
        yes_button = QPushButton("Evet")
        yes_button.clicked.connect(self.accept)
        no_button = QPushButton("Hayır")
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(yes_button)
        button_layout.addWidget(no_button)
        layout.addLayout(button_layout)
        self.setLayout(layout)

class CustomDialog2(QDialog):
    """Sadece 'Tamam' butonu içeren basit bilgilendirme dialogu."""
    def __init__(self, title, message):
        super(CustomDialog2, self).__init__()
        self.setWindowTitle(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(message))
        ok_button = QPushButton("Tamam")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)
        self.setLayout(layout)

# --- Ana Pencere ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.worker = None

        self.setWindowTitle("Program Yöneticisi")
        self.setGeometry(100, 100, 800, 650)

        self.create_menu()
        self.init_ui()
        self.apply_windows_theme()
        self.check_and_update_winget()

    def init_ui(self):
        """Arayüzü ve sekmeleri oluşturan ana fonksiyon."""
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        tabs = {
            "Programlar": self.add_programs_tab,
            "Chocolatey": self.add_choco_tab,
            "Tweakler": self.add_tweaks_tab,
            "Güncelleştirmeler": self.add_updates_tab,
            "Program Kaldırma": self.add_uninstall_tab,
            "Sistem Bilgileri": self.add_system_info_tab,
            "İşlem Kaydı": self.add_log_tab,
            "Hakkında": self.add_about_tab,
        }
        for title, method in tabs.items():
            tab = QWidget()
            self.tab_widget.addTab(tab, title)
            method(tab)

    def load_config(self):
        """Yapılandırma dosyasını (config.json) yükler."""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            QMessageBox.critical(self, "Hata", "config.json dosyası bulunamadı veya bozuk.")
            return {}

    # --- Sekme Oluşturma Metotları ---

    def add_programs_tab(self, tab):
        """'Programlar' sekmesini oluşturur ve winget programlarını listeler."""
        self.programs_checkboxes = self.create_checkbox_list(self.config.get("programs", {}).get("winget", []))
        install_button = QPushButton("Seçilenleri Kur (Winget)")
        install_button.clicked.connect(lambda: self.install_selected("winget", self.programs_checkboxes))
        
        search_button = QPushButton("Program Ara")
        search_button.clicked.connect(self.open_program_search_window)

        button_layout = QHBoxLayout()
        button_layout.addWidget(search_button)
        button_layout.addWidget(install_button)

        layout = self.create_scrollable_layout(self.programs_checkboxes)
        layout.addLayout(button_layout)
        tab.setLayout(layout)

    def add_choco_tab(self, tab):
        """'Chocolatey' sekmesini oluşturur."""
        self.choco_checkboxes = self.create_checkbox_list(self.config.get("programs", {}).get("choco", []))
        
        install_choco_button = QPushButton("Chocolatey Kurulumunu Başlat")
        install_choco_button.clicked.connect(self.install_choco)
        
        install_programs_button = QPushButton("Seçilenleri Kur (Choco)")
        install_programs_button.clicked.connect(lambda: self.install_selected("choco", self.choco_checkboxes))

        button_layout = QHBoxLayout()
        button_layout.addWidget(install_choco_button)
        button_layout.addWidget(install_programs_button)
        
        layout = self.create_scrollable_layout(self.choco_checkboxes)
        layout.addLayout(button_layout)
        tab.setLayout(layout)
        
    def add_tweaks_tab(self, tab):
        """'Tweakler' sekmesini oluşturur."""
        self.tweaks_checkboxes = self.create_checkbox_list(self.config.get("tweaks", {}).keys())
        apply_button = QPushButton("Seçili Tweakleri Uygula")
        apply_button.clicked.connect(self.apply_tweaks)
        
        layout = self.create_scrollable_layout(self.tweaks_checkboxes)
        layout.addWidget(apply_button)
        tab.setLayout(layout)

    def add_updates_tab(self, tab):
        """'Güncelleştirmeler' sekmesini oluşturur."""
        layout = QVBoxLayout()
        self.update_list = QTextEdit()
        self.update_list.setReadOnly(True)
        
        check_button = QPushButton("Güncelleştirmeleri Denetle")
        check_button.clicked.connect(self.check_updates)
        
        self.apply_updates_button = QPushButton("Tümünü Güncelle")
        self.apply_updates_button.clicked.connect(self.apply_updates)
        self.apply_updates_button.setEnabled(False)
        
        layout.addWidget(check_button)
        layout.addWidget(self.update_list)
        layout.addWidget(self.apply_updates_button)
        tab.setLayout(layout)

    def add_uninstall_tab(self, tab):
        """'Program Kaldırma' sekmesini oluşturur."""
        layout = QVBoxLayout()
        self.program_list_widget = QListWidget()
        
        refresh_button = QPushButton("Listeyi Yenile")
        refresh_button.clicked.connect(self.populate_program_list)
        
        remove_button = QPushButton("Seçilen Programı Kaldır")
        remove_button.clicked.connect(self.remove_selected_program)

        layout.addWidget(refresh_button)
        layout.addWidget(self.program_list_widget)
        layout.addWidget(remove_button)
        tab.setLayout(layout)
        self.populate_program_list()

    def add_system_info_tab(self, tab):
        """'Sistem Bilgileri' sekmesini oluşturur."""
        layout = QVBoxLayout()
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        refresh_button = QPushButton("Bilgileri Yenile")
        refresh_button.clicked.connect(self.refresh_system_info)
        layout.addWidget(refresh_button)
        layout.addWidget(self.system_info_text)
        tab.setLayout(layout)
        self.refresh_system_info()

    def add_log_tab(self, tab):
        """'İşlem Kaydı' sekmesini oluşturur."""
        layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(QLabel("Arka plan işlemlerinin çıktısı:"))
        layout.addWidget(self.log_text)
        layout.addWidget(self.progress_bar)
        tab.setLayout(layout)

    def add_about_tab(self, tab):
        """'Hakkında' sekmesini oluşturur."""
        layout = QVBoxLayout()
        about_text = ("Program Yöneticisi, kullanıcıların kolayca programları yönetmelerine olanak tanıyan bir araçtır."
                      "Bu arayüz, program kurulumunu, tweak uygulamayı, güncellemeleri yapmayı ve programları kaldırmayı kolaylaştırır.\n\n"
                      "İletişim ve Öneriler: kemal.saydut@gmail.com")
        layout.addWidget(QLabel(about_text))
        
        self.version_label = QLabel("Program Versiyonu: 10.5.1")
        version_check_button = QPushButton("Güncellemeleri Kontrol Et")
        version_check_button.clicked.connect(self.prog_ver_check)
        
        layout.addStretch()
        layout.addWidget(self.version_label)
        layout.addWidget(version_check_button)
        tab.setLayout(layout)

    # --- Yardımcı Arayüz Metotları ---

    def create_checkbox_list(self, items):
        """Verilen listeden bir QCheckBox listesi oluşturur."""
        checkboxes = []
        for item in items:
            name = item.get("name") if isinstance(item, dict) else item
            checkboxes.append(QCheckBox(name))
        return checkboxes

    def create_scrollable_layout(self, widgets):
        """Widget listesini kaydırılabilir bir alana yerleştirir."""
        layout = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        for widget in widgets:
            scroll_layout.addWidget(widget)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        return layout
    
    # --- Arka Plan İşlem Metotları (Worker'ları başlatanlar) ---

    def install_selected(self, installer_type, checkboxes):
        """Seçili programları arka planda kurar."""
        selected_items = [cb.text() for cb in checkboxes if cb.isChecked()]
        if not selected_items:
            return

        self.tab_widget.setCurrentWidget(self.log_text.parentWidget())
        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected_items))
        self.progress_bar.setValue(0)

        # Config'den tam program bilgilerini al
        if installer_type == "winget":
            program_list = self.config.get("programs", {}).get("winget", [])
        else:
            program_list = self.config.get("programs", {}).get("choco", [])
            
        commands = []
        for name in selected_items:
            for prog_info in program_list:
                if prog_info["name"] == name:
                    if installer_type == "winget":
                        commands.append(f"winget install --id {prog_info['id']} --source winget --accept-source-agreements --accept-package-agreements")
                    else: # choco
                        commands.append(f"choco install {prog_info['id']} -y")
                    break
        
        self.worker = Worker(self.run_commands_sequentially, commands)
        self.worker.progress.connect(self.log_text.append)
        self.worker.finished.connect(self.on_installation_finished)
        self.worker.start()

    def run_commands_sequentially(self, progress_callback, commands):
        """Komut listesini sırayla çalıştırır."""
        for i, cmd in enumerate(commands):
            progress_callback(f"\n--- {i+1}/{len(commands)}: {cmd.split()[2]} kuruluyor ---\n")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in iter(process.stdout.readline, ''):
                progress_callback(line.strip())
            process.wait()
            self.progress_bar.setValue(i + 1)
        return "Tüm kurulumlar tamamlandı."

    def apply_tweaks(self):
        """Seçili tweak'leri uygular."""
        selected_tweaks = [cb.text() for cb in self.tweaks_checkboxes if cb.isChecked()]
        if not selected_tweaks:
            return

        self.tab_widget.setCurrentWidget(self.log_text.parentWidget())
        self.log_text.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected_tweaks))
        
        self.worker = Worker(self.run_tweaks_sequentially, selected_tweaks)
        self.worker.progress.connect(self.log_text.append)
        self.worker.finished.connect(self.on_installation_finished)
        self.worker.start()

    def run_tweaks_sequentially(self, progress_callback, tweak_names):
        """Tweak'leri sırayla çalıştırır."""
        for i, name in enumerate(tweak_names):
            progress_callback(f"\n--- {name} uygulanıyor... ---\n")
            tweak_info = self.config["tweaks"][name]
            t_type = tweak_info.get("type")

            if t_type == "powershell_web":
                subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", tweak_info["command"]], check=True)
            elif t_type == "local_file":
                os.startfile(os.path.join(TWEAKLER_DIR, tweak_info["path"]))
            elif t_type == "local_admin":
                ctypes.windll.shell32.ShellExecuteW(None, "runas", os.path.join(TWEAKLER_DIR, tweak_info["path"]), None, None, 1)
            elif t_type == "winget":
                 subprocess.run(["winget", "install", "--id", tweak_info["id"]], check=True)
            elif t_type in ["download_and_run", "download_zip_and_run"]:
                self.download_and_run(progress_callback, tweak_info)
            
            self.progress_bar.setValue(i + 1)
            progress_callback(f"--- {name} tamamlandı. ---\n")
        return "Tüm tweak işlemleri tamamlandı."
        
    def download_and_run(self, progress_callback, tweak_info):
        """Bir dosyayı indirir, gerekirse zipten çıkarır ve çalıştırır."""
        try:
            url = tweak_info["url"]
            filename = os.path.basename(url)
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)

            progress_callback(f"{filename} indiriliyor...")
            response = requests.get(url, stream=True)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if tweak_info["type"] == "download_zip_and_run":
                progress_callback(f"{filename} zipten çıkarılıyor...")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                exe_path = os.path.join(temp_dir, tweak_info["exe_name"])
                # Bazen dosyalar bir alt klasöre çıkar
                if not os.path.exists(exe_path):
                     for root, _, files in os.walk(temp_dir):
                         if tweak_info["exe_name"] in files:
                             exe_path = os.path.join(root, tweak_info["exe_name"])
                             break

                progress_callback(f"{tweak_info['exe_name']} çalıştırılıyor...")
                subprocess.Popen([exe_path], shell=True)
            else: # download_and_run
                progress_callback(f"{filename} çalıştırılıyor...")
                os.startfile(file_path)

        except Exception as e:
            progress_callback(f"Tweak uygulanırken hata: {e}")

    def on_installation_finished(self, result):
        """Kurulum/Tweak işlemleri bittiğinde çağrılır."""
        self.progress_bar.setVisible(False)
        self.log_text.append(f"\nİşlem Sonucu: {result}")
        QMessageBox.information(self, "Tamamlandı", str(result))

    def check_updates(self):
        """Winget güncellemelerini arka planda kontrol eder."""
        self.update_list.setText("Güncellemeler kontrol ediliyor, lütfen bekleyin...")
        self.worker = SubprocessWorker("winget upgrade")
        self.worker.progress.connect(self.update_list.append)
        self.worker.finished.connect(self.on_check_updates_finished)
        self.worker.start()

    def on_check_updates_finished(self, returncode):
        """Güncelleme kontrolü bittiğinde çağrılır."""
        if "No applicable update found" not in self.update_list.toPlainText():
            self.apply_updates_button.setEnabled(True)
            self.log_text.append("Uygulanacak güncellemeler bulundu.")
        else:
            self.apply_updates_button.setEnabled(False)
            self.log_text.append("Sisteminiz güncel.")

    def apply_updates(self):
        """Tüm güncellemeleri uygular."""
        self.worker = SubprocessWorker("winget upgrade --all --accept-package-agreements --accept-source-agreements")
        self.worker.progress.connect(self.log_text.append)
        self.worker.finished.connect(lambda: QMessageBox.information(self, "Tamamlandı", "Güncelleme işlemi bitti."))
        self.worker.start()

    def populate_program_list(self):
        """Program kaldırma listesini doldurur."""
        self.program_list_widget.clear()
        self.program_list_widget.addItems(["Yüklü programlar listeleniyor..."])
        self.worker = Worker(self.get_installed_programs)
        self.worker.finished.connect(self.on_populate_program_list_finished)
        self.worker.start()

    def on_populate_program_list_finished(self, programs):
        """Program listesi alındığında çağrılır."""
        self.program_list_widget.clear()
        if programs:
            self.program_list_widget.addItems(programs)
        else:
            self.program_list_widget.addItem("Yüklü program bulunamadı veya listelenemedi.")

    def remove_selected_program(self):
        """Seçilen programı kaldırır."""
        selected_item = self.program_list_widget.currentItem()
        if not selected_item:
            return
        
        program_name = selected_item.text()
        reply = QMessageBox.question(self, 'Onay', f'"{program_name}" programını kaldırmak istediğinizden emin misiniz?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.worker = SubprocessWorker(f'winget uninstall --name "{program_name}" --accept-source-agreements')
            self.worker.progress.connect(self.log_text.append)
            self.worker.finished.connect(lambda: self.populate_program_list())
            self.worker.start()

    # --- Diğer Fonksiyonlar ---
    
    def get_installed_programs(self, progress_callback=None):
        """Windows kayıt defterinden yüklü programları listeler."""
        programs = set()
        uninstall_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]

        for hive in hives:
            for path in uninstall_paths:
                try:
                    key = winreg.OpenKey(hive, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        skey_name = winreg.EnumKey(key, i)
                        try:
                            skey = winreg.OpenKey(key, skey_name)
                            try:
                                display_name = winreg.QueryValueEx(skey, 'DisplayName')[0]
                                if display_name and len(display_name) > 1:
                                    programs.add(display_name.strip())
                            except OSError:
                                continue
                            finally:
                                winreg.CloseKey(skey)
                        except OSError:
                            continue
                except OSError:
                    continue
        return sorted(list(programs))

    def refresh_system_info(self):
        """Sistem bilgilerini toplar ve gösterir."""
        try:
            cpu_info = f"İşlemci: {platform.processor()}\n"
            cpu_info += f"Çekirdek Sayısı: {psutil.cpu_count(logical=False)}\n"
            cpu_info += f"İş Parçacığı Sayısı: {psutil.cpu_count(logical=True)}\n\n"

            mem_info = psutil.virtual_memory()
            mem_total = round(mem_info.total / (1024 ** 3), 2)
            mem_available = round(mem_info.available / (1024 ** 3), 2)
            mem_info_str = f"Bellek: {mem_available} GB / {mem_total} GB ({mem_info.percent}%)\n\n"

            os_info = f"İşletim Sistemi: {platform.uname().system} {platform.uname().release}\n\n"

            gpu_info = self.get_gpu_info()
            
            system_info_text = cpu_info + mem_info_str + os_info + gpu_info
            self.system_info_text.setText(system_info_text)
        except Exception as e:
            self.system_info_text.setText(f"Sistem bilgileri alınırken bir hata oluştu: {e}")

    def get_gpu_info(self):
        """WMI kullanarak GPU bilgilerini alır."""
        try:
            c = wmi.WMI()
            gpu_info_list = []
            for gpu in c.Win32_VideoController():
                gpu_info_list.append(f"GPU Adı: {gpu.Name}")
                gpu_info_list.append(f"Sürücü Versiyonu: {gpu.DriverVersion}")
                if gpu.AdapterRAM:
                    ram_gb = int(gpu.AdapterRAM) / (1024**3)
                    gpu_info_list.append(f"Adaptör RAM: {ram_gb:.2f} GB")
                gpu_info_list.append("-" * 30)
            return "\n".join(gpu_info_list) if gpu_info_list else "GPU bilgisi bulunamadı."
        except Exception:
            return "WMI kütüphanesi bulunamadı veya GPU bilgisi alınamadı."

    def check_and_update_winget(self):
        """Winget sürümünü kontrol eder."""
        self.log_text.append("Winget sürümü kontrol ediliyor...")
        self.worker = SubprocessWorker("winget --version")
        self.worker.progress.connect(self.log_text.append)
        self.worker.start()

    def install_choco(self):
        """Chocolatey kurulumunu başlatır."""
        command = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        self.worker = SubprocessWorker(f"powershell -Command \"{command}\"")
        self.worker.progress.connect(self.log_text.append)
        self.worker.finished.connect(lambda: QMessageBox.information(self, "Tamamlandı", "Chocolatey kurulum işlemi bitti."))
        self.worker.start()

    def open_program_search_window(self):
        # Bu fonksiyonun implementasyonu basitlik adına şimdilik çıkarıldı.
        # Gelecekte eklenebilir.
        QMessageBox.information(self, "Bilgi", "Program arama özelliği gelecek sürümlerde eklenecektir.")

    def prog_ver_check(self):
        QMessageBox.information(self, "Bilgi", "Otomatik güncelleme özelliği gelecek sürümlerde eklenecektir.")

    def create_menu(self):
        main_menu = self.menuBar()
        view_menu = main_menu.addMenu('Temalar')
        dark_theme_action = QAction('Karanlık Tema', self)
        dark_theme_action.triggered.connect(self.apply_dark_theme)
        view_menu.addAction(dark_theme_action)
        light_theme_action = QAction('Açık Tema', self)
        light_theme_action.triggered.connect(self.apply_light_theme)
        view_menu.addAction(light_theme_action)
        
    def apply_dark_theme(self):
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    def apply_light_theme(self):
        self.setStyleSheet('')

    def apply_windows_theme(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize')
            value = winreg.QueryValueEx(key, 'AppsUseLightTheme')[0]
            if value == 0:
                self.apply_dark_theme()
            else:
                self.apply_light_theme()
        except Exception:
            self.apply_light_theme()

def main():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
        
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
