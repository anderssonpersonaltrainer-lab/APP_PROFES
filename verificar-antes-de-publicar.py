#!/usr/bin/env python3
"""
Verificacion obligatoria ANTES de publicar la app.

Nacio el 22/08/2026 despues de caer DOS VECES en la misma trampa (09/08 y 22/08):
un backtick dentro de un comentario HTML que vive dentro de un template literal
cierra la cadena a mitad y deja TODO el bloque <script> invalido. El 09/08 eso
dejo la app en blanco para todos los roles, en produccion, durante horas.

Este script NO reemplaza la verificacion con el motor real del navegador
(`new Function()` sobre cada bloque <script>) — esa sigue siendo obligatoria y es
la unica que detecta cualquier error de sintaxis. Este script atrapa antes, y sin
depender de nada, los errores concretos que ya nos han mordido.

Uso:  python3 verificar-antes-de-publicar.py
Sale con codigo 1 si algo esta mal, para que sea imposible ignorarlo por accidente.
"""
import io
import json
import re
import sys
import hashlib

APP = 'andersson-app.html'
INDEX = 'index.html'
VERSION_JSON = 'version.json'

errores = []
avisos = []


def leer(ruta):
    try:
        return io.open(ruta, encoding='utf-8').read()
    except FileNotFoundError:
        errores.append(f'FALTA el archivo {ruta}')
        return None


app = leer(APP)
index = leer(INDEX)

# ---------------------------------------------------------------- 1
# LA TRAMPA QUE YA NOS MORDIO DOS VECES.
# Un backtick o un ${...} dentro de un comentario HTML rompe el template literal
# que lo contiene. Los comentarios largos van FUERA, encima de la funcion, con //.
if app:
    for m in re.finditer(r'<!--[\s\S]*?-->', app):
        linea = app[:m.start()].count('\n') + 1
        texto = m.group(0)
        if '`' in texto:
            errores.append(f'linea {linea}: comentario HTML con BACKTICK — rompe el <script> entero')
        if '${' in texto:
            errores.append(f'linea {linea}: comentario HTML con ${{...}} — rompe el <script> entero')

# ---------------------------------------------------------------- 2
# Los dos archivos que se publican deben ser IDENTICOS. GitHub Pages sirve
# index.html; andersson-app.html es la copia de trabajo. Si se editan por
# separado, se publica una version distinta a la que se verifico.
if app is not None and index is not None:
    if app != index:
        h1 = hashlib.md5(app.encode()).hexdigest()[:8]
        h2 = hashlib.md5(index.encode()).hexdigest()[:8]
        errores.append(f'{APP} ({h1}) e {INDEX} ({h2}) NO son identicos — falta copiar uno sobre el otro')

# ---------------------------------------------------------------- 3
# La version del <meta> y la de version.json tienen que coincidir. Si no, el
# mecanismo de auto-actualizacion queda detectando una version nueva para
# siempre, o no la detecta nunca (ver la nota junto a checkForUpdate).
if app:
    m = re.search(r'<meta name="app-version" content="([^"]+)">', app)
    version_meta = m.group(1) if m else None
    if not version_meta:
        errores.append('no se encontro <meta name="app-version"> en el HTML')
    vj = leer(VERSION_JSON)
    if vj:
        try:
            version_archivo = json.loads(vj).get('version')
            if version_meta and version_archivo != version_meta:
                errores.append(f'version.json dice "{version_archivo}" pero el HTML dice "{version_meta}"')
        except json.JSONDecodeError:
            errores.append('version.json no es JSON valido')

# ---------------------------------------------------------------- 4
# Los archivos de la PWA deben existir, o el navegador deja de ofrecer instalarla.
for archivo in ['manifest.json', 'sw.js', 'icon192.png', 'icon512.png']:
    try:
        io.open(archivo, 'rb').read(1)
    except FileNotFoundError:
        avisos.append(f'falta {archivo} (la app deja de ser instalable)')

# ---------------------------------------------------------------- 5
# Ningun token de GitHub puede quedar dentro de lo que se publica.
if app and re.search(r'github_pat_[A-Za-z0-9_]{20,}', app):
    errores.append('HAY UN TOKEN DE GITHUB dentro del HTML — no publicar')

# ---------------------------------------------------------------- resultado
print('=' * 62)
if errores:
    print('NO PUBLICAR — se encontraron problemas:\n')
    for e in errores:
        print('  X  ' + e)
else:
    print('Verificaciones automaticas: TODO BIEN')
if avisos:
    print('\nAvisos (no bloquean):')
    for a in avisos:
        print('  !  ' + a)
print('=' * 62)
print('RECORDATORIO: esto NO reemplaza pasar cada bloque <script> por')
print('new Function() en el navegador real. Esa verificacion sigue siendo')
print('obligatoria — es la unica que detecta cualquier error de sintaxis.')
sys.exit(1 if errores else 0)
