"""Material trace: re-runs a room's own builder (tools/room_art/build_<id>.py) with pixel.Canvas
instrumented so every pixel remembers which painting functions put it there, e.g.
"sky", "far_campus", "lawn>grass_tuft", "norlin_portico>roof_edge".

The season pass reads these labels instead of guessing materials from colour alone: snow goes on
what the builder called a lawn, a roof or a ledge; leaves change on what it called a tree.

    trace_room("N01") -> {"background.png": (rgba uint8, labels int32, names list[str], tint int32), ...}

Every image the builder saves through Canvas.save is captured (background, props, battle). Nothing
is written into the game: the builder runs against a scratch project folder. The captured pixels
are checked against the committed PNGs so a stale trace can never be used."""
import importlib
import os
import sys
import tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM_ART = os.path.abspath(os.path.join(HERE, "..", "room_art"))
if ROOM_ART not in sys.path:
    sys.path.insert(0, ROOM_ART)
import pixel  # noqa: E402

SKIP_FILES = {"pixel.py"}
SKIP_FUNCS = {"<module>", "build", "main", "build_room", "<lambda>", "<listcomp>", "<genexpr>", "<dictcomp>"}

_names = ["", "?"]
_index = {"": 0, "?": 1}


def _label_id(name):
    i = _index.get(name)
    if i is None:
        i = len(_names)
        _names.append(name)
        _index[name] = i
    return i


def _stack():
    """'outer>inner' chain of the room_art painting functions currently running."""
    f = sys._getframe(2)
    chain = []
    while f is not None:
        fn = f.f_code.co_filename
        if fn.startswith(ROOM_ART) and os.path.basename(fn) not in SKIP_FILES:
            name = f.f_code.co_name
            if name not in SKIP_FUNCS:
                chain.append(name)
        f = f.f_back
    return ">".join(reversed(chain))


def _ensure(cv):
    if not hasattr(cv, "_lab") or cv._lab.shape != (cv.h, cv.w):
        cv._lab = np.zeros((cv.h, cv.w), np.int32)
        cv._tint = np.zeros((cv.h, cv.w), np.int32)
        cv._gen = np.zeros((cv.h, cv.w), np.int64)


_orig = {}


def _mark(cv, mask_or_slice, alpha, label=None):
    _ensure(cv)
    lid = _label_id(label if label is not None else _stack())
    _gen[0] += 1
    cv._gen[mask_or_slice] = _gen[0]
    if alpha >= 0.6:
        cv._lab[mask_or_slice] = lid
    else:
        cv._tint[mask_or_slice] = lid


_live = []          # weakrefs of canvases
_gen = [0]          # bumps on every traced primitive write
_snaps = {}         # frame id -> (gen at call, [(canvas ref, snapshot)])
MAX_DEPTH = 3


def _depth(frame):
    d = 0
    while frame is not None:
        if frame.f_code.co_filename.startswith(ROOM_ART) and os.path.basename(frame.f_code.co_filename) not in SKIP_FILES:
            d += 1
        frame = frame.f_back
    return d


def _profile(frame, event, arg):
    """Pixels a painting function changed by writing straight into canvas.a (not through the
    primitives) are credited to that function when it returns."""
    if event not in ("call", "return"):
        return
    code = frame.f_code
    fn = code.co_filename
    if not fn.startswith(ROOM_ART) or os.path.basename(fn) in SKIP_FILES:
        return
    if event == "call":
        if _depth(frame) > MAX_DEPTH:
            return
        snaps = []
        for ref in _live:
            cv = ref()
            if cv is not None and cv.a.size <= 4 * 1100 * 1100:
                snaps.append((ref, cv.a.copy()))
        _gen[0] += 1
        _snaps[id(frame)] = (_gen[0], snaps)
    else:
        rec = _snaps.pop(id(frame), None)
        if rec is None:
            return
        g0, snaps = rec
        name = code.co_name
        chain = []
        f = frame
        while f is not None:
            if f.f_code.co_filename.startswith(ROOM_ART) and os.path.basename(f.f_code.co_filename) not in SKIP_FILES \
                    and f.f_code.co_name not in SKIP_FUNCS:
                chain.append(f.f_code.co_name)
            f = f.f_back
        label = ">".join(reversed(chain))
        if not label:
            return
        for ref, snap in snaps:
            cv = ref()
            if cv is None or cv.a.shape != snap.shape:
                continue
            _ensure(cv)
            changed = np.any(cv.a != snap, axis=-1) & (cv._gen < g0)
            if changed.any():
                solid = changed & (cv.a[..., 3] >= 0.6)
                lid = _label_id(label)
                cv._lab[solid] = lid
                _gen[0] += 1
                cv._gen[changed] = _gen[0]


