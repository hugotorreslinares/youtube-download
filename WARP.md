# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Production Deployment
```bash
# Using Gunicorn (production)
./start.sh

# Using Docker
docker build -t youtube-downloader .
docker run -p 5000:5000 youtube-downloader
```

### Testing and Validation
```bash
# Test API endpoints manually
curl -X POST http://localhost:5000/api/video-info \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID"}'

# Check download progress
curl http://localhost:5000/api/progress/DOWNLOAD_ID
```

## Architecture Overview

### Backend (Flask Application)
- **Main Application**: `app.py` - Flask web server with YouTube download functionality
- **Core Dependencies**: Flask, yt-dlp (YouTube downloader), flask-cors
- **Threading Model**: Uses daemon threads for non-blocking downloads
- **Progress Tracking**: In-memory storage using global `download_progress` dictionary

### API Endpoints
- `GET /` - Serves main HTML interface
- `POST /api/video-info` - Extracts video metadata without downloading
- `POST /api/download` - Initiates video/audio download with progress tracking
- `GET /api/progress/<download_id>` - Returns download progress status
- `GET /api/download-file/<download_id>` - Serves completed download files
- `GET /api/downloads` - Lists all active downloads

### Frontend Architecture
- **Single-Page Application**: Vanilla JavaScript (no frameworks)
- **State Management**: Class-based `YouTubeDownloader` with internal state
- **UI Pattern**: Section-based visibility management (loading, info, progress, error)
- **Progress Updates**: Polling-based progress monitoring using `setInterval`

### File Structure Pattern
```
app.py                 # Main Flask application and API routes
templates/index.html   # Single HTML template with all UI sections
static/
  css/style.css       # CSS with CSS custom properties for theming
  js/app.js          # Frontend JavaScript controller class
downloads/            # Temporary download storage (auto-cleanup)
```

## Key Implementation Details

### Download Flow
1. **Video Info Phase**: Extract metadata using yt-dlp without downloading
2. **Download Initiation**: Generate unique UUID, start background thread
3. **Progress Tracking**: Hook into yt-dlp progress callbacks
4. **File Serving**: Temporary file storage with automatic cleanup after 10 seconds
5. **Cleanup**: Remove files and progress data after download completion

### Threading and Concurrency
- Downloads run in daemon threads to prevent blocking the main Flask process
- Progress updates stored in shared `download_progress` dictionary
- No persistence - all state lost on server restart
- Each download gets a unique UUID for isolation

### Error Handling Patterns
- Backend: Try-catch with JSON error responses
- Frontend: Centralized error display via `showError()` method
- yt-dlp errors captured through custom logger class

### Configuration
- **Environment Variables**: `PORT` (default: 5000), `FLASK_ENV`
- **Gunicorn Config**: `gunicorn.conf.py` with production settings
- **Docker Support**: Multi-stage build with ffmpeg dependency

## Development Guidelines

### Adding New Download Formats
When adding support for new formats, update:
1. Quality selector options in `templates/index.html`
2. Format mapping logic in `app.py` download endpoint
3. Frontend format validation in `static/js/app.js`

### Extending Progress Tracking
The `download_progress` dictionary structure:
```python
{
    'status': 'starting|downloading|completed|error',
    'progress': 0-100,
    'downloaded': bytes,
    'total': bytes,
    'speed': bytes_per_second,
    'file_path': str,
    'error': str
}
```

### Frontend State Management
The `YouTubeDownloader` class manages UI state through section visibility:
- Only one section visible at a time
- State transitions: URL input → Loading → Video info → Progress → Complete/Error
- Use `hideAllSections()` before showing new content

### URL Validation
YouTube URL patterns supported:
- `youtube.com/watch?v=VIDEO_ID`
- `youtu.be/VIDEO_ID`
- `youtube.com/shorts/VIDEO_ID`

### Legal and Compliance Notes
This application downloads YouTube content using yt-dlp. Ensure compliance with:
- YouTube Terms of Service
- Local copyright laws
- Fair use guidelines when deployed publicly