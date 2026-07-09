# 異世界魔法石工坊 — 開發交接文件 (claude.md)

> 給未來的我 / 未來的 AI session：這份是**目前實作狀態**的交接,不是原始需求。
> 原始需求規格在 `isekai_gemcraft_claude.md`(v1.0 概念文件),那份不要改,當願景參考。
> 這份 `claude.md` 是「現在做到哪、怎麼動、接下來做什麼」。

---

## 0. 一句話

模擬真實寶石切割機的網頁小遊戲,單一 HTML 檔。選晶系(+可選切割圖紙)→ 傾斜石頭設角度/方位(+深度止停)→ 盲切 → 拋光 → 中二鑑定。

**主程式：`gemcraft.html`(單檔,雙擊用瀏覽器開,需連網載 Three.js CDN)。**

**文件路由(不懂什麼,去哪找)**:
| 想知道 | 去這裡 |
|---|---|
| 程式碼在 gemcraft.html 哪裡/怎麼改 | 本文件第 6 節程式地圖 |
| 某功能怎麼實作的/當時踩過什麼坑 | `開發史.md`(搜功能名/元素 id/函式名) |
| 加新切割圖紙 | `新增切型指南.md`(可直接發包給其他模型) |
| 原始願景/概念規格 | `isekai_gemcraft_claude.md`(不要改) |
| 機台 3D 模型/預告片開場算圖 | `machine_model/`(`build_machine.py`/`intro_flythrough*.py`) |
| 預告片剪輯素材與工作流(不進 repo) | `偷偷剪片不能推上Github/01_footage/manifest.md`、`粗切填單.md` |
| 視覺風格 token/元件參考 | `..\Isekai Gemcraft Design System`(其產出先 diff 再用,見第 8 節) |

---

## 1. 怎麼跑 / 怎麼改

- **跑**：雙擊 `gemcraft.html`,或瀏覽器開檔案。改完檔案要手動 **Ctrl+R** 重新整理(本機檔案不會自動刷新)。
- **改**：全部程式在那一個 HTML 檔裡,沒有 build、沒有套件安裝。`<style>` 是樣式,`<script>` 是邏輯。
- **依賴**：只有一個 → Three.js r128(CDN `cdnjs`)。離線打不開。

---

## 2. 最重要的架構決策(別推翻,踩過坑)

### 2.1 切割算法 = 凸多面體 + 平面裁切(不是 voxel,不是 CSG library)
原始規格建議 voxel + marching cubes,**那是錯的**:切不出寶石要的鏡面平刻面,輸出是圓鈍肉塊,而且吃記憶體。

實際做法:石頭存成**凸多面體**(頂點 + 面),每一刀 = 一個半空間平面把多面體裁掉一塊。
- 核心函式 `clipSolid(solid, n, d)`：保留 `dot(n,v) <= d` 那一側,回傳新多面體。
- 精確、刻面永遠平整、刻面數無上限、不需任何 CSG 套件。
- **代價**：只能凸形,不能有內部孔洞/內含物。但 faceted 寶石本來就是凸的,無損。
- 風險:`stitchLoop`(把切面邊界縫成新面)在極端切法下理論上可能破面,目前測試沒爆,但若之後看到破面先查這裡。

### 2.2 切割機的「傾斜模型」(這是手感的核心,很重要)
真實切割機:**轉盤(lap)水平,石頭+dop 桿傾斜+自旋,壓上去**。

- `rigQuaternion()` = 只含**傾斜(角度)+ 自旋(index)**,給 **dop 桿**用,桿子永遠從上方來、**不翻面**。
- `stoneQuaternion()` = rig + **冠部時翻面 180°**(模擬重新黏石),給**石頭**用。
- 切割平面永遠是「世界的水平向下」,用 `stoneQuaternion()` 的逆轉進石頭局部座標來切。
- 所以拉角度滑桿石頭會即時傾斜、按 index 石頭會轉 —— 玩家看得到這一刀從哪切。
- **踩過的坑**:一開始把翻面也套到 dop 桿上,冠部模式桿子會插進石頭裡。記住:**桿子不翻,只有石頭翻**。

### 2.3 盲切
按住下壓鈕時畫面遮蔽(看不到切到哪),深度條隨按住時間長,鬆開才套用切割並揭曉。`MAX_DEPTH`/`DEPTH_RATE` 控制壓深速度。
2026-07 起有**時間魔法「未觀測的一刀」**:每顆石頭 3 次回溯(受試者2號誤把長按當拋光磨掉整顆石頭的回饋),用完回到不可返回的硬派本色——次數上限是張力保護,不要調成無限。

