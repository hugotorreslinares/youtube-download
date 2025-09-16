#!/usr/bin/env python3
import os
import json
from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp
import threading
import uuid
from datetime import datetime
import tempfile
import shutil

app = Flask(__name__)
CORS(app)

# Configuración
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Almacén de progreso de descargas
download_progress = {}

class DownloadLogger:
    def __init__(self, download_id):
        self.download_id = download_id
    
    def debug(self, msg):
        pass
    
    def warning(self, msg):
        pass
    
    def error(self, msg):
        download_progress[self.download_id]['status'] = 'error'
        download_progress[self.download_id]['error'] = str(msg)

def progress_hook(d, download_id):
    """Hook para actualizar el progreso de descarga"""
    if download_id not in download_progress:
        return
    
    if d['status'] == 'downloading':
        if 'total_bytes' in d and d['total_bytes']:
            percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            download_progress[download_id]['progress'] = round(percentage, 2)
            download_progress[download_id]['downloaded'] = d.get('downloaded_bytes', 0)
            download_progress[download_id]['total'] = d.get('total_bytes', 0)
            download_progress[download_id]['speed'] = d.get('speed', 0)
        
    elif d['status'] == 'finished':
        download_progress[download_id]['status'] = 'completed'
        download_progress[download_id]['progress'] = 100
        download_progress[download_id]['file_path'] = d['filename']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Obtener información del video sin descargarlo"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL requerida'}), 400
        
        # Validar URL de YouTube
        if not any(domain in url for domain in ['youtube.com/watch', 'youtu.be/', 'youtube.com/shorts']):
            return jsonify({'error': 'URL debe ser de YouTube'}), 400
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Obtener formatos disponibles
            formats = []
            if 'formats' in info:
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' or fmt.get('acodec') != 'none':
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': fmt.get('format_note', 'Unknown'),
                            'filesize': fmt.get('filesize'),
                            'vcodec': fmt.get('vcodec'),
                            'acodec': fmt.get('acodec')
                        })
            
            video_info = {
                'title': info.get('title', 'Sin título'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Desconocido'),
                'view_count': info.get('view_count', 0),
                'thumbnail': info.get('thumbnail'),
                'description': info.get('description', ''),
                'upload_date': info.get('upload_date'),
                'formats': formats[:10]  # Limitar a 10 formatos principales
            }
            
            return jsonify(video_info)
            
    except Exception as e:
        return jsonify({'error': f'Error al obtener información del video: {str(e)}'}), 400

@app.route('/api/download', methods=['POST'])
def download_video():
    """Iniciar descarga de video"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best')
        audio_only = data.get('audio_only', False)
        
        if not url:
            return jsonify({'error': 'URL requerida'}), 400
        
        # Generar ID único para esta descarga
        download_id = str(uuid.uuid4())
        
        # Inicializar progreso
        download_progress[download_id] = {
            'status': 'starting',
            'progress': 0,
            'downloaded': 0,
            'total': 0,
            'speed': 0,
            'file_path': None,
            'error': None
        }
        
        # Configurar formato
        if audio_only:
            format_selector = 'bestaudio/best'
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f'{download_id}_%(title)s.%(ext)s')
        else:
            if quality == 'best':
                format_selector = 'best'
            elif quality == '1080':
                format_selector = 'best[height<=1080]'
            elif quality == '720':
                format_selector = 'best[height<=720]'
            elif quality == '480':
                format_selector = 'best[height<=480]'
            else:
                format_selector = quality  # ID de formato específico
            
            outtmpl = os.path.join(DOWNLOAD_FOLDER, f'{download_id}_%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': outtmpl,
            'logger': DownloadLogger(download_id),
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
        }
        
        def download_thread():
            try:
                download_progress[download_id]['status'] = 'downloading'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                download_progress[download_id]['status'] = 'error'
                download_progress[download_id]['error'] = str(e)
        
        # Iniciar descarga en hilo separado
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'download_id': download_id,
            'message': 'Descarga iniciada'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al iniciar descarga: {str(e)}'}), 400

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    """Obtener progreso de descarga"""
    if download_id not in download_progress:
        return jsonify({'error': 'ID de descarga no encontrado'}), 404
    
    return jsonify(download_progress[download_id])

@app.route('/api/download-file/<download_id>')
def download_file(download_id):
    """Descargar archivo completado"""
    if download_id not in download_progress:
        abort(404)
    
    progress_data = download_progress[download_id]
    
    if progress_data['status'] != 'completed' or not progress_data['file_path']:
        abort(404)
    
    file_path = progress_data['file_path']
    
    if not os.path.exists(file_path):
        abort(404)
    
    # Obtener nombre del archivo
    filename = os.path.basename(file_path)
    
    def remove_file_after_send(response):
        try:
            # Limpiar después de enviar
            threading.Timer(10.0, lambda: cleanup_download(download_id)).start()
        except Exception:
            pass
        return response
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename.replace(f'{download_id}_', ''),
        mimetype='application/octet-stream'
    )

def cleanup_download(download_id):
    """Limpiar archivos y datos de descarga"""
    if download_id in download_progress:
        progress_data = download_progress[download_id]
        if progress_data.get('file_path') and os.path.exists(progress_data['file_path']):
            try:
                os.remove(progress_data['file_path'])
            except Exception:
                pass
        del download_progress[download_id]

@app.route('/api/downloads')
def list_downloads():
    """Listar descargas activas"""
    return jsonify(download_progress)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)