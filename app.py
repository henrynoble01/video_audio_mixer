import sys
import os # Import the os module for path manipulation
import subprocess # Import subprocess for running FFmpeg later
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog,
    QSizePolicy, QMessageBox # Import QMessageBox for displaying errors/info
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal # Import QThread and pyqtSignal for background processing

# --- Add FFmpeg Worker Thread ---
# We'll run FFmpeg in a separate thread to avoid freezing the GUI
class FFmpegWorker(QThread):
    # Signals to communicate back to the main thread
    progress = pyqtSignal(str) # To send status updates
    finished = pyqtSignal(bool, str) # To signal completion (success/fail, message)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        self.progress.emit("Processing started...")
        try:
            # Use shell=True for simplicity here, but be cautious with user input
            # On Windows, shell=True might be needed if ffmpeg is in PATH but not directly executable
            # On Linux/macOS, passing command as a list (shlex.split) is often safer if shell=False
            process = subprocess.run(
                self.command,
                shell=True, # Make sure FFmpeg can be found in PATH or use full path
                capture_output=True,
                text=True,
                check=False # Don't raise exception on non-zero exit code, handle it manually
            )

            if process.returncode == 0:
                self.progress.emit("Processing finished successfully!")
                # Include stdout for potential info, though ffmpeg often uses stderr
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
            error_message = f"An unexpected error occurred: {e}\n{traceback.format_exc()}"
            self.progress.emit("Processing failed.")
            self.finished.emit(False, error_message)