### 2.4 反覆踩到的 JS 雷:TDZ(暫時死區)
`let state=null;` 宣告在腳本中段。**任何在它之前就被呼叫、且讀取 `state` 的函式都會整支腳本報錯**(然後選石卡都生不出來,畫面卡在標題)。
→ 教訓:不要在 `let state` 宣告之前呼叫 `updateNavCam()` 之類會碰 `state` 的東西。已用靜態初始化避開。

### 2.5 深度的兩套語意(圖紙模式的核心,別混用)
- **自由模式** `doCut(depth)`:深度相對「當前最高點」(`d = dmax − depth`),每切一刀基準就變。純手感。
- **圖紙模式** `cutAtPlane(n, d)`:d 是**石頭局部座標的絕對平面距離**(真機 mast height 的類比)。
  同 tier 八刀用同一個 d → 天然完美對稱;同參數重切 = 幾何 no-op(零損耗,已驗證)。
  深度止停(`state.depthStopOn/depthStopV`,單位 %R)壓到 `pressLimit` 會自動停住,鬆手切在**精確的目標平面**(不是時間換算值);提早鬆手 = 走自由模式淺切、不勾銷。
- 全部止停邏輯 gate 在 `depthStopActive()`,自由模式路徑一行沒動。

### 2.6 圖紙資料的寶石學陷阱(踩過)
- **halves 比 mains 陡**:SRB 下腰 42° > 亭主 40.75°、上腰 40° > 冠主 34.5°。陡的刻面才會只切腰圍附近;
  反過來設(主刻面比 halves 陡)會讓 halves **整層切不到東西**或吃掉底尖。
- **index 集合必須對齒 96 鏡像對稱**:冠部翻面會鏡像方位(t→96−t),非對稱集合會冠亭對不上。
- 桌面(角度 0)自旋不影響法線 → `indices:[96], indexFree:true`。
- d 值(×R)校準過:oct8 P1=0.735(底尖剛好收攏在 −1.04R,預成形底蓋 −1.05R 被吃掉);SRB 六層見 `DIAGRAMS`。
- **垂直腰刀 `side:'girdle'`**(角度 90°):塑八角/三角等直邊腰圍。相鄰兩刀交角頂點 = d/cos(半夾角),必須 **< 1.0R** 否則與 24 角柱側面共面(退化風險):八角 d≤0.90(頂點 0.974R)、三角 d≤0.49(頂點 0.98R)。
- **軸向預算**:亭部 −1.05R、**冠部只有 +0.55R**——冠部各 tier 平面在軸心的高度(d/cosθ)可以超過 0.55(那層只切外圈環帶),但**桌面 d 必須 < 0.55**,多層冠 tier 的斷點高度要全程追蹤。d 的幾何公式與逐 tier 鏈式計算見 `新增切型指南.md`。

---

## 3. 目前實作了什麼(一句話總覽)

> ⚠ 各功能的實作細節、改動位置、驗證紀錄、踩坑教訓,全部搬去 **`開發史.md`**(同目錄)——
> 改到哪個功能,先去那裡搜功能名再動手。這裡只回答「遊戲現在有什麼」。

核心迴圈:7 晶系選石 → 傾斜切割機(角度滑桿/96 齒 index/翻面) → 盲切(按住下壓、鬆手揭曉) → 三段 lap → 中二結算。

- **切割輔助**:導覽器 top view、方位尺羅盤(逆時針,已校準)、折數快捷、深度止停(mast height)、時間魔法回溯 3 次(「未觀測的一刀」)、✂ 預成形
- **圖紙模式**:5 份圖紙(oct8/SRB57/Asscher49/Portuguese97/Trillion16)+圖紙預成形(24 角柱標準粗胚)+指令表逐 tier 帶入+勾銷防呆+⚡魔法陣列快切+結算稽核(`auditDiagram`);`#dev` 校準工具(`__diag.run/dump`)
- **視覺**:機台 GLB(base64 內嵌)+標題演出、教堂光氛圍、附魔轉色 18 色(含 6 雙色漸層)、淺色石稜線描邊、環境亮度滑桿、亮色玻璃主題切換
- **平台**:手機版直向優先(觸控完整支援)、in-app WebView 視口修正、i18n 中英即時切換
- **存檔**:localStorage Vault+蒐集頁(⬇匯出/⬆匯入)、鏟寶石結算演出+hero 旋轉
- **教學**:教學卡、魔法快切導覽(coachmark)、音效(全程序化 WebAudio `SFX`)
- **推廣**:landing page(`index.html`:特色卡特效/寶石互動層/影片框紫焰)、`#shot` 截圖旗標、Blender 預告片開場運鏡(`machine_model/intro_flythrough*.py`,tight 版已裁定採用)、GPL-3.0+CONTRIBUTING+issue 模板

