import os
import json
import comfy.samplers

PRESET_FILE = os.path.join(os.path.dirname(__file__), "presets.json")

class CheckpointPresetNode:
    @classmethod
    def INPUT_TYPES(s):
        samplers = comfy.samplers.KSampler.SAMPLERS
        schedulers = comfy.samplers.KSampler.SCHEDULERS
        return {
            "required": {
                "ckpt_name": ("STRING", {"forceInput": True}),
                "mode": (["use_preset", "use_ui"], {"default": "use_preset"}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1, "round": 0.01}),
                "sampler_name": (samplers, {"default": "euler"}),
                "scheduler": (schedulers, {"default": "normal"}),
                # --- 追加項目1：解像度 ---
                "width": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "height": ("INT", {"default": 512, "min": 64, "max": 8192, "step": 8}),
                "save": ("BOOLEAN", {"default": False}), 
            },
            # --- 追加項目2：備忘録（マルチラインテキスト） ---
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
            "optional": {
                # JS側でTextAreaに変換するため、ここではSTRINGとして定義
                "memo": ("STRING", {"default": "", "multiline": True}), 
            }
        }

    # 出力ポートも拡張
    RETURN_TYPES = ("INT", "FLOAT", "*", "*", "INT", "INT", "STRING")
    RETURN_NAMES = ("steps", "cfg", "sampler_name", "scheduler", "width", "height", "memo")
    FUNCTION = "manage_presets"
    CATEGORY = "utils"
    OUTPUT_NODE = True

    def manage_presets(self, ckpt_name, mode, steps, cfg, sampler_name, scheduler, width, height, save, memo=None, **kwargs):
        if not os.path.exists(PRESET_FILE):
            with open(PRESET_FILE, "w") as f: json.dump({}, f)
        
        with open(PRESET_FILE, "r") as f: presets = json.load(f)

        # デフォルト値の設定（memoがNoneの場合の空文字列化を含む）
        safe_memo = memo if memo is not None else ""

        is_saved = False
        if save:
            # すべての項目をJSONに保存
            presets[ckpt_name] = {
                "steps": steps, "cfg": cfg, 
                "sampler_name": sampler_name, "scheduler": scheduler,
                "width": width, "height": height,
                "memo": safe_memo # 備忘録も保存
            }
            with open(PRESET_FILE, "w") as f: 
                json.dump(presets, f, indent=4)
            is_saved = True

        current_mode = "UI"
        if mode == "use_preset" and ckpt_name in presets:
            p = presets[ckpt_name]
            current_mode = "PRESET"
            # JSONから値を読み込む（memoのデフォルト値処理を追加）
            res_steps = p.get("steps", steps)
            res_cfg = p.get("cfg", cfg)
            res_sampler = p.get("sampler_name", sampler_name)
            res_scheduler = p.get("scheduler", scheduler)
            res_width = p.get("width", width)
            res_height = p.get("height", height)
            res_memo = p.get("memo", safe_memo) # JSONにmemoがあれば読み込む
        else:
            # use_ui または プリセットなし
            res_steps, res_cfg = steps, cfg
            res_sampler, res_scheduler = sampler_name, scheduler
            res_width, res_height = width, height
            res_memo = safe_memo

        # 解像度とメモを含めたステータスメッセージを作成
        # memoは長い場合があるので、1行目だけステータスに表示
        memo_first_line = res_memo.split('\n')[0][:30] + '...' if res_memo else ''
        status_msg = f"MODE: {current_mode} {'(SAVED!)' if is_saved else ''}\nSteps: {res_steps} / CFG: {res_cfg}\nSampler: {res_sampler} / Sched: {res_scheduler}\nSize: {res_width}x{res_height}\nMemo: {memo_first_line}"

        return {
            "ui": {"status_text": [status_msg]}, 
            "result": (res_steps, res_cfg, res_sampler, res_scheduler, res_width, res_height, res_memo)
        }

NODE_CLASS_MAPPINGS = {"CheckpointPresetNode": CheckpointPresetNode}
NODE_DISPLAY_NAME_MAPPINGS = {"CheckpointPresetNode": "Checkpoint Preset Manager"}