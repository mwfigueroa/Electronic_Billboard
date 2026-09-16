# Simulador de panel — pipeline de contenido del cartel
# Especificación: ../docs/14_software_contenido.md
# Arquitectura del driver: ../docs/11_arquitectura_colorlight_5a75b.md

PY  := .venv/bin/python
PIP := .venv/bin/pip

EXAMPLE := examples/playlist.json
PLAYLIST ?= $(EXAMPLE)
OUT     := out
ARGS    ?= --scale 5
VIDEO_URL := https://test-videos.co.uk/vids/sintel/mp4/h264/360/Sintel_360_10s_1MB.mp4
MEDIA   := media/sintel_10s.mp4

.PHONY: all venv test render view vectors video app demo editor hooks clean distclean help

all: test render

# --- Entorno ----------------------------------------------------------------
venv: .venv/pyvenv.cfg

.venv/pyvenv.cfg: requirements.txt requirements-dev.txt
	python3 -m venv .venv
	$(PIP) install -q -U pip
	$(PIP) install -q -r requirements.txt -r requirements-dev.txt
	@touch $@

# --- Verificacion -----------------------------------------------------------
test: venv
	$(PY) -m pytest -q

# Activa el pre-commit del repo (corre los tests si cambia simulator/)
hooks:
	git -C .. config core.hooksPath .githooks
	@echo "pre-commit activado: corre la suite cuando el commit toca simulator/"

# --- PNG por slide (pixeles cuadrados visibles) -----------------------------
render: venv
	$(PY) -m panel_sim.render $(PLAYLIST) -o $(OUT)

# --- Visor animado en tiempo real -------------------------------------------
# Ej.: make view ARGS="--panel-distance 5 --monitor-inch 32 --monitor-px 1920 --eye-cm 60"
#      make view PLAYLIST=examples/playlist_video.json
view: venv
	$(PY) -m panel_sim.viewer $(PLAYLIST) $(ARGS)

# --- Video de ejemplo (Sintel © Blender Foundation, CC-BY 3.0) --------------
video: venv
	mkdir -p media
	curl -fsSL -o $(MEDIA) $(VIDEO_URL)
	@echo "listo: $(MEDIA) — probar con make view PLAYLIST=examples/playlist_video.json"

# --- App de contenido (contrato de wire v1, docs/14) -------------------------
# Publica la playlist como fuente viva: horarios, recarga en caliente, /status
app: venv
	$(PY) -m content.app $(PLAYLIST)

# --- Editor de playlist con preview en vivo (herramienta del lado panel) ------
# Abrir http://127.0.0.1:8090 — al guardar, la app recarga sola
editor: venv
	$(PY) -m panel_sim.editor $(PLAYLIST)

# --- Demo mínima del transporte (Pillow crudo; no es la app) ------------------
demo: venv
	$(PY) examples/app_ejemplo.py

# --- Vectores dorados para los testbenches del HDL --------------------------
vectors: venv
	$(PY) -m panel_sim.vectors -o vectors

clean:
	rm -rf $(OUT) .pytest_cache panel_sim/__pycache__ tests/__pycache__

distclean: clean
	rm -rf .venv

help:
	@echo "make          - tests + render de ejemplo"
	@echo "make test     - corre pytest"
	@echo "make hooks    - activa el pre-commit del repo (tests antes de commitear)"
	@echo "make render   - PNG de cada slide en $(OUT)/"
	@echo "make view     - visor animado; teclas: SPACE pausa,"
	@echo "                ←→ slide, 4/5/6 profundidad, G gamma, +/- distancia, S captura, Q salir"
	@echo "                Ej.: make view ARGS=\"--panel-distance 5 --monitor-inch 32 --monitor-px 1920 --eye-cm 60\""
	@echo "make vectors  - regenera vectors/*.mem para los testbenches"
	@echo "make video    - baja el video de ejemplo (CC-BY) a media/"
	@echo "make app      - publica la playlist como fuente viva (content/app.py)"
	@echo "make demo     - demo mínima del transporte (Pillow crudo, sin Timeline)"
	@echo "make editor   - editor de playlist con preview en vivo (http://127.0.0.1:8090)"
	@echo "make view PLAYLIST=examples/playlist_live.json - consume la fuente viva"
	@echo "make clean    - borra artefactos de salida"
	@echo "make distclean- borra tambien el venv"