---

## 4. 待確認 / 已知小問題

- ~~方位尺金針的轉向與零點~~ **已校準**(2026-07 實測+修正):原本確實**鏡像且有偏移**——把「index t 的刻面切完後在導覽器畫面上的實際方位」投影到 topCam 螢幕座標實測,亭部 actual=270−deg、冠部 actual=90−deg(deg=t×3.75,金針卻畫在 +deg)。修法兩件一組:①`updateNavCam` 的 `topCam.up` 從石頭局部 +Z 改 **−X**(實測這個軸讓亭/冠兩側都變成 actual=−deg,同一公式不用分支);②羅盤四件套(度數環/金針/青點/金環)全改**逆時針刻度**,共用新 helper `compassXY(deg,r)`,金針 `rotate(−deg)`——從研磨台側(下方)看石頭,方位天生鏡像,逆時針才是物理正確。驗證:螢幕投影數值全對齊(亭/冠各 4 個 index)+垂直腰刀直邊視覺比對(金針正指切出的平邊)+五份圖紙 `#dev` 迴歸 100%、偏差 0°。**注意**:console 的 index 小錶盤 `#idxNeedle` 仍順時針——它代表機台分度輪(機構示意),不是畫面空間,刻意不同步;導覽器畫面因 up 軸換了會比舊版整體轉 90°(純視覺,無存檔參照)。
- `clipSolid` / `stitchLoop` 的極端切法破面風險(見 2.1)。SRB 57 面 + 24 腰稜(81 面)壓測通過,沒破面。**圖紙模式風險趨近於零**(角度/深度/index 都鎖在表定值,等於全跑過壓測);**自由切割沒有這層保護**——玩家可以用任意角度+任意深度連續下壓,沒人校過那個組合空間,是「破圖」回報最可能的來源(2026-07 用戶朋友玩舊版時發生)。目前只做了 UX 層防呆:選石畫面自由切割卡加「🔥匠人精神」警示角標(`.hardBadge`,見選石畫面 `#diagramRow` 第一張卡)區分於圖紙的「⭐推薦入門」,提示新手不要預設選它;**幾何層本身沒加防呆**,真的極端切法(例如同角度貼著切到只剩極薄一層)理論上仍可能讓 `stitchLoop` 縫不出封閉面。若之後再收到破圖回報,先問清楚是「幾何真的破洞/面缺角」還是「只是切得對稱很差、形狀很醜」——只有前者才是這裡要查的 bug。
- 結算估價/評級公式是隨手抓的(`showResult()` 裡),數值平衡沒調過。圖紙模式成品率天生偏低(預成形吃掉很多料,約 10–15%),評語 <15% 那句會常駐,要嫌煩就調門檻。
- 圖紙模式的深度止停滑桿玩家可以手動亂調(離開表定值),切了照樣不勾銷——是特性不是 bug(機器不會救你)。**提示已補**(2026-07):`recordDiagramCut` 對不上任何 tier 時 `flashWarn`「⚠ 角度或止停深度不在圖紙表定值——這刀不計入圖紙(點 tier 列可自動帶入)」;成功勾銷時 `clearWarn()` 立即清掉殘留警告(不等 2.5s 淡出)。
- `preformDiagram()` 假設原石對 y=0 上下大致對稱(現有 8 個 builder 都滿足);之後若加不對稱原石要回頭看腰圍定位(`c=0.25R` 那段)。
- **非圓截面原石的 R 陷阱**(鑽石/石榴石踩過):八面體水平截面是方形,「整體最小徑向支撐」≠「腰圍平面實際內半徑」,R 抓太大會讓冠部整層落空、成品破碎。`preformDiagram` 現在會切腰圍薄片量實際內半徑,短缺就縮 R 迭代重做(最多 3 輪)。八大晶系 × SRB57 已全掃 57/57。
- **hero/縮圖過曝**:shotR 掛 ACESFilmic tone mapping(exposure 0.85)+上下雙 DirectionalLight;白鑽這種淺色石驗過 0% 飽和像素。
- **儲存只在 localStorage**:換電腦/換瀏覽器/清快取就消失;蒐集頁只存縮圖+參數,無法重建 3D 模型(詳情頁有註明)。跨機用蒐集頁的「⬇匯出/⬆匯入存檔」(JSON,匯入=合併去重)。
- **一天=一盤**:`session.vid='s_'+日期`,同日各爐自動併盤;`Vault.mergeByDate()` 在 load 時跑,也是舊資料遷移。
- **標題字的坑**:`.tsTitle` 拆字後父層 `background-clip:text` 不會畫進 span → 漸層要掛在每個 `.tsChar` 上;空白字元用 NBSP 否則 inline-block 會塌。
- **已上 git**(2026-07):repo 在專案根目錄,`參考圖/`(他人 IG 素材)與 `.claude/settings.local.json` 已 gitignore。部署走 GitHub Pages(純靜態,無 build,`index.html` 轉跳 `gemcraft.html`),用戶用 GitHub Desktop 推送。Pages 偶發 `Deployment failed` 多為 GitHub Actions 暫時性抽風,手動 Re-run 即可。
- **PMREM envMap 綁 renderer**(r128):`makeEnvTexture(renderer)` 與 `makeEnvTexture(shotR)` 各自產,不能共用,刪掉 shotR 那份 hero/縮圖會變黑。

