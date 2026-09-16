"""Línea de tiempo: compone cada slide a un canvas RGB888.

Determinista respecto de ``t`` (y de la hora para los slides de reloj y los
horarios): el visor y el render PNG consumen el mismo ``frame_at``, así que no
hay dos caminos de composición que puedan divergir.

Con horarios, el "programa" es el subconjunto de slides vigentes en ``now``:
``locate`` mapea el tiempo dentro de ese subconjunto y ``next_active`` salta
los que no están vigentes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from .canvas import contain, hex_to_rgb, new_canvas, paste_aligned, text_image
from .playlist import (
    ClockSlide,
    ColorSlide,
    ImageSlide,
    LiveSlide,
    Playlist,
    TextSlide,
    VideoSlide,
    is_active,
)
from .video import VideoSource


class Timeline:
    def __init__(self, playlist: Playlist):
        if not playlist.slides:
            raise ValueError("la playlist no tiene slides")
        self.playlist = playlist
        self._images: dict[Path, Image.Image] = {}
        self._videos: dict[object, VideoSource] = {}

    @property
    def duration(self) -> float:
        return sum(slide.duration for slide in self.playlist.slides)

    def program_duration(self, now: datetime | None = None) -> float:
        """Duración total de los slides vigentes a esa hora."""
        now = now or datetime.now()
        return sum(slide.duration for slide in self.playlist.active_slides(now))

    def slide_active(self, index: int, now: datetime | None = None) -> bool:
        return is_active(self.playlist.slides[index], now or datetime.now())

    def next_active(self, index: int, now: datetime | None = None, step: int = 1) -> int | None:
        """Índice del próximo slide vigente (cíclico); None si no hay ninguno."""
        now = now or datetime.now()
        total = len(self.playlist.slides)
        for k in range(1, total + 1):
            candidate = (index + step * k) % total
            if self.slide_active(candidate, now):
                return candidate
        return None

    def locate(self, t: float, now: datetime | None = None) -> tuple[int, float] | None:
        """Tiempo absoluto → (índice, tiempo local) dentro del programa vigente.

        ``None`` si ningún slide está vigente a esa hora. Sin horarios, el
        programa es la playlist completa y el resultado es el de siempre.
        """
        now = now or datetime.now()
        active = [
            (index, slide)
            for index, slide in enumerate(self.playlist.slides)
            if is_active(slide, now)
        ]
        total = sum(slide.duration for _, slide in active)
        if total <= 0:
            return None
        t %= total
        for index, slide in active:
            if t < slide.duration:
                return index, t
            t -= slide.duration
        index, slide = active[-1]
        return index, slide.duration

    def frame(self, t: float, now: datetime | None = None) -> np.ndarray:
        found = self.locate(t, now)
        display = self.playlist.display
        if found is None:
            return np.zeros((display.height, display.width, 3), dtype=np.uint8)
        index, local_t = found
        return self.frame_at(index, local_t, now)

    def frame_at(self, index: int, local_t: float, now: datetime | None = None) -> np.ndarray:
        slide = self.playlist.slides[index]
        display = self.playlist.display
        width, height = display.width, display.height

        if isinstance(slide, VideoSlide) or isinstance(slide, LiveSlide):
            return self._video_frame(slide, local_t)
        if isinstance(slide, ColorSlide):
            canvas = new_canvas(width, height, hex_to_rgb(slide.color))
        else:
            background = hex_to_rgb(slide.background or display.background)
            canvas = new_canvas(width, height, background)
            if isinstance(slide, TextSlide):
                img = text_image(
                    slide.text, slide.font, slide.size,
                    hex_to_rgb(slide.color), align=slide.align,
                )
                self._place(canvas, img, slide, background, local_t)
            elif isinstance(slide, ClockSlide):
                text = (now or datetime.now()).strftime(slide.fmt)
                img = text_image(
                    text, slide.font, slide.size,
                    hex_to_rgb(slide.color), align="center",
                )
                paste_aligned(canvas, img, "center", "middle")
            elif isinstance(slide, ImageSlide):
                img = contain(
                    self._load(slide.path), width, height,
                    limit_width=not slide.scroll,
                )
                self._place(canvas, img, slide, background, local_t)
            else:  # pragma: no cover
                raise TypeError(f"slide desconocido: {slide!r}")
        return np.asarray(canvas, dtype=np.uint8)

    def _place(
        self,
        canvas: Image.Image,
        img: Image.Image,
        slide: TextSlide | ImageSlide,
        background: tuple[int, int, int],
        local_t: float,
    ) -> None:
        if slide.scroll:
            strip = new_canvas(img.width, canvas.height, background)
            strip.paste(img, (0, (canvas.height - img.height) // 2), img)
            period = canvas.width + strip.width
            offset = int((slide.speed_px_s * local_t) % period)
            if slide.scroll == "right":
                x = -strip.width + offset
            else:
                x = canvas.width - offset
            canvas.paste(strip, (x, 0))
        else:
            align = getattr(slide, "align", "center")
            valign = getattr(slide, "valign", "middle")
            paste_aligned(canvas, img, align, valign)

    def close(self) -> int:
        """Termina los decodificadores de video abiertos. Devuelve cuántos."""
        count = len(self._videos)
        for source in self._videos.values():
            source.close()
        self._videos.clear()
        return count

    def _load(self, path: Path) -> Image.Image:
        if path not in self._images:
            self._images[path] = Image.open(path).convert("RGBA")
        return self._images[path]

    def _video_frame(self, slide: VideoSlide | LiveSlide, local_t: float) -> np.ndarray:
        source = self._videos.get(slide)
        if source is None:
            display = self.playlist.display
            size = (display.width, display.height)
            if isinstance(slide, LiveSlide):
                source = VideoSource(
                    slide.url, size, fps=slide.fps, live=True,
                    input_args=slide.input_args,
                )
            else:
                source = VideoSource(
                    slide.path, size, fps=slide.fps, loop=slide.loop,
                )
            self._videos[slide] = source
        if isinstance(slide, LiveSlide):
            return source.frame_latest()
        return source.frame_at(local_t)
