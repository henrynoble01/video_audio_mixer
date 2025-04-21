# Video Audio Mixer

Hey there! 👋 This is a simple but powerful desktop app I made to help you combine video files with separate audio tracks. You know those times when you have a video recording but want to replace or add different audio to it? That's exactly what this tool is for!

## What Can It Do?

- Combine any video with any audio file
- Hardware acceleration support for faster processing
- Works with popular video formats (MP4, AVI, MOV, MKV)
- Supports common audio formats (MP3, WAV, AAC, M4A, OGG, FLAC)
- Shows real-time progress while processing
- Super easy to use with a simple interface

## Requirements

- Python 3.6 or newer
- FFmpeg (required for video processing)
- PyQt6 (for the user interface)

## Quick Start

1. First, make sure you have FFmpeg installed on your system:
   - Windows users: Check out [this guide](https://www.wikihow.com/Install-FFmpeg-on-Windows)
   - Make sure FFmpeg is added to your system's PATH

2. Install the dependencies:
   ```
   pip install poetry
   poetry install
   ```

3. Run the app:
   ```
   poetry run python app.py
   ```

## How to Use

1. Click "Browse" to select your video file
2. Click "Browse" to select your audio file
3. Choose where you want to save the output file
4. Click "Add Audio to Video" and wait for processing to complete

The app will show you the progress as it combines the files. If you have a GPU (NVIDIA/AMD) or Apple Silicon, it'll automatically use hardware acceleration to speed things up!

## Why I Made This

I got tired of using complex video editors just to add a different audio track to my videos. Sometimes you just want to quickly replace the audio in a video without dealing with timeline editing or complicated software. That's why I made this tool - simple, fast, and gets the job done!

## Tech Details

- Built with Python and PyQt6
- Uses FFmpeg for video/audio processing
- Supports hardware acceleration (CUDA, AMD, Apple Silicon)
- Cross-platform compatible

## Need Help?

If FFmpeg isn't working, make sure it's properly installed and added to your system's PATH. For Windows users, I've included a link to an installation guide in the requirements section above.

Feel free to open an issue if you run into any problems!

## License

Feel free to use this however you like! Just give credit if you share it around.