---

## 5. 接下來想加的(原規格有、還沒做)

優先級是用戶醒來再定,以下是池子:

- ~~切割圖紙 / 目標範本~~ **已做**;~~擴充圖紙庫~~ **已做第一輪**(2026-07 加了 Asscher 49 / Portuguese 97 / Trillion 16,共 5 份,見 開發史.md)。**再加新切型看 `新增切型指南.md`**(完整格式/數學/校準流程/授權注意,可直接發包給其他模型)。
- ~~魔法陣列快切~~ **已做**(`#arrayCutBtn`)。GemCutter 的 mirror split/offset 進階模式還沒做,要做花式切割再說。
- **附魔系統**:指定石種名稱 + 處理方式(加熱/輻照/充填/擴散/鍍膜),並用附魔當「清除 dop 蠟痕、恢復透明度」的敘事理由。(轉色部分已做,見 🎨 附魔轉色)
- **Minecraft 第一人稱選石手**:選石畫面目前是純卡片,沒有持 dop 的第一人稱手。
- **多種 index 齒數(80 齒)**:5 折對稱需要(96 不整除 5)。工程量與改動點分析見 `新增切型指南.md` 第 6 節。
- ~~音效~~ **已做**(全程序化 WebAudio `SFX`,見程式地圖)。
- ~~研磨機模型導入~~ **已導入**(細節見 開發史.md)。`machine_model/` 資產:`gem_faceting_machine.blend`(含魔法陣閃爍動畫 fr1-250)、`.glb`、`build_machine.py`(全程序化,改參數重跑 25 秒重生一台)、`inject_glb.ps1`(重生後把 GLB 重新 base64 注入 gemcraft.html)、三張 render。
  - 模型更新流程:改 `build_machine.py` → `blender -b --factory-startup -P build_machine.py` → `inject_glb.ps1` → Ctrl+R。
  - 座標換算:Blender (x,y,z) → glTF (x,z,−y);模型 lap r=0.125m → 遊戲 lap r=2.6 → 縮放 ×20.8,root 位移 (2.08,−3.762,0)。
  - 建模心得:Blender 5.1 headless 可全自動;燈光瓦數按「燈到物距離平方」縮(0.5m 內桌面景 10W 級就夠,100W 把黑鐵洗成灰);色彩轉換 Khronos PBR Neutral 比 AgX 接近 Three.js;5.1 動畫是 slotted actions(fcurve 在 `action.layers[0].strips[0].channelbag(slot)`)。

**用戶已裁定不做**(2026-07,別再提案):
- **機台完全綁定**(石頭長在機臂上、quill=角度、分度輪=index):重構風險大,會動到 2.2 手感核心。
- **真 AI 鑑定**(接 Claude API):本地預填文字就夠,不處理 key+CORS 中介。
- **透射材質 transmission / 進階光影**:效能與幾何複雜度風險,不做。

