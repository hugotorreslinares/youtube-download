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
        # Validar que se reciba JSON válido
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON válido requerido'}), 400
        
        # Obtener y validar URL
        url = data.get('url')
        if url is None:
            return jsonify({'error': 'Campo "url" requerido'}), 400
            
        url = str(url).strip()
        if not url:
            return jsonify({'error': 'URL no puede estar vacía'}), 400
        
        # Validar URL de YouTube
        youtube_domains = ['youtube.com/watch', 'youtu.be/', 'youtube.com/shorts']
        if not any(domain in url for domain in youtube_domains):
            return jsonify({'error': 'URL debe ser de YouTube'}), 400
        
        # Configuración avanzada según documentación oficial yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,  # Continuar con errores
            # Configuración anti-bot avanzada
            'extractor_args': {
                'youtube': {
                    # Múltiples clientes como fallback
                    'player_client': ['android', 'mweb', 'web'],
                    # Skip webpage para evitar detección
                    'player_skip': ['webpage', 'configs'],
                },
                'youtubetab': {
                    'skip': ['webpage'],  # Skip webpage para tabs
                }
            },
            # Headers de Android/Mobile
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip',
                'X-YouTube-Client-Name': '3',
                'X-YouTube-Client-Version': '17.31.35',
            },
            # Otras opciones
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Verificar que se obtuvo información válida
            if info is None:
                return jsonify({'error': 'No se pudo extraer información del video'}), 400
            
            # Obtener formatos disponibles
            formats = []
            if info.get('formats'):
                for fmt in info['formats']:
                    if fmt and (fmt.get('vcodec') != 'none' or fmt.get('acodec') != 'none'):
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
        # Validar que se reciba JSON válido
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON válido requerido'}), 400
        
        # Obtener y validar URL
        url = data.get('url')
        if url is None:
            return jsonify({'error': 'Campo "url" requerido'}), 400
            
        url = str(url).strip()
        if not url:
            return jsonify({'error': 'URL no puede estar vacía'}), 400
            
        quality = data.get('quality', 'best')
        audio_only = data.get('audio_only', False)
        
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
        
        # Configuración avanzada para descarga
        ydl_opts = {
            'format': format_selector,
            'outtmpl': outtmpl,
            'logger': DownloadLogger(download_id),
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'no_warnings': True,
            'ignoreerrors': True,  # Continuar con errores
            # Configuración anti-bot avanzada
            'extractor_args': {
                'youtube': {
                    # Múltiples clientes como fallback
                    'player_client': ['android', 'mweb', 'web'],
                    # Skip webpage para evitar detección
                    'player_skip': ['webpage', 'configs'],
                },
                'youtubetab': {
                    'skip': ['webpage'],  # Skip webpage para tabs
                }
            },
            # Headers de Android/Mobile
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip',
                'X-YouTube-Client-Name': '3',
                'X-YouTube-Client-Version': '17.31.35',
            },
            # Otras opciones
            'socket_timeout': 60,
            'retries': 5,
            'fragment_retries': 5,
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
