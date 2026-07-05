# ✦ 異世界魔法石工坊 — Isekai Gemcraft

模擬真實寶石切割機的網頁小遊戲。單一 HTML 檔,零 build、零安裝。

**▶ 線上遊玩:部署到 GitHub Pages 後,網址是 `https://<帳號>.github.io/<repo名>/`**

## 玩法

選晶系(可選切割圖紙)→ 傾斜石頭設角度/方位(96 齒分度盤)→ 設深度止停 → 盲切 → 拋光 → 中二鑑定 → 寶石鏟結算入盤。

- **圖紙模式**:內建「初陽八角」教學圖紙與「標準圓明亮式 57 面」(SRB),照真實 faceting diagram 的角度+index+深度施工
- **自由模式**:純盲切手感,壓越久切越深,鬆開才揭曉
- **蒐集**:每顆石頭(含廢案)拍縮圖入盤,一天一鏟,可標⭐、匯出/匯入 JSON 存檔

## 技術

- Three.js r128(CDN),切割核心 = 凸多面體半空間裁切(非 voxel/CSG 套件)
- 機台 3D 模型:Blender 程序化生成(`machine_model/build_machine.py`),GLB base64 內嵌
- 存檔:localStorage(僅本機;跨機用遊戲內匯出/匯入)

## 本機開發

雙擊 `gemcraft.html` 即可玩。改完 Ctrl+R。開發交接文件見 `CLAUDE.md`。

---
🤖 與 [Claude Code](https://claude.com/claude-code) 協作開發