---

## 6. 程式地圖(在 gemcraft.html 裡找東西)

| 想改什麼 | 找這個 |
|---|---|
| 晶系定義、原石形狀 | `SYSTEMS` 陣列、`buildOctahedron`/`buildPrism`/`buildBox`/`buildTriclinic` |
| 切割數學 | `clipSolid`、`cutAtPlane`(絕對平面)、`doCut`(相對深度)、`preform` |
| **圖紙資料(加新圖紙改這)** | `DIAGRAMS` 陣列(格式與陷阱見 2.6;完整方法論見 `新增切型指南.md`)+ 選石畫面 `#diagramRow` 加卡 |
| **圖紙預成形 / 標準粗胚 R** | `preformDiagram`(24 角柱、腰圍 y=0、`state.diagram.R`) |
| **深度止停** | `depthStopActive`/`depthStopD`/`updateDepthStopUI`、`startPress` 的 `pressLimit`、`animate` 的 clamp |
| **指令表面板 / tier 帶入 / 勾銷** | `renderDiagramPanel`、`activateTier`、`recordDiagramCut`、`flashWarn`/`clearWarn` |
| **陣列快切** | `#arrayCutBtn` 的 onclick |
| **圖紙結算稽核** | `auditDiagram`、`showResult` 的 `dg` 分支 |
| **#dev 校準工具** | 檔尾 `location.hash.includes('dev')` 區塊(`__diag.run`/`__diag.dump`) |
| 傾斜/自旋/翻面 | `rigQuaternion`、`stoneQuaternion`、`expectedNormal`、`setCrown`、`updateNavCam` |
| 石頭外觀/材質/lap 階段 | `LAPS`、`rebuildStone`、`buildGeometry` |
| 盲切手感 | `startPress`/`endPress`、`MAX_DEPTH`、`DEPTH_RATE`、`animate` 裡的深度條 |
| **時間魔法回溯(未觀測的一刀)** | `snapshotStone`/`undoCut`/`updateUndoUI`、HTML `#undoGroup`(操作台第 5 格);快照鉤子在 `endPress`/`arrayCutBtn`/`preform`/`preformDiagram`;次數在 `spawnStone` 的 `state.undoLeft=3`。圖示是 `.undoIcon`(inline SVG,眼睛加斜線=「未被觀測」,取代原本 ⏪ emoji——用戶嫌舊圖示不好看,inline SVG 用 `stroke="currentColor"` 自動跟 `var(--text)` 走,亮暗主題都不用另外配色) |
| **in-app WebView 視口修正** | CSS `@supports (height:100svh)` 區塊(html/body 高+body relative+左下三鈕改 absolute)、`#console` 的 `52svh` 檔 |
| **下壓鈕窄視窗被裁切(flex 擠壓 bug)** | `#pressBtn` 的 `flex-shrink:0`(根因:`overflow:hidden` 讓 flex item 失去自動最小高度保護,被 `#console` 的 `overflow-y:auto` 擠壓吃掉) |
| index / 折數 / 錶盤 | `setIndex`、`.presetRow` 的 onclick、`setActiveFold` |
| 方位尺羅盤 | `compassXY`(逆時針座標 helper,四件套共用)、`buildCompass`、`updateCompassNeedle`(rotate(−deg))、`updateCompassFold`、`updateCompassTargets`(金環);校準脈絡見第 4 節 |
| 導覽器相機 | `topCam`、`updateNavCam` |
| 結算 / 評分 / 估價 / 毒舌 | `showResult`、`GEM_NAMES` |
| 教學卡 | HTML `#tutorial`、`helpBtn`/`tutClose` |
| **魔法快切導覽(coachmark)** | `COACH_STEPS`、`coachShow`/`coachHide`/`coachPosition`、HTML `#coachMark` |
| **亮色玻璃主題 / 明暗切換** | CSS `html[data-theme="light"]` 區塊(疊加,不改暗色原規則)、JS `applyTheme`、HTML `#themeBtn` |
| **中英雙語(i18n)** | 檔頭 `UI_LANG`/`tx(zh,en)`、檔尾 `I18N_STATIC` 表+`applyStaticLang`/`applyLang`、`#langBtn`;資料欄位 `nameEn/descEn/gemEn/shapeEn`、helper `dgName/dgDesc/lapName/tierLabel`;**加新 UI 文字一律走 tx() 或 I18N_STATIC,別寫死單語** |
| **推廣頁 / 影片嵌入** | `index.html`(landing,獨立檔不影響遊戲);影片好了改裡面的 `const YT_ID=""` |
| **宣傳截圖** | URL 加 `#shot`(或 `#shot-dev`)→ `renderer.domElement.toDataURL()`;成品在 `assets/`;注意背景分頁 rAF 暫停要手動 render 一幀 |
| 對稱性評分 | `updateSymmetry` |
| **機台模型載入/換裝/動態** | `loadMachine`、`setupMachine`(lapSpin/quillPark/gearSpin 分組)、`tickMachine`、`PARK_ANGLE` |
| **氛圍(教堂環境/霧氣/光柱)** | `makeEnvScene`/`makeEnvTexture`(彩窗 envMap——**金屬材質全靠它亮**,別刪)、`fxGroup`/`tickFx`(乾冰霧+god rays)、CSS `#vignette`、`scene.fog` |
| **環境亮度(手動曝光)** | `applyExposure`、`#expBtn`/`#expRow`(leftTools);renderer/topR 是 `LinearToneMapping`(為了讓 exposure 生效,**要在第一次 render 前設**);shotR 的 ACES 是另一套,別混 |
| **下一刀資訊帶** | `#nextCutBar`、`updateNextCutBar`、`nextTargetIndex`(與羅盤粗環共用) |
| **縮圖擷取 / hero 旋轉** | `shotR`、`ensureShotScene`、`captureStoneThumb`、`startHero`/`stopHero` |
| **儲存 Vault** | `Vault`(load/save/upsert/toggleFav/trim)、`stoneRecordFromState`、`genId`/`todayKey` |
| **鏟寶石結算** | `scoopSVG`、`stonePileHTML`(id hash 定位)、`renderResultScoop`、CSS `pourIn` |
| **蒐集頁 / 石頭詳情** | `openGallery`/`renderGallery`/`openStoneDetail`、`#galleryScreen`/`#stoneDetail` |
| **標題演出** | `.tsChar` 逐字動畫、`armBase`/`armCur`(工作姿勢↔抬臂) |
| **標題字體(Cinzel+Noto Sans TC)** | `.tsTitle`/`.tsSub`/`#selectScreen .title h1` 的 `font-family`、`<head>` 的 `fonts.googleapis` 連結;改字體找這幾處 |
| **音效(全程序化 WebAudio)** | `SFX`(init/toggle/startBGM/grindStart/grindStop/enchant/**arrayCut**)、`#sndBtn`;無音檔,BGM=音墊+五聲鐘,磨石=帶通噪聲+6.5Hz 顫抖,結算=琶音→收銀,**陣列快切=噪聲上掃(魔法陣展開)+五聲密集閃光(模擬同時切完一圈)+低音收尾**(2026-07,補上原本沒音效的缺);mute 存 localStorage `gemcraft.mute`;必須在使用者手勢後 init(自動播放政策) |
| **附魔轉色(含雙色漸層)** | `TINTS` 陣列(value=數字→單色,`[c1,c2]`→漸層;紫黃晶配色=landing page 同款)、`#tintBtn`/`#tintRow`(leftTools 內原地展開,in-flow 非浮動),reset dot=回原石色;漸層核心=`applyGradAttr`(沿石頭局部方向把 c1→c2 烘進頂點色,材質底色改白+`vertexColors:true`,t 中段 ×1.6 收窄做出雙色帶分界)、`GRAD_DIRS`/`GRAD_GLYPH`(↕⤢↔⤡ 四方向,石頭局部座標=翻面自旋時顏色跟著石頭)、`#gradCtrl`(方向循環+⇅顏色對調=交換 color/color2,只在漸層時顯示)、`tintOf(state)`(縮圖/hero 共用的色描述 helper,單色=數字/漸層=物件);state 欄位 `color2`(null=單色)/`gradDir`;蒐集存檔記錄有存 color2/gradDir;淺色稜線/拋光自發光用兩色平均(`tone`)判斷;回溯不清漸層(附魔是視覺不是幾何) |
| **淺色石稜線描邊** | `rebuildStone` 的 `lum>0.85` 分支(EdgesGeometry+polygonOffset) |
| **自由切割警示角標** | `.hardBadge`(套 `.recBadge` 定位,紅橙漸層),選石畫面自由切割卡上的「🔥匠人精神」,對比圖紙卡的「⭐推薦入門」 |
| **圖紙卡 icon** | `.dcIcon` base64,來源 `瑰藝局\jewelcraft\assets\gems\`(JewelCraft GPL-3.0,`light/`=白線稿給暗色主題、`dark/`=黑線稿,亮色主題靠 CSS `filter:invert(1)` 從白轉黑,不用另外嵌 dark 版)。五份圖紙全配到位:oct8=octagon、srb57=port97=round、asscher49=asscher、tri16=trillion。`.recBadge` 推薦角標。要加新圖紙 icon 就去該資料夾選同名或形狀最近的 `light/*.png` 轉 base64 塞進對應 `<img class="dcIcon">` |
| **手機版/觸控** | CSS 尾端「手機版」區塊(`@media (max-width:720px)` 等,疊加不動桌面規則)、canvas `touchstart/touchmove`(orbit+`pinchD` 捏合)、`pressBtn` touchstart、`IS_TOUCH`/`defaultCamR`/`PRESS_LABEL` |
| **左欄收合(手機)** | `#leftCollapseBtn`(桌面 display:none)、`#leftTools.collapsed` CSS |
| **標題畫面/開場流程** | HTML `#titleScreen`、`titleMode`、`animate` 裡的定鏡塊、`titleScreen.onclick` |
| **GLB base64 資料行** | `window.MACHINE_GLB_B64=`(1.1MB 單行,別手改,用 `machine_model/inject_glb.ps1` 重生) |

另:`.claude/launch.json` 有一組 `gemcraft` 設定(`npx http-server`,autoPort 自動配 port),給 Claude Code 的 preview 工具起本地伺服器自動驗證用;玩家照樣雙擊 HTML 就好,手機玩家走 GitHub Pages 網址。

---

## 7. 用戶背景備忘(影響怎麼跟他溝通)

- **程式小白**,但有寶石礦物學、金工、Rhino NURBS 底,3D 幾何概念講得通。
- 描述力他自評低 → 給選項勾(A/B/C)比要他開放描述有效;他會直接在截圖上標註。
- 偏好:繁中、結論先講、不鋪墊、不評論進度、不估時間。
- 創作脈絡:MOGA 世界觀(硬 SF + 寶石/AI 角色),這遊戲的「中二魔法附魔」要冷峻精準,別煽情。

---

## 8. 參考資源

- **Faceting Designs 圖紙庫**(切割圖紙功能的資料來源):
  `https://www.gemologyproject.com/wiki/index.php?title=Faceting_Designs`
  → 大量現成 faceting diagram,格式 = 每行一 tier:角度 + index 位置列表。
- **GemCutter**(Blender 插件,作者 Máté Djuroska):
  核心數學跟我們一樣(angle × index × depth = facet),但他做精確建模、我們做互動體驗。
  可參考的設計:Symmetry + Mirror 模式(symmetry 數 / mirror split / mirror offset)、80 齒 index gear。
  他的參考來源也是上面的 gemologyproject。
- 原始概念規格:`isekai_gemcraft_claude.md`(v1.0,當願景參考,不要改)。
- Three.js r128 文件(切割渲染用)。
- **Design System**(2026-07,Claude Design 雲端工具產出,**故意沒放進這個 repo**,獨立資料夾:
  `C:\Users\yu2_7\Downloads\Isekai Gemcraft Design System`):品牌色票/字體/間距 token、React 元件(Button/Panel/Badge/GemMark/FeatureCard/GradientHeading/AppraisalCard)、landing/gemcraft 兩份 UI kit 重建版,給以後做視覺類任務(新宣傳頁、社群圖、新元件)當風格參考。
  **注意**:它自己的 `readme.md` 寫「gemcraft.html 沒被 commit 到 repo,UI kit 是純靠 CLAUDE.md 文字描述重建的」——這句話**是錯的**(已用 `diff` 驗證,它資料夾裡的 `game/gemcraft.html`、`game/index.html` 其實跟本 repo 的檔案逐位元組相同,它有拉到真檔)。但既然它自己都誤判過一次資料來源,**以後這個工具吐出的任何「程式碼建議」用之前都要跟本 repo 實際檔案 diff 過,別照抄**——這次的 Cinzel 字體建議剛好是巧合地已經跟現有程式碼一致,不代表每次都會這樣準。
