# herostep.py — aplicación principal HeroStep
# pygame · ventana sin bordes · grid de retratos por rol · i18n · rutas de build

import pygame
import sys
import os
import time
import math
import random
import numpy as np

from roster  import ROSTER, ROLE_COLORS, ROLE_ORDER
from tracker import (load_data, save_data, reset_data, pick_hero,
                     on_correct, on_wrong, tick_weight, get_summary)
from paths   import asset_chars_dir, asset_steps_dir
from paths   import asset_chars_dir, asset_steps_dir
from i18n    import t, set_lang, current_lang, save_lang_setting, load_lang_setting

import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("herostep.app")

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────

LANG = load_lang_setting()

WIN_W, WIN_H   = 1100, 660
FPS            = 60
SESSION_LENGTH = 10

PORTRAIT_SIZE    = 72
PORTRAIT_PAD     = 6
PORTRAITS_PER_ROW = 13

AUDIO_PANEL_H  = 88
STATUSBAR_H    = 32

# ── PALETA ────────────────────────────────────────────────────────────────────

C_BG        = (15,  15,  20)
C_PANEL     = (25,  25,  35)
C_TEXT      = (220, 220, 220)
C_SUBTEXT   = (120, 120, 140)
C_CORRECT   = (60,  210,  90)
C_WRONG     = (210,  60,  60)
C_HIGHLIGHT = (255, 200,   0)
C_DIVIDER   = (45,  45,  60)
C_RESET     = (80,  80, 100)


# ── APP ───────────────────────────────────────────────────────────────────────

