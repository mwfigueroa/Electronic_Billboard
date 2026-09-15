# Simulador de panel — pipeline de contenido del cartel
# Especificación: ../docs/14_software_contenido.md
# Arquitectura del driver: ../docs/11_arquitectura_colorlight_5a75b.md

PY  := .venv/bin/python
PIP := .venv/bin/pip

EXAMPLE := examples/playlist.json
PLAYLIST ?= $(EXAMPLE)
OUT     := out
ARGS    ?= --scale 3
VIDEO_URL := https://test-videos.co.uk/vids/sintel/mp4/h264/360/Sintel_360_10s_1MB.mp4
MEDIA   := media/sintel_10s.mp4

.PHONY: all venv test render view vectors video clean distclean help

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
	@echo "make render   - PNG de cada slide en $(OUT)/"
	@echo "make view     - visor animado; teclas: SPACE pausa,"
	@echo "                ←→ slide, 4/5/6 profundidad, G gamma, +/- distancia, S captura, Q salir"
	@echo "                Ej.: make view ARGS=\"--panel-distance 5 --monitor-inch 32 --monitor-px 1920 --eye-cm 60\""
	@echo "make vectors  - regenera vectors/*.mem para los testbenches"
	@echo "make video    - baja el video de ejemplo (CC-BY) a media/"
	@echo "make view PLAYLIST=examples/playlist_video.json - reproduce el video"
	@echo "make clean    - borra artefactos de salida"
	@echo "make distclean- borra tambien el venv"
