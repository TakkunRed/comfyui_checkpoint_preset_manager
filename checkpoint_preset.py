import os
import json
import shutil
import threading
import comfy.samplers

try:
    import folder_paths
except ImportError:  # ComfyUI 外（テスト等）
    folder_paths = None

_LEGACY_PRESET_FILE = os.path.join(os.path.dirname(__file__), "presets.json")
_LOCK = threading.Lock()


def _preset_file():
    """プリセットの保存先。ノードのフォルダ外（ComfyUI の user ディレクトリ）に置き、更新で消えないようにする"""
    base = None
    if folder_paths is not None:
        getter = getattr(folder_paths, "get_user_directory", None)
        base = getter() if getter else os.path.join(getattr(folder_paths, "base_path", ""), "user")
    if not base:
        return _LEGACY_PRESET_FILE
    return os.path.join(base, "checkpoint_preset_manager", "presets.json")


def _norm_key(name):
    """OS 間でパス区切りが違っても同じモデルとして扱う"""
    return str(name).strip().replace("\\", "/")


def _load_presets(path):
    """読み込み。無い・壊れている場合は空として扱う（壊れたファイルは .bak に退避）"""
    if not os.path.exists(path) and path != _LEGACY_PRESET_FILE and os.path.exists(_LEGACY_PRESET_FILE):
        path_to_read = _LEGACY_PRESET_FILE  # 旧バージョンの保存先から引き継ぐ
    else:
        path_to_read = path
    if not os.path.exists(path_to_read):
        return {}
    try:
        with open(path_to_read, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("presets.json のルートがオブジェクトではありません")
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        try:
            shutil.copyfile(path_to_read, path_to_read + ".bak")
        except OSError:
            pass
        print(f"[CheckpointPresetManager] presets.json を読めませんでした（{path_to_read}.bak に退避）: {e}")
        return {}
    presets = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            presets[_norm_key(k)] = v
    return presets


def _save_presets(path, presets):
    """一時ファイルに書いてから置き換える（書き込み中断でファイルが壊れないように）"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)


def _coerce(value, cast, default):
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


class CheckpointPresetNode:
    @classmethod
    def INPUT_TYPES(s):
        samplers = comfy.samplers.KSampler.SAMPLERS
        schedulers = comfy.samplers.KSampler.SCHEDULERS
        return {
            "required": {
                "ckpt_name": ("STRING", {"default": ""}),
                "mode": (["use_preset", "use_ui"], {"default": "use_preset"}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "sampler_name": (samplers, {"default": "euler"}),
                "scheduler": (schedulers, {"default": "normal"}),
                "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "save": ("BOOLEAN", {"default": False}),
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
            "optional": {
                "memo": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "*", "*", "INT", "INT", "STRING")
    RETURN_NAMES = ("steps", "cfg", "sampler_name", "scheduler", "width", "height", "memo")
    FUNCTION = "manage_presets"
    CATEGORY = "utils"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(s, **kwargs):
        # 他のノードや手編集でプリセットが変わったとき、キャッシュされた出力を使わない
        try:
            st = os.stat(_preset_file())
            return f"{st.st_mtime_ns}:{st.st_size}"
        except OSError:
            return ""

    def manage_presets(self, ckpt_name, mode, steps, cfg, sampler_name, scheduler, width, height, save, memo=None, **kwargs):
        path = _preset_file()
        key = _norm_key(ckpt_name)
        safe_memo = memo if memo is not None else ""

        with _LOCK:
            presets = _load_presets(path)

            # 保存は use_ui のとき、または use_preset でまだ未登録のときだけ。
            # （use_preset で登録済みのモデルを UI の値で上書きしない）
            save_note = ""
            if save:
                if not key:
                    save_note = "(NOT SAVED: ckpt_name is empty)"
                elif mode == "use_preset" and key in presets:
                    save_note = "(SAVE SKIPPED: set mode to use_ui to overwrite)"
                else:
                    presets[key] = {
                        "steps": steps, "cfg": cfg,
                        "sampler_name": sampler_name, "scheduler": scheduler,
                        "width": width, "height": height,
                        "memo": safe_memo
                    }
                    _save_presets(path, presets)
                    save_note = "(SAVED!)"

        current_mode = "UI"
        if mode == "use_preset" and key in presets:
            p = presets[key]
            current_mode = "PRESET"
            res_steps = _coerce(p.get("steps", steps), int, steps)
            res_cfg = _coerce(p.get("cfg", cfg), float, cfg)
            res_sampler = p.get("sampler_name", sampler_name)
            res_scheduler = p.get("scheduler", scheduler)
            res_width = _coerce(p.get("width", width), int, width)
            res_height = _coerce(p.get("height", height), int, height)
            res_memo = p.get("memo", safe_memo)
            if not isinstance(res_memo, str):
                res_memo = safe_memo
        else:
            res_steps, res_cfg = steps, cfg
            res_sampler, res_scheduler = sampler_name, scheduler
            res_width, res_height = width, height
            res_memo = safe_memo

        memo_line = res_memo.strip().split('\n')[0] if res_memo.strip() else ''
        memo_first_line = memo_line[:30] + ('...' if len(memo_line) > 30 or '\n' in res_memo.strip() else '')
        ckpt_label = key.rsplit("/", 1)[-1] if key else "(empty)"
        if len(ckpt_label) > 40:
            ckpt_label = ckpt_label[:37] + "..."
        status_msg = f"MODE: {current_mode} {save_note}\nCkpt: {ckpt_label}\nSteps: {res_steps} / CFG: {res_cfg}\nSampler: {res_sampler} / Sched: {res_scheduler}\nSize: {res_width}x{res_height}\nMemo: {memo_first_line}"

        return {
            "ui": {"status_text": [status_msg]},
            "result": (res_steps, res_cfg, res_sampler, res_scheduler, res_width, res_height, res_memo)
        }

NODE_CLASS_MAPPINGS = {"CheckpointPresetNode": CheckpointPresetNode}
NODE_DISPLAY_NAME_MAPPINGS = {"CheckpointPresetNode": "Checkpoint Preset Manager"}