def install():
    if _orig:
        return
    import weakref
    C = pixel.C
    Canvas = pixel.Canvas
    _orig.update({k: getattr(Canvas, k) for k in ("__init__", "px", "rect", "fill_mask", "paste", "save")})

    def init(self, *a, **k):
        _orig["__init__"](self, *a, **k)
        _ensure(self)
        _live.append(weakref.ref(self))
        if k.get("fill") is not None or (len(a) >= 3 and a[2] is not None):
            self._lab[:] = _label_id(_stack() or "fill")

    def px(self, x, y, c):
        _orig["px"](self, x, y, c)
        if 0 <= x < self.w and 0 <= y < self.h:
            _mark(self, (y, x), C(c)[3])

    def rect(self, x, y, w, h, c):
        _orig["rect"](self, x, y, w, h, c)
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x0 < x1 and y0 < y1:
            _mark(self, (slice(y0, y1), slice(x0, x1)), C(c)[3])

    def fill_mask(self, m, c):
        _orig["fill_mask"](self, m, c)
        _mark(self, m, C(c)[3])

    def paste(self, src, x, y):
        _orig["paste"](self, src, x, y)
        _ensure(self)
        arr = src.a if isinstance(src, Canvas) else src
        h, w = arr.shape[:2]
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        s_al = arr[y0 - y:y1 - y, x0 - x:x1 - x, 3]
        here = _stack()
        solid = s_al >= 0.6
        faint = (s_al > 0) & ~solid
        if isinstance(src, Canvas) and hasattr(src, "_lab"):
            sl = src._lab[y0 - y:y1 - y, x0 - x:x1 - x]
            # compose "paste site|sprite label"
            out = np.zeros_like(sl)
            for lid in np.unique(sl[solid]):
                out[solid & (sl == lid)] = _label_id((here + "|" + _names[lid]).strip("|"))
            reg = self._lab[y0:y1, x0:x1]
            reg[solid] = out[solid]
            _gen[0] += 1
            self._gen[y0:y1, x0:x1][s_al > 0] = _gen[0]
            self._tint[y0:y1, x0:x1][faint] = _label_id(here + "|faint")
        else:
            lid = _label_id((here + "|array") if here else "array")
            self._lab[y0:y1, x0:x1][solid] = lid
            _gen[0] += 1
            self._gen[y0:y1, x0:x1][s_al > 0] = _gen[0]
            self._tint[y0:y1, x0:x1][faint] = lid

    def save(self, path):
        _ensure(self)
        CAPTURE[os.path.basename(path)] = (
            (np.clip(self.a, 0, 1) * 255).round().astype(np.uint8), self._lab.copy(), self._tint.copy(),
            _order(self._gen))
        _orig["save"](self, path)

    Canvas.__init__ = init
    Canvas.px = px
    Canvas.rect = rect
    Canvas.fill_mask = fill_mask
    Canvas.paste = paste
    Canvas.save = save


CAPTURE = {}


def _order(gen):
    """Paint order as small dense ranks (0 = untouched background fill)."""
    u, inv = np.unique(gen, return_inverse=True)
    return inv.reshape(gen.shape).astype(np.int32)
_cache = {}


CACHE_DIR = os.environ.get("AH_TRACE_CACHE") or os.path.join(HERE, ".trace-cache")   # git-ignored


