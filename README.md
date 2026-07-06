# ✦ 異世界魔法石工坊 — Isekai Gemcraft

模擬真實寶石切割機的網頁小遊戲。單一 HTML 檔,零 build、零安裝。

**▶ 線上遊玩:部署到 GitHub Pages 後,網址是 `https://<帳號>.github.io/<repo名>/`**

## 玩法

選晶系(可選切割圖紙)→ 傾斜石頭設角度/方位(96 齒分度盤)→ 設深度止停 → 盲切 → 拋光 → 中二鑑定 → 寶石鏟結算入盤。

- **圖紙模式**:5 套內建切割圖紙,照真實 faceting diagram 的角度+index+深度施工——
  初陽八角(教學 17 面)、標準圓明亮式 SRB 57 面、八角階梯 Asscher 49 面、
  迴環重瓣 Portuguese 97 面、三稜 Trillion 16 面
- **深度止停**:壓到設定深度自動停手,鬆開切在精確平面,同位重切零損耗
- **魔法陣列快切**:一鍵切完當前 tier 剩餘對稱位
- **方位尺羅盤**:度數環+目標齒位提示,搭配導覽器(top view)即時看對稱性
- **自由模式**:純盲切手感,壓越久切越深,鬆開才揭曉
- **蒐集**:每顆石頭(含廢案)拍縮圖入盤,一天一鏟,可標⭐、匯出/匯入 JSON 存檔
- **新手導覽**:圖紙模式第一次選石自動跳教學提示,跟著實際操作走
- **手機版**:直向排版+觸控操作(單指轉視角/雙指縮放),橫向也堪用
- **明暗雙主題**:預設暗色教堂光氛圍,可切亮色 liquid-glass 主題
- 全程序化音效(WebAudio),無外部音檔

## 技術

- Three.js r128(CDN),切割核心 = 凸多面體半空間裁切(非 voxel/CSG 套件)
- 機台 3D 模型:Blender 程序化生成(`machine_model/build_machine.py`),GLB base64 內嵌;
  標題畫面定鏡看機台運轉(轉盤/魔法陣/分度輪),點擊進切割介面
- 存檔:localStorage(僅本機;跨機用遊戲內匯出/匯入)

## 本機開發

雙擊 `gemcraft.html` 即可玩。改完 Ctrl+R。開發交接文件見 `CLAUDE.md`(程式地圖在第 6 節,
加新切型的完整方法論見 `新增切型指南.md`)。

## 素材出處

- 切工形狀 icon 取自 [JewelCraft](https://github.com/mrachinskiy/jewelcraft)(Mikhail Rachinskiy, GPL-3.0)
- 音效全為 WebAudio 程序化生成,無外部音檔

---
🤖 與 [Claude Code](https://claude.com/claude-code) 協作開發