# --- Main Application Window ---
class VideoAudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Audio Mixer")
        self.setGeometry(200, 200, 600, 250) # x, y, width, height

        # Store file paths
        self.video_file = ""
        self.audio_file = ""
        self.output_file = ""
        self.ffmpeg_worker = None # To hold the worker thread instance

        self.initUI()

    def initUI(self):
        # --- Main Layout ---
        main_layout = QVBoxLayout(self)

        # --- Video File Selection ---
        video_layout = QHBoxLayout()
        video_label = QLabel("Video File:")
        video_label.setFixedWidth(80)
        self.video_path_edit = QLineEdit()
        self.video_path_edit.setPlaceholderText("Select video file...")
        self.video_path_edit.setReadOnly(True)
        video_button = QPushButton("Browse...")
        # *** Connect button click ***
        video_button.clicked.connect(self.select_video_file)

        video_layout.addWidget(video_label)
        video_layout.addWidget(self.video_path_edit)
        video_layout.addWidget(video_button)
        main_layout.addLayout(video_layout)

        # --- Audio File Selection ---
        audio_layout = QHBoxLayout()
        audio_label = QLabel("Audio File:")
        audio_label.setFixedWidth(80)
        self.audio_path_edit = QLineEdit()
        self.audio_path_edit.setPlaceholderText("Select audio file...")
        self.audio_path_edit.setReadOnly(True)
        audio_button = QPushButton("Browse...")
        # *** Connect button click ***
        audio_button.clicked.connect(self.select_audio_file)

        audio_layout.addWidget(audio_label)
        audio_layout.addWidget(self.audio_path_edit)
        audio_layout.addWidget(audio_button)
        main_layout.addLayout(audio_layout)

        # --- Output File Selection ---
        output_layout = QHBoxLayout()
        output_label = QLabel("Output File:")
        output_label.setFixedWidth(80)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("Select output location and name...")
        self.output_path_edit.setReadOnly(True)
        output_button = QPushButton("Browse...")
        # *** Connect button click ***
        output_button.clicked.connect(self.select_output_file)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(output_button)
        main_layout.addLayout(output_layout)

        # --- Spacer to push elements up ---
        main_layout.addStretch(1)

        # --- Process Button ---
        self.process_button = QPushButton("Add Audio to Video")
        self.process_button.setFixedHeight(40)
        # *** Connect button click ***
        self.process_button.clicked.connect(self.start_processing)
        main_layout.addWidget(self.process_button)

        # --- Status Label ---
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    # --- File Selection Methods ---
    def select_video_file(self):
        """Opens a dialog to select a video file."""
        # Suggest starting directory (optional, e.g., user's home)
        start_dir = os.path.expanduser("~")
        # Define supported video file types (adjust as needed)
        file_filter = "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, 'Select Video File', start_dir, file_filter)
        if fname: # Check if a file was actually selected
            self.video_file = fname
            self.video_path_edit.setText(fname)
            self.status_label.setText("Status: Ready") # Reset status

    def select_audio_file(self):
        """Opens a dialog to select an audio file."""
        start_dir = os.path.expanduser("~")
        # Define supported audio file types
        file_filter = "Audio Files (*.mp3 *.wav *.aac *.m4a *.ogg *.flac);;All Files (*)"
        fname, _ = QFileDialog.getOpenFileName(self, 'Select Audio File', start_dir, file_filter)
        if fname:
            self.audio_file = fname
            self.audio_path_edit.setText(fname)
            self.status_label.setText("Status: Ready")

    def select_output_file(self):
        """Opens a dialog to select the output file path and name."""
        start_dir = os.path.expanduser("~")
        # Suggest a default filename based on video input (optional)
        default_name = ""
        if self.video_file:
            base, _ = os.path.splitext(os.path.basename(self.video_file))
            default_name = os.path.join(start_dir, f"{base}_with_audio.mp4")

        # Define output file types (match common FFmpeg output)
        file_filter = "MP4 Video (*.mp4);;MOV Video (*.mov);;MKV Video (*.mkv);;All Files (*)"
        fname, _ = QFileDialog.getSaveFileName(self, 'Select Output File', default_name, file_filter)
        if fname:
            # Ensure the file has a reasonable extension if user didn't type one
            # This logic can be more sophisticated
            if not os.path.splitext(fname)[1] and "(*.mp4)" in _: # Check selected filter if no ext
                 fname += ".mp4"
            elif not os.path.splitext(fname)[1] and "(*.mov)" in _:
                 fname += ".mov"
            elif not os.path.splitext(fname)[1] and "(*.mkv)" in _:
                 fname += ".mkv"
            # Add more cases if needed

            self.output_file = fname
            self.output_path_edit.setText(fname)
            self.status_label.setText("Status: Ready")

    # --- Processing Logic ---
    def start_processing(self):
        """Validates inputs and starts the FFmpeg process in a worker thread."""
        # 1. Validate Inputs
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

        # Prevent starting multiple processes
        if self.ffmpeg_worker and self.ffmpeg_worker.isRunning():
            self.show_message("Info", "Processing is already in progress.", QMessageBox.Icon.Information)
            return

        # 2. Construct FFmpeg Command (Replace Audio Example)
        # IMPORTANT: Adjust 'ffmpeg_path' if FFmpeg isn't in your system PATH
        ffmpeg_path = "ffmpeg" # Or "C:/path/to/ffmpeg/bin/ffmpeg.exe" or "/usr/local/bin/ffmpeg" etc.

        # Use quotes for paths to handle spaces
        command = (
            f'{ffmpeg_path} -i "{self.video_file}" -i "{self.audio_file}" '
            f'-c:v copy -c:a aac -map 0:v:0 -map 1:a:0 '
            f'-shortest "{self.output_file}"'
        )
        print(f"Executing command: {command}") # For debugging

        # 3. Disable UI elements and show status
        self.process_button.setEnabled(False)
        # Consider disabling browse buttons too
        self.status_label.setText("Status: Processing...")

        # 4. Start Worker Thread
        self.ffmpeg_worker = FFmpegWorker(command)
        self.ffmpeg_worker.progress.connect(self.update_status) # Connect signal to slot
        self.ffmpeg_worker.finished.connect(self.on_processing_finished) # Connect signal to slot
        self.ffmpeg_worker.start() # Start the thread


    def update_status(self, message):
        """Updates the status label."""
        self.status_label.setText(f"Status: {message}")

    def on_processing_finished(self, success, message):
        """Handles the completion of the FFmpeg process."""
        # Re-enable UI elements
        self.process_button.setEnabled(True)
        # Reset status label or keep the final message
        self.status_label.setText(f"Status: {message.splitlines()[0]}") # Show first line in status

        # Show detailed result in a message box
        if success:
            self.show_message("Success", f"Operation completed successfully!\nOutput saved to:\n{self.output_file}", QMessageBox.Icon.Information)
        else:
            # Display the detailed error message from FFmpegWorker
             self.show_message("Error", message, QMessageBox.Icon.Critical)

        self.ffmpeg_worker = None # Clear worker reference


    def show_message(self, title, message, icon=QMessageBox.Icon.NoIcon):
        """Helper function to display message boxes."""
        msgBox = QMessageBox(self) # Set parent to self
        msgBox.setIcon(icon)
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok)
        msgBox.exec()

    # --- Handle Window Closing ---
    def closeEvent(self, event):
        """Ensure worker thread is stopped if window is closed."""
        if self.ffmpeg_worker and self.ffmpeg_worker.isRunning():
            # You might want to ask the user if they want to stop
            # For simplicity now, we just try to terminate
            print("Terminating FFmpeg process...")
            # Note: Terminating subprocess cleanly can be tricky.
            # This might leave incomplete files.
            # A more robust solution might involve sending a 'q' key press
            # to FFmpeg's stdin if run with Popen, or using process group killing.
            self.ffmpeg_worker.terminate() # Attempt to terminate thread
            self.ffmpeg_worker.wait()      # Wait for termination
        event.accept() # Proceed with closing


# --- Main execution block ---
if __name__ == '__main__':
    # Add exception hook for uncaught exceptions (good for debugging)
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