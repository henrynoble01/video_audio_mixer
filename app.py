import sys
import os
import subprocess
import platform
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class FFmpegWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        self.progress.emit("Processing started...")
        try:
            process = subprocess.run(
                self.command,
                shell=True,
                capture_output=True,
                text=True,
                check=False
            )
            if process.returncode == 0:
                self.progress.emit("Processing finished successfully!")
                output_message = f"Success!\nOutput:\n{process.stdout}\n{process.stderr}"
                self.finished.emit(True, output_message)
            else:
                error_message = f"FFmpeg Error (Code {process.returncode}):\n{process.stderr}"
                self.progress.emit("Processing failed.")
                self.finished.emit(False, error_message)
        except FileNotFoundError:
            error_message = "Error: 'ffmpeg' command not found.\nMake sure FFmpeg is installed and added to your system's PATH or provide the full path."
            self.progress.emit("Processing failed.")
            self.finished.emit(False, error_message)
        except Exception as e:
            import traceback
            error_message = f"An unexpected error occurred: {e}\n{traceback.format_exc()}"
            self.progress.emit("Processing failed.")
            self.finished.emit(False, error_message)

class VideoAudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Audio Mixer")
        self.setGeometry(200, 200, 600, 250)
        self.video_file = ""
        self.audio_file = ""
        self.output_file = ""
        self.ffmpeg_worker = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        video_layout = QHBoxLayout()
        video_label = QLabel("Video File:")
        video_label.setFixedWidth(80)
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select video file...")
        self.video_path_edit.setReadOnly(True)
        video_button = QPushButton("Browse...")
        video_button.clicked.connect(self.select_video_file)
        video_layout.addWidget(video_label)
        video_layout.addWidget(self.video_path_edit)
        video_layout.addWidget(video_button)
        main_layout.addLayout(video_layout)
        audio_layout = QHBoxLayout()
        audio_label = QLabel("Audio File:")
        audio_label.setFixedWidth(80)
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("Select audio file...")
        self.audio_path_edit.setReadOnly(True)
        audio_button = QPushButton("Browse...")
        audio_button.clicked.connect(self.select_audio_file)
        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self.audio_path_edit)
        audio_layout.addWidget(audio_button)
        main_layout.addLayout(audio_layout)
        output_layout = QHBoxLayout()
        output_label = QLabel("Output File:")
        output_label.setFixedWidth(80)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output location and name...")
        self.output_path_edit.setReadOnly(True)
        output_button = QPushButton("Browse...")
        output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(output_button)
        main_layout.addLayout(output_layout)
        main_layout.addStretch(1)
        self.process_button = QPushButton("Add Audio to Video")
        self.process_button.setFixedHeight(40)
        self.process_button.clicked.connect(self.start_processing)
        main_layout.addWidget(self.process_button)
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        self.setLayout(main_layout)

    def select_video_file(self):
        start_dir = os.path.expanduser("~")
        file_filter = "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, 'Select Video File', start_dir, file_filter)
        if fname:
            self.video_file = fname
            self.video_path_edit.setText(fname)
            self.status_label.setText("Status: Ready")

    def select_audio_file(self):
        start_dir = os.path.expanduser("~")
        file_filter = "Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, 'Select Audio File', start_dir, file_filter)
        if fname:
            self.audio_file = fname
            self.audio_path_edit.setText(fname)
            self.status_label.setText("Status: Ready")

    def select_output_file(self):
        start_dir = os.path.expanduser("~")
        default_name = ""
        if self.video_file:
            base, _ = os.path.splitext(os.path.basename(self.video_file))
            default_name = os.path.join(start_dir, f"{base}_with_audio.mp4")
        file_filter = "MP4 Video (*.mp4);;MOV Video (*.mov);;MKV Video (*.mkv);;All Files (*)"
        fname, _ = QFileDialog.getSaveFileName(self, 'Select Output File', default_name, file_filter)
        if fname:
            if not os.path.splitext(fname)[1] and "(*.mp4)" in _:
                 fname += ".mp4"
            elif not os.path.splitext(fname)[1] and "(*.mov)" in _:
                 fname += ".mov"
            elif not os.path.splitext(fname)[1] and "(*.mkv)" in _:
                 fname += ".mkv"
            self.output_file = fname
            self.output_path_edit.setText(fname)
            self.status_label.setText("Status: Ready")

    def detect_hwaccel(self):
        system = platform.system().lower()
        if system == "darwin":
            return "-hwaccel videotoolbox"
        elif system == "windows" or system == "linux":
            try:
                result = subprocess.run(["ffmpeg", "-hide_banner", "-hwaccels"], capture_output=True, text=True)
                if "cuda" in result.stdout:
                    return "-hwaccel cuda"
                elif "d3d11va" in result.stdout:
                    return "-hwaccel d3d11va"
                elif "dxva2" in result.stdout:
                    return "-hwaccel dxva2"
                elif "qsv" in result.stdout:
                    return "-hwaccel qsv"
                elif "vaapi" in result.stdout:
                    return "-hwaccel vaapi"
                elif "videotoolbox" in result.stdout:
                    return "-hwaccel videotoolbox"
                elif "opencl" in result.stdout:
                    return "-hwaccel opencl"
                elif "amf" in result.stdout:
                    return "-hwaccel amf"
            except Exception:
                pass
        return ""

    def start_processing(self):
        if not self.video_file:
            self.show_message("Error", "Please select a video file.", QMessageBox.Icon.Warning)
            return
        if not self.audio_file:
            self.show_message("Error", "Please select an audio file.", QMessageBox.Icon.Warning)
            return
        if not self.output_file:
            self.show_message("Error", "Please select an output file location.", QMessageBox.Icon.Warning)
            return
        if not os.path.exists(self.video_file):
             self.show_message("Error", f"Video file not found:\n{self.video_file}", QMessageBox.Icon.Critical)
             return
        if not os.path.exists(self.audio_file):
             self.show_message("Error", f"Audio file not found:\n{self.audio_file}", QMessageBox.Icon.Critical)
             return
        if self.ffmpeg_worker and self.ffmpeg_worker.isRunning():
            self.show_message("Info", "Processing is already in progress.", QMessageBox.Icon.Information)
            return
        ffmpeg_path = "ffmpeg"
        hwaccel = self.detect_hwaccel()
        command = (
            f'{ffmpeg_path} {hwaccel} -i "{self.video_file}" -i "{self.audio_file}" '
            f'-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 '
            f'-shortest "{self.output_file}"'
        )
        print(f"Executing command: {command}")
        self.process_button.setEnabled(False)
        self.status_label.setText("Status: Processing...")
        self.ffmpeg_worker = FFmpegWorker(command)
        self.ffmpeg_worker.progress.connect(self.update_status)
        self.ffmpeg_worker.finished.connect(self.on_processing_finished)
        self.ffmpeg_worker.start()

    def update_status(self, message):
        self.status_label.setText(f"Status: {message}")

    def on_processing_finished(self, success, message):
        self.process_button.setEnabled(True)
        self.status_label.setText(f"Status: {message.splitlines()[0]}")
        if success:
            self.show_message("Success", f"Operation completed successfully!\nOutput saved to:\n{self.output_file}", QMessageBox.Icon.Information)
        else:
             self.show_message("Error", message, QMessageBox.Icon.Critical)
        self.ffmpeg_worker = None

    def show_message(self, title, message, icon=QMessageBox.Icon.NoIcon):
        msgBox = QMessageBox(self)
        msgBox.setIcon(icon)
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
        msgBox.exec()

    def closeEvent(self, event):
        if self.ffmpeg_worker and self.ffmpeg_worker.isRunning():
            print("Terminating FFmpeg process...")
            self.ffmpeg_worker.terminate()
            self.ffmpeg_worker.wait()
        event.accept()

if __name__ == '__main__':
    import traceback
    def excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print("Error:", tb)
        QApplication.quit()
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    window = VideoAudioApp()
    window.show()
    sys.exit(app.exec())