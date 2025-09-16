#!/bin/bash

# Crear directorio de descargas si no existe
mkdir -p downloads

# Ejecutar con Gunicorn para producción
gunicorn --config gunicorn.conf.py app:app