class HeroStep:

    # ── INIT ──────────────────────────────────────────────────────────────────

    def __init__(self):
        set_lang(LANG)
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._channel = pygame.mixer.Channel(0)   # ← canal fijo
        self.AUDIO_END = pygame.USEREVENT + 1
        self._channel.set_endevent(self.AUDIO_END)
        self._playing_fragment = False

        self.screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.NOFRAME)
        pygame.display.set_caption(t("app_title"))

        # ← aquí
        from PIL import Image
        import io
        icon_path = os.path.join(os.path.dirname(asset_chars_dir()), "icon.ico")
        pil_icon = Image.open(icon_path).convert("RGBA").resize((32, 32))
        icon_bytes = io.BytesIO()
        pil_icon.save(icon_bytes, format="PNG")
        icon_bytes.seek(0)
        icon = pygame.image.load(icon_bytes, "icon.png")
        pygame.display.set_icon(icon)

        self.clock = self.clock  = pygame.time.Clock()

        self.font_lg = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_md = pygame.font.SysFont("segoeui", 16)
        self.font_sm = pygame.font.SysFont("segoeui", 13)

        self.data      = load_data()
        self.portraits : dict[str, pygame.Surface] = {}
        self.sounds : dict[str, pygame.mixer.Sound] = {}
        self.available : list[str] = []

        self._load_assets()
        self._build_grid()

        # Estado de juego
        self.current_hero : str   = ""
        self.audio_start  : float = 0.0
        self.elapsed      : float = 0.0
        self.loop_audio   : bool  = True
        self.muted        : bool  = False
        self.session      : list  = []
        self.feedback     : dict | None = None   # {correct, name, t}
        self.scene        : str   = "game"       # "game" | "summary" | "confirm_reset"

        # Rects de botones (se asignan en render)
        self.btn_replay   : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_loop     : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_mute     : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_continue : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_quit     : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_reset_yes: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.btn_reset_no : pygame.Rect = pygame.Rect(0, 0, 0, 0)
        self.reset_link   : pygame.Rect = pygame.Rect(0, 0, 0, 0)

        # Arrastre de ventana sin bordes
        self._drag_offset : tuple[int,int] | None = None

        if self.available:
            self._next_hero()
        else:
            print(t("errors.no_assets"))
            self._quit()

    # ── CARGA DE ASSETS ───────────────────────────────────────────────────────

    def _load_assets(self):
        chars_dir = asset_chars_dir()
        steps_dir = asset_steps_dir()
        roster_names = {h["name"] for h in ROSTER}

        for name in roster_names:
            img_path   = os.path.join(chars_dir, f"{name}.png")
            audio_path = os.path.join(steps_dir, f"{name}.wav")
            if os.path.exists(img_path) and os.path.exists(audio_path):
                try:
                    img = pygame.image.load(img_path).convert_alpha()
                    img = pygame.transform.smoothscale(img, (PORTRAIT_SIZE, PORTRAIT_SIZE))
                    self.portraits[name] = img
                    self.sounds[name]    = pygame.mixer.Sound(audio_path)
                    self.available.append(name)
                except Exception:
                    print(t("errors.load_warn", name=name))

        print(f"[INFO] {len(self.available)} heroes loaded.")

    # ── GRID ──────────────────────────────────────────────────────────────────

    def _build_grid(self):
        """Pre-calcula pygame.Rect para cada retrato según rol y orden del roster."""
        self.grid_rects   : dict[str, pygame.Rect] = {}
        self.role_label_y : dict[str, int]         = {}

        available_set = set(self.available)
        step = PORTRAIT_SIZE + PORTRAIT_PAD
        x0   = 10
        y    = AUDIO_PANEL_H + 8

        for role in ROLE_ORDER:
            heroes = [h["name"] for h in ROSTER
                      if h["role"] == role and h["name"] in available_set]
            if not heroes:
                continue

            self.role_label_y[role] = y
            y += 20   # altura de la label

            x = x0
            for i, name in enumerate(heroes):
                self.grid_rects[name] = pygame.Rect(x, y, PORTRAIT_SIZE, PORTRAIT_SIZE)
                x += step
                if (i + 1) % PORTRAITS_PER_ROW == 0:
                    x  = x0
                    y += step

            # Avanzar si la última fila no estaba completa
            if len(heroes) % PORTRAITS_PER_ROW != 0:
                y += step

            y += 4   # separador entre roles

    # ── LÓGICA DE AUDIO ───────────────────────────────────────────────────────

    def _next_hero(self):
        self.current_hero = pick_hero(self.data, self.available)
        self._play_audio()
        self.audio_start  = time.time()
        self.elapsed      = 0.0
        self.feedback     = None

    def _play_audio(self):
        self._channel.stop()
        self._channel.set_volume(0.0 if self.muted else 1.0)

        sound = self.sounds[self.current_hero]
        samples   = pygame.sndarray.samples(sound)
        total     = len(samples)
        max_start = int(total * 0.6)
        start     = random.randint(0, max_start)
        sliced    = np.ascontiguousarray(samples[start:])
        self._current_sound = pygame.sndarray.make_sound(sliced)
        self._current_sound.set_volume(0.0 if self.muted else 1.0)
        self._full_sound = sound
        self._full_sound.set_volume(0.0 if self.muted else 1.0)

        self._playing_fragment = True
        self._channel.play(self._current_sound, loops=0)

    def _toggle_loop(self):
        self.loop_audio = not self.loop_audio
        if self.loop_audio and not self._playing_fragment:
            self._channel.play(self._full_sound, loops=-1)
        elif not self.loop_audio and not self._playing_fragment:
            self._channel.play(self._full_sound, loops=0)

    def _toggle_mute(self):
        self.muted = not self.muted
        vol = 0.0 if self.muted else 1.0
        if hasattr(self, "_channel"):
            self._channel.set_volume(vol)
        if hasattr(self, "_full_sound"):
            self._full_sound.set_volume(vol)

    def _stop_audio(self):
        if hasattr(self, "_channel"):
            self._channel.stop()
        else:
            pygame.mixer.stop()

    def _replay(self):
        self._play_audio()

    # ── LÓGICA DE JUEGO ───────────────────────────────────────────────────────

    def _on_click_portrait(self, name: str):
        if self.feedback:
            return
        elapsed = time.time() - self.audio_start
        print(f"[DEBUG] clicked={name!r}  current={self.current_hero!r}")
        correct = (name == self.current_hero)

        self.session.append({"name": self.current_hero, "elapsed": elapsed, "correct": correct})
        self.feedback = {"correct": correct, "name": name, "t": time.time()}

        if correct:
            on_correct(self.data, self.current_hero, elapsed)
            self._stop_audio()
        else:
            on_wrong(self.data, self.current_hero, elapsed)

    def _do_reset(self):
        self.data    = reset_data()
        self.session = []
        self.scene   = "game"
        self._next_hero()

    # ── EVENTOS ───────────────────────────────────────────────────────────────

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
            elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._quit()
                    elif event.key == pygame.K_r:
                        self._replay()
                    elif event.key == pygame.K_l:
                        self._toggle_loop()
                    elif event.key == pygame.K_m:
                        self._toggle_mute()

            elif event.type == self.AUDIO_END:
                if self._playing_fragment and self.loop_audio:
                    self._playing_fragment = False
                    self._channel.play(self._full_sound, loops=-1)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
                # Inicio de arrastre de ventana (barra superior)
                if event.pos[1] < AUDIO_PANEL_H:
                    self._drag_offset = event.pos

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._drag_offset = None

            elif event.type == pygame.MOUSEMOTION:
                if self._drag_offset:
                    wx = pygame.display.get_wm_info().get("window", 0)
                    # Mover ventana vía SDL2 en Windows
                    try:
                        import ctypes
                        hwnd = pygame.display.get_wm_info()["window"]
                        ctypes.windll.user32.ReleaseCapture()
                        ctypes.windll.user32.SendMessageW(hwnd, 0x0112, 0xF012, 0)
                    except Exception:
                        pass

    def _handle_click(self, pos: tuple[int, int]):
        if self.scene == "game":
            if self.btn_replay.collidepoint(pos):
                self._replay(); return
            if self.btn_loop.collidepoint(pos):
                self._toggle_loop(); return
            if self.btn_mute.collidepoint(pos):
                self._toggle_mute(); return
            if self.reset_link.collidepoint(pos):
                self.scene = "confirm_reset"; return
            for name, rect in self.grid_rects.items():
                if rect.collidepoint(pos):
                    self._on_click_portrait(name); return
            if self.lang_toggle.collidepoint(pos):
                new_lang = "en" if current_lang() == "es" else "es"
                set_lang(new_lang)
                save_lang_setting(new_lang)
                return

        elif self.scene == "summary":
            if self.btn_continue.collidepoint(pos):
                self.session = []; self.scene = "game"; self._next_hero()
            elif self.btn_quit.collidepoint(pos):
                self._quit()

        elif self.scene == "confirm_reset":
            if self.btn_reset_yes.collidepoint(pos):
                self._do_reset()
            elif self.btn_reset_no.collidepoint(pos):
                self.scene = "game"

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def update(self):
        dt = self.clock.get_time() / 1000.0

        if self.scene != "game":
            return

        audio_playing = pygame.mixer.music.get_busy()

        # Tick de peso: corre mientras el audio suena y no está muteado
        # Incluye fallos (audio sigue) y estado neutro (sin feedback)
        if audio_playing and not self.muted:
            tick_weight(self.data, self.current_hero, dt)
            self.elapsed = time.time() - self.audio_start

        # Auto-avance tras acierto (1.2s de feedback verde)
        if self.feedback and self.feedback["correct"]:
            if time.time() - self.feedback["t"] > 1.2:
                if len(self.session) >= SESSION_LENGTH:
                    self.scene = "summary"
                else:
                    self._next_hero()

        # Limpiar feedback visual de fallo tras 0.7s (audio sigue)
        if self.feedback and not self.feedback["correct"]:
            if time.time() - self.feedback["t"] > 0.7:
                self.feedback = None

    # ── RENDER ────────────────────────────────────────────────────────────────

    def render(self):
        self.screen.fill(C_BG)

        if self.scene in ("game", "confirm_reset"):
            self._render_audio_panel()
            self._render_grid()
            self._render_statusbar()
            if self.scene == "confirm_reset":
                self._render_confirm_reset()
        elif self.scene == "summary":
            self._render_summary()

        pygame.display.flip()

    # ── SUB-RENDERS ───────────────────────────────────────────────────────────

    def _render_audio_panel(self):
        pygame.draw.rect(self.screen, C_PANEL, (0, 0, WIN_W, AUDIO_PANEL_H))
        pygame.draw.line(self.screen, C_DIVIDER, (0, AUDIO_PANEL_H), (WIN_W, AUDIO_PANEL_H), 1)
        # Título + toggle de idioma pegado a su derecha
        title_surf = self.font_lg.render(t("app_title"), True, C_HIGHLIGHT)
        self.screen.blit(title_surf, (16, 12))
        lang_surf = self.font_md.render("ES | EN", True, C_TEXT)
        lx = 16 + title_surf.get_width() + 14
        self.screen.blit(lang_surf, (lx, 16))
        self.lang_toggle = pygame.Rect(lx, 16, lang_surf.get_width(), lang_surf.get_height())
        # Timer, no longer used due to loop implementation
        #timer_str = f"{t('audio_panel.timer_label')} {self.elapsed:.1f}s"
        #self.screen.blit(self.font_md.render(timer_str, True, C_SUBTEXT), (16, 42))
        # Botones
        bw, bh = 100, 32
        bx = WIN_W - 340
        by = 28
        self.btn_replay = pygame.Rect(bx,       by, bw, bh)
        self.btn_loop   = pygame.Rect(bx + 110, by, bw, bh)
        self.btn_mute   = pygame.Rect(bx + 220, by, bw, bh)
        self._draw_btn(self.btn_replay, t("audio_panel.btn_replay"), active=False)
        self._draw_btn(self.btn_loop,   t("audio_panel.btn_loop"),   active=self.loop_audio)
        self._draw_btn(self.btn_mute,   t("audio_panel.btn_mute"),   active=self.muted)
        hint = self.font_sm.render(t("audio_panel.hint_keys"), True, C_SUBTEXT)
        self.screen.blit(hint, (bx, by + 38))
        # Reset link — discreto, esquina inferior derecha
        reset_surf = self.font_sm.render(t("reset.link_text"), True, C_RESET)
        rx = WIN_W - reset_surf.get_width() - 12
        ry = AUDIO_PANEL_H - reset_surf.get_height() - 4
        self.screen.blit(reset_surf, (rx, ry))
        self.reset_link = pygame.Rect(rx, ry, reset_surf.get_width(), reset_surf.get_height())

    def _render_grid(self):
        available_set = set(self.available)
        mouse_pos     = pygame.mouse.get_pos()
        step          = PORTRAIT_SIZE + PORTRAIT_PAD

        for role, ry in self.role_label_y.items():
            color = ROLE_COLORS[role]
            label = self.font_sm.render(t(f"roles.{role}"), True, color)
            self.screen.blit(label, (10, ry + 3))
            pygame.draw.line(self.screen, color,
                             (10 + label.get_width() + 6, ry + 10),
                             (WIN_W - 10, ry + 10), 1)

        for name, rect in self.grid_rects.items():
            portrait = self.portraits.get(name)
            if not portrait:
                continue

            hovered   = rect.collidepoint(mouse_pos) and not self.feedback
            is_correct = self.feedback and self.feedback["correct"] and name == self.current_hero
            is_wrong   = self.feedback and not self.feedback["correct"] and name == self.feedback["name"]

            if is_correct:
                pygame.draw.rect(self.screen, C_CORRECT,   rect.inflate(6, 6), border_radius=5)
            elif is_wrong:
                pygame.draw.rect(self.screen, C_WRONG,     rect.inflate(6, 6), border_radius=5)
            elif hovered:
                pygame.draw.rect(self.screen, C_HIGHLIGHT, rect.inflate(4, 4), border_radius=4)

            self.screen.blit(portrait, rect)

    def _render_statusbar(self):
        y0 = WIN_H - STATUSBAR_H
        pygame.draw.rect(self.screen, C_PANEL, (0, y0, WIN_W, STATUSBAR_H))
        pygame.draw.line(self.screen, C_DIVIDER, (0, y0), (WIN_W, y0), 1)

        total   = len(self.session)
        correct = sum(1 for r in self.session if r["correct"])
        text = (f"{t('statusbar.session_progress', current=total, total=SESSION_LENGTH)}   "
                f"{t('statusbar.correct', n=correct)}   "
                f"{t('statusbar.wrong',   n=total - correct)}")
        self.screen.blit(self.font_sm.render(text, True, C_SUBTEXT), (16, y0 + 9))

        # Dots de progreso
        for i in range(SESSION_LENGTH):
            color = C_DIVIDER
            if i < total:
                color = C_CORRECT if self.session[i]["correct"] else C_WRONG
            cx = WIN_W - 20 - (SESSION_LENGTH - i) * 18
            pygame.draw.circle(self.screen, color, (cx, y0 + STATUSBAR_H // 2), 6)

    def _render_summary(self):
        summary = get_summary(self.session)
        cx, cy  = WIN_W // 2, WIN_H // 2

        pygame.draw.rect(self.screen, C_PANEL,
                         pygame.Rect(cx - 220, cy - 180, 440, 370), border_radius=12)

        hardest_key  = "summary.hardest" if summary["hardest"] else "summary.hardest_none"
        hardest_val  = summary["hardest"] or ""

        lines = [
            (t("summary.title"),                                         self.font_lg, C_HIGHLIGHT, -135),
            (t("summary.subtitle"),                                      self.font_md, C_SUBTEXT,   -100),
            (t("summary.hits",     correct=summary["correct"],
                                   total=summary["total"]),              self.font_lg, C_TEXT,       -55),
            (t("summary.accuracy", pct=summary["accuracy"]),             self.font_lg,
             C_CORRECT if summary["accuracy"] >= 70 else C_WRONG,        -15),
            (t("summary.avg_time", seconds=summary["avg_time"]),         self.font_md, C_SUBTEXT,    25),
            (t(hardest_key,        name=hardest_val),                    self.font_md, C_SUBTEXT,    55),
        ]
        for text, font, color, dy in lines:
            surf = font.render(text, True, color)
            self.screen.blit(surf, surf.get_rect(center=(cx, cy + dy)))

        bw, bh = 160, 40
        self.btn_continue = pygame.Rect(cx - bw - 10, cy + 105, bw, bh)
        self.btn_quit     = pygame.Rect(cx + 10,       cy + 105, bw, bh)
        self._draw_btn(self.btn_continue, t("summary.btn_continue"), active=True)
        self._draw_btn(self.btn_quit,     t("summary.btn_quit"),     active=False)

    def _render_confirm_reset(self):
        """Overlay de confirmación de reset sobre el juego."""
        overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        cx, cy = WIN_W // 2, WIN_H // 2
        pygame.draw.rect(self.screen, C_PANEL,
                         pygame.Rect(cx - 180, cy - 70, 360, 160), border_radius=10)

        msg = self.font_md.render(t("reset.confirm_text"), True, C_TEXT)
        self.screen.blit(msg, msg.get_rect(center=(cx, cy - 30)))

        bw, bh = 130, 36
        self.btn_reset_yes = pygame.Rect(cx - bw - 8, cy + 10, bw, bh)
        self.btn_reset_no  = pygame.Rect(cx + 8,       cy + 10, bw, bh)
        self._draw_btn(self.btn_reset_yes, t("reset.btn_yes"), active=False)
        self._draw_btn(self.btn_reset_no,  t("reset.btn_no"),  active=True)

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _draw_btn(self, rect: pygame.Rect, label: str, active: bool = False):
        color = C_HIGHLIGHT if active else C_DIVIDER
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        surf = self.font_sm.render(label, True, C_BG if active else C_TEXT)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    # ── LOOP ──────────────────────────────────────────────────────────────────

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

    def _quit(self):
        save_data(self.data)
        pygame.quit()
        sys.exit()


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = HeroStep()
    app.run()

