# ComfyUI [comfyui_checkpoint_preset]

checkpointごとに推奨されるsteps,cfg,sampler_name,schedulerがあります。
これを都度設定するのは面倒なので、checkpointごとに、steps,cfg,sampler_name,scheduler,width,height
をプリセットすることで、checkpointを切り替えたときの手間を省きます

## 💡 特徴
- [特徴1]checkpointごとにsteps,cfg,sampler_name,scheduler,width,heightを保存可能
- [特徴2]checkpointごとに自動的にsteps,cfg,sampler_name,schedulerをKSamplerへ連携
- [特徴3]width,heightの連携、memoの保存が可能。mmemoも出力可能なので、ほかの設定値を保存、連携に使うことも可能

## 🖼️ サンプル
![Sample Workflow](example.png)
*ここにこのノードを使用したワークフロー画像を配置*

## 🛠️ インストール方法

### ComfyUI-Manager でインストール (推奨)
1. ComfyUI-Manager を開く
2. "Install Custom Nodes" をクリック
3. "comfyui_checkpoint_preset" を検索
4. "Install" をクリックして再起動

### 手動インストール
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/[ユーザー名]/[リポジトリ名].git
cd comfyui_checkpoint_preset

### ライセンス
Apache 2.0