def load_trace(room, project=None):
    """The cached trace of a room (made by `python3 trace.py <ROOM> ...`), else a fresh one.
    A cached image whose pixels no longer match the committed PNG is retraced."""
    import json
    from seasonlib import PROJECT
    project = project or PROJECT
    path = os.path.join(CACHE_DIR, room + ".npz")
    if os.path.exists(path):
        z = np.load(path, allow_pickle=False)
        names = json.loads(str(z["names"]))
        out = {}
        stale = False
        for key in z.files:
            if not key.endswith(":lab"):
                continue
            name = key[:-4]
            real = os.path.join(project, "assets", "art", "rooms", room, name)
            rgba = np.array(Image.open(real).convert("RGBA")) if os.path.exists(real) else None
            if rgba is None or rgba.shape[:2] != z[key].shape:
                stale = stale or rgba is not None
                continue
            if not np.array_equal(rgba, z[name + ":rgba"]):
                stale = True
            out[name] = (rgba, z[key], z[name + ":tint"], z[name + ":order"])
        if not stale:
            return out, names
    out, names = trace_room(room, project)
    save_trace(room, out, names)
    return out, list(names)


def save_trace(room, out, names):
    import json
    os.makedirs(CACHE_DIR, exist_ok=True)
    arrays = {"names": np.array(json.dumps(list(names)))}
    for name, (rgba, lab, tint, order) in out.items():
        arrays[name + ":rgba"] = rgba
        arrays[name + ":lab"] = lab
        arrays[name + ":tint"] = tint
        arrays[name + ":order"] = order
    np.savez_compressed(os.path.join(CACHE_DIR, room + ".npz"), **arrays)


def trace_room(room, project=None, verify=True):
    """Runs build_<room>.py (and build_battle_<room>.py) under the tracer; returns the captures."""
    if room in _cache:
        return _cache[room]
    install()
    from seasonlib import PROJECT
    project = project or PROJECT
    CAPTURE.clear()
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "assets", "art", "rooms", room), exist_ok=True)
        for mod in (f"build_{room.lower()}", f"build_battle_{room.lower()}"):
            if os.path.exists(os.path.join(ROOM_ART, mod + ".py")):
                m = importlib.import_module(mod)
                sys.setprofile(_profile)
                try:
                    m.build(tmp)
                finally:
                    sys.setprofile(None)
                    _snaps.clear()
    out = {}
    for name, (rgba, lab, tint, order) in CAPTURE.items():
        real = os.path.join(project, "assets", "art", "rooms", room, name)
        if verify and os.path.exists(real):
            have = np.array(Image.open(real).convert("RGBA"))
            if have.shape != rgba.shape or not np.array_equal(have, rgba):
                diff = (np.abs(have.astype(int) - rgba.astype(int)).sum(-1) > 0).mean() if have.shape == rgba.shape else 1
                if diff > 0.0005:
                    print(f"  trace {room}/{name}: rebuild differs from the committed PNG ({diff:.2%}); labels approximate")
            rgba = have if have.shape == rgba.shape else rgba
        out[name] = (rgba, lab, tint, order)
    _cache[room] = (out, _names)
    return out, _names


def label_mask(labels, names, pattern, tint=False):
    """Bool mask of pixels whose label chain matches the regex `pattern`."""
    import re
    rx = re.compile(pattern)
    hit = np.array([bool(rx.search(n)) for n in names] + [False] * 0)
    hit = np.concatenate([hit, np.zeros(max(0, labels.max() + 1 - len(hit)), bool)])
    return hit[labels]


if __name__ == "__main__":
    if sys.argv[1] == "cache":
        for room in sys.argv[2:]:
            o, n = trace_room(room)
            save_trace(room, o, n)
            print("traced", room, flush=True)
        sys.exit(0)
    room = sys.argv[1]
    caps, names = load_trace(room)
    for name, (rgba, lab, tint, order) in caps.items():
        ids, counts = np.unique(lab, return_counts=True)
        print(name, rgba.shape)
        if name == (sys.argv[2] if len(sys.argv) > 2 else "background.png"):
            for i, c in sorted(zip(ids, counts), key=lambda t: -t[1])[:80]:
                print(f"   {c:7d}  {names[i]}")
