# 異世界魔法石工坊 — 開發交接文件 (claude.md)

> 給未來的我 / 未來的 AI session：這份是**目前實作狀態**的交接,不是原始需求。
> 原始需求規格在 `isekai_gemcraft_claude.md`(v1.0 概念文件),那份不要改,當願景參考。
> 這份 `claude.md` 是「現在做到哪、怎麼動、接下來做什麼」。

---

## 0. 一句話

模擬真實寶石切割機的網頁小遊戲,單一 HTML 檔。選晶系(+可選切割圖紙)→ 傾斜石頭設角度/方位(+深度止停)→ 盲切 → 拋光 → 中二鑑定。

**主程式：`gemcraft.html`(單檔,雙擊用瀏覽器開,需連網載 Three.js CDN)。**

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

## 3. 目前實作了什麼(可玩的核心迴圈)

- [x] 7 晶系選擇 → 對應凸多面體原石(八面體/六角雙錐柱/方柱/三角柱/菱形柱/斜柱/扁板)+ 隨機克拉(25–40ct)
- [x] **傾斜切割機**:角度滑桿(0–90°)石頭即時傾斜;96 齒 index 自旋
- [x] **盲切**:按住下壓遮蔽 + 深度條,鬆開揭曉,不可 Undo
- [x] 三段 lap(粗磨/細磨/拋光)材質從霧面→鏡面
- [x] 翻面切冠部/亭部(桿不翻、石頭翻)
- [x] **✂ 預成形**:一鍵把細長晶柱裁成矮胖粗胚
- [x] 報廢換石、克拉累計、殘骸列表
- [x] **導覽器(top view)**:沿石頭軸看,即時對稱性分析(算切面法線方位的 n 折偏差)
- [x] **🧭 方位尺(羅盤)**:可開關,度數環 + 金針(指當前 index 方位)+ 折數對稱位青點
- [x] 折數快捷(8/16/4/6 折),每按跳「下一個」對稱齒位 + 高亮
- [x] index 小錶盤指針 + 方位角度數字
- [x] **研磨台顯示模式**:實體 / 線框 / 隱藏(擋視線時切掉)
- [x] **教學卡**:左上❔鈕,進切割畫面第一次自動跳一次
- [x] 操作台可收合、移到右下角
- [x] 中二結算卡:評級/成品率/估價/毒舌評語(本地啟發式,非真 AI)
- [x] **📜 切割圖紙模式**(2026-07):選石畫面選圖紙(`#diagramRow`)→「✂ 圖紙預成形」裁成已知半徑 R 的 24 角柱標準粗胚(腰圍=y0,24 角柱側面就是腰稜,不用切 girdle tier)→ 左側指令表面板(`#diagramPanel`)逐 tier 施工。內建兩份:**初陽八角**(教學 17 面)、**SRB 57**(標準圓明亮式)。已用 `#dev` 工具驗證兩份圖紙 100% 命中(法線偏差 0°)
- [x] **深度止停(mast height)**:操作台新滑桿+開關(單位 %R),壓到止停自動停住、鬆手切在精確平面;同位重切零損耗
- [x] **點 tier 列自動帶入**角度+深度+翻面;index 與下壓仍手動(真機自動化 vs 師傅手工的分界)
- [x] **勾銷與防呆**:止停切割匹配 tier(側+角度±0.5°+深度±0.5%R)且齒位在表內才打勾;錯齒照切但警告「這刀白切了」
- [x] **⚡ 魔法陣列快切**:一鍵切完當前 tier 剩餘對稱位(逐刀 `cutAtPlane`,最後才重建 mesh)
- [x] **羅盤目標齒位**:金環=目標、填色=已完成、粗環=離當前 index 最近的下一刀;圖紙模式自動開方位尺
- [x] **圖紙結算分支**:完成度 50 + 幾何準確度 30(`auditDiagram` 掃切面法線+平面距離對表)+ 成品率 20
- [x] **#dev 校準工具**:URL 加 `#dev` → console 的 `__diag.run('oct8'|'srb57')` 一鍵照圖切完、`__diag.dump()` 傾印每個切面的角度/方位/d(%R)
- [x] **UI 熱點重排**(2026-07 第三輪):操作台瘦身兩欄+不 hover 自動淡出(按壓中 `.pressing` 不淡);**下壓鈕上方「下一刀」資訊帶**(`#nextCutBar`,tier+角度+深度+下一齒,陣列快切鈕也搬到這);UI 整體提亮(`--dim`/面板不透明度/金紫邊);石頭+dop 視覺下移貼盤(`STONE_Y_OFF=-0.42`,切割數學不動,導覽器相機已補償)
- [x] **標題演出**:機臂工作姿勢壓盤(armBase=0)→點擊進入抬臂緩動到 `PARK_ANGLE`;遊戲 dop 標題時隱藏;標題字逐字放大進場(`.tsChar`)
- [x] **鏟寶石結算 + localStorage 儲存 + 蒐集頁**(2026-07 第三輪,分鏡=用戶手繪):
  - 每顆石頭在提交/報廢時用 `captureStoneThumb`(shotR 離屏渲染 96px JPEG ~3KB)拍縮圖入盤;結算卡兩欄:左=鏟子 SVG+縮圖彈跳撒入(`pourIn`),右=hero 主角石實時 3D 旋轉(`startHero`,MeshPhysicalMaterial+自產 envMap 亮晶晶)+原數據/鑑定
  - `Vault`(key `gemcraft.vault.v1`):一爐=一盤(session.vid/date),同 uid 重提交=覆蓋;上限 600 顆,超額砍最舊非⭐;無痕/擋儲存靜默降級
  - 蒐集頁(`#galleryScreen`,選石畫面/結算 foot 進入):一盤一卡按日期,點石頭開詳情(參數+⭐最滿意,⭐石在盤中放大)
- [x] **圖紙庫擴充至 5 份 + 垂直腰刀**(2026-07 第四輪):新增 **八角階梯 Asscher 49**(8 indices 階梯切工)、**迴環重瓣 Portuguese 97**(16 折三層齒位交錯,含 24 腰稜共 121 面壓測通過)、**三稜 Trillion 16**(3 折,96/3=32 齒一格)。新機制 `side:'girdle'`(垂直腰刀,角度 90°,亭部模式下切不翻面,`TIER_LABEL` 顯示「腰」,`recordDiagramCut` 視同 pavilion 側勾銷)——用來把 24 角柱腰圍塑成八角/三角直邊外形。五份圖紙 `#dev` 全掃 100% 命中、偏差 0°;玩家路徑(預成形→點 tier→陣列快切)驗證通過。**新增切型的完整方法論見 `新增切型指南.md`**。
- [x] **左欄排版修正 + 淺色石稜線描邊**(2026-07 第四輪,修用戶回報兩個視覺 bug):
  - **左欄不再互蓋**:`#diagramPanel` 原本絕對定位 `top:190px`,圖紙模式會蓋住第三顆 🎨 附魔轉色鈕(用戶:「這個按鈕只有我會知道而已」);現在整個收進 `#leftTools` 的 flex column 正常排版流(HTML 也搬進去了),`#tintRow` 調色盤改成按鈕正下方原地展開(6×2 grid,不再是浮在 3D 畫面上的絕對定位 popover),開合會把指令表往下推,三者永不重疊。`#diagramPanel` max-height 56vh→48vh 補償排版流起點變低。
  - **淺色石看得到刻面**:白鑽在切割視圖整坨死白、刻面邊界讀不出來 → `rebuildStone` 對亮度 lum>0.85 的石色(白鑽 0xdce8f2)疊一層 `EdgesGeometry` 深色稜線(石色×0.38)+ 面色×0.9 微降亮 + 兩個面材質開 polygonOffset 防線面 z-fighting;深色石完全不動。稜線是 stoneMesh 的 child,跟著傾斜/自旋,導覽器 top view 也看得到;rebuild 時會 dispose 舊稜線。已用 `#dev` oct8 全程切完驗證 17/17 命中、偏差 0°,切割數學不受影響。
- [x] **機台模型導入 + 標題畫面**(2026-07):`machine_model/` 的切割機 GLB 以 **base64 內嵌**在 HTML(`window.MACHINE_GLB_B64` 那行,~1.1MB,**別手改**,重生成用 `machine_model/inject_glb.ps1`)。流程變成:標題畫面(定鏡看機台,機件全動:lap 轉/魔法陣呼吸閃爍/水滴循環/分度輪慢轉/機臂呼吸)→ 點擊 → 選晶系+圖紙 → 切割介面。切割介面裡機台取代舊簡易研磨台(`lapGroup`/`floor` 退役但保留當 fallback),**石頭/dop 仍是遊戲原本那套會動的**(手感核心不動),機臂抬起待命(`PARK_ANGLE`);轉 index 時機台 96 齒分度輪會跟著跳齒。GLTFLoader 從 jsdelivr CDN 載;GLB 載入失敗自動退回舊簡易研磨台,遊戲照玩。
- [x] **魔法快切導覽(coachmark)**(2026-07 第五輪):圖紙模式第一次選石自動跳,非阻塞式聚光燈提示(`#coachMark`,dim 背景+金框+文字泡泡),**跟著玩家實際動作前進**而非手動翻頁:①點 `#preformBtn`(預成形)→②點 `#dgTiers` 任一列(照順序走)→③按住 `#pressBtn` 到「🛑已達深度止停」才放開(用戶實測回報卡在這步——原因是誤以為點一下就好,沒發現深度止停要「按住等它自己停」,已在文案明講)→④點 `#nextCutBar` 的「⚡魔法陣列快切」。四步分別掛在 `preformDiagram`/`activateTier`/`recordDiagramCut`/`arrayCutBtn.onclick` 尾端推進,隨時可按泡泡上「✕略過導覽」跳出;`coachShown` 是 session 變數(跟 `tutShown` 同慣例,重整頁面會再跳一次)。收合操作台/視窗縮放都有掛 `coachPosition()` 防跑位。
- [x] **手機版適配(直向優先)**(2026-07 第七輪):同亮色主題的疊加策略——桌面 CSS 一行不動,`<style>` 尾端加觸控通用規則 + `@media (max-width:720px)`(直向重排)+ `@media (min-width:721px) and (max-height:540px)`(橫向微縮)。
  - **觸控輸入**:canvas 單指拖曳=轉視角、雙指捏合=縮放(對應右鍵拖曳/滾輪;`touch-action:none` 把手勢留給遊戲不給瀏覽器);`#pressBtn` touchstart/touchend 對應盲切按住(touchstart 的 preventDefault 同時擋掉合成 mousedown,不會重複觸發);全域 `touchend/touchcancel` 保底 endPress。
  - **直向排版**:導覽器縮 146px、指令表 46vw/26vh、操作台滿版貼底(左留 56px 走道給音效/主題鈕直排,兩鈕 z-index 降 30 讓結算/蒐集彈窗蓋過)、選石畫面晶系 2 欄+圖紙卡滿寬直排+整頁可捲動、結算卡 `.rMain` 改直排、`#scrapTray` 隱藏、教學/結算卡可捲動不超框。
  - **相機補償**:`defaultCamR()` 窄螢幕(<720px)回 7.2、桌面 5.5(直向水平視野窄,拉遠才裝得下機台),`resetView` 同步。
  - **文案**:`IS_TOUCH`(pointer:coarse)時下壓鈕文案去掉「左鍵」(`PRESS_LABEL`)、教學卡「右鍵拖曳/滾輪」字眼換成觸控版;coachmark ③ 改裝置中性「滑鼠或手指壓著」。觸控裝置 `#console` 的 hover 淡出改常駐 92% 透明度(`@media (hover:none)`)。
  - **實測**:375×812 全流程(選石→預成形→合成 TouchEvent 壓到深度止停→鬆手勾銷→陣列快切→結算)通過,oct8 17/17 稽核不受影響;桌面(>720px)迴歸無變化;亮色主題×手機版相容。**已知妥協**:手機橫拿(812×375)導覽器與操作台右上角小面積重疊,靠操作台可捲動+微透明堪用——**直向是主設計模式**。
  - 附帶:`.claude/launch.json` 改 `autoPort`(8123 被別的 session 占走時自動換 port,http-server 吃 PORT 環境變數)。
- [x] **手機版實機回饋修正**(2026-07 第七輪後續,用戶 iPhone 實測三個問題):
  - **收合操作台鈕被裁切**:上一輪給 `#console` 加的 `overflow-y:auto` 把突出面板頂的 `#collapseBtn`(top:-14)剪掉了 → 手機版把它改 `position:static; order:-1` 收進 flex 排版流第一列(靠右),桌面浮動樣式不動。
  - **左欄收合**(`#leftCollapseBtn`,手機版才顯示):「◀ 收合面板」⇄「📜 展開面板」,收起時 `#leftTools.collapsed > *:not(#leftCollapseBtn){display:none !important}` 藏掉教學/研磨台/附魔/指令表整欄(`!important` 蓋得過 JS 寫的 inline display),看石頭不擋視線。
  - **coachmark 框選偏移+卡步驟**:根因是 `coachPosition()` 只在 resize/收合時重算,手機上指令表捲動、iOS 工具列縮放、預成形後面板長高都會讓金框停在舊位置 → ①導覽顯示中改 **每 250ms setInterval 跟刷**(任何漂移 0.25 秒內歸位);②泡泡加「**下一步 ▸**」鈕(末步變「✓ 完成」),手動推進不再依賴玩家做對動作才前進(用戶建議的形式);③`coachShow` 先把目標 `scrollIntoView` 再定位;④窄螢幕兩側塞不下泡泡時改放目標正下方/上方,不蓋住要點的元素。注意 `#coachHi` 有 0.25s CSS transition,程式讀 highlight 位置要等過渡完。
  - 全流程手機重測:①→②→③→④ 金框全部貼合目標、下一步/完成可點、左欄收展正常;桌面(>720px)迴歸無變化(左欄鈕隱藏、操作台鈕維持浮動)。
- [x] **推廣 landing page + 宣傳截圖管線**(2026-07 第九輪,用戶四選一裁定:首頁 landing/暗色魔法風/YouTube 佔位/純英文):
  - **`index.html` 從轉跳頁改成英文推廣頁**:hero(大 Play 鈕→gemcraft.html)+影片區(YouTube 佔位,`const YT_ID=""` 填影片 ID 即自動換 iframe,沒填顯示機台海報+TRAILER COMING SOON)+三特色卡+截圖區+圖紙表+How it works(凸多面體技術段,關鍵詞:real-time convex clipping/procedural gemstone faceting/computational geometry in the browser)+開源 CTA+footer。styling 沿用遊戲暗色魔法調色盤,RWD(375px 無橫捲)。**og:image/twitter card 已配**(shot_title.jpg 絕對網址),社群分享有大圖。
  - **`#shot` 截圖旗標**(gemcraft.html):URL hash 含 `shot` 時 renderer 開 `preserveDrawingBuffer`,console 可用 `renderer.domElement.toDataURL()` 拍乾淨 3D 圖(無 UI overlay);`#shot-dev` 可同時啟用 `__diag`。**拍圖流程備忘**:preview 分頁背景化會暫停 rAF → 拍之前要手動 `renderer.render(scene,camera)` 刷一幀;等 `machineRoot` 非 null 才代表 GLB 載完;落地用臨時 Node 接收器(頁面 fetch POST dataURL 到 localhost 小 server,scratchpad 有範本 shot_receiver.js 的做法)。
  - **`assets/`**:shot_title.jpg(標題機台,og:image)、shot_asscher.jpg(白鑽 Asscher+稜線)、shot_port97.jpg(紫晶 Portuguese),全部 1200×675 遊戲內實拍。
  - **repo topics/描述已設**(gh CLI):threejs/webgl/computational-geometry/convex-clipping/faceting/lapidary/gemstone 等。
  - **landing 視覺升級**(第九輪後續,用戶看了 Spline Remix 想要但要課金 → 純 SVG+vanilla JS 自製,Opus 開規格):①捲動進場 fadeInUp(IntersectionObserver+`.reveal`,特色卡 stagger)、特色卡 hover 紫金光暈、hero 標題呼吸光、Play 鈕 hover 脈衝;②**紫黃晶寶石互動層**(`#gemField`):10 種經典切型俯視線稿(Round/Radiant/Princess/Pear/Oval/Marquise/Heart/Emerald/Cushion/Asscher,SVG `<defs>` 手繪 path)散佈頁面兩側 16 顆、緩慢浮動,滑鼠 250px 半徑內從半透明白漸變成**紫黃晶 Ametrine**(上紫 #9b59b6 下金 #d4a017,`linearGradient`)+輕轉 22°,離開 0.8s 褪回;rAF 節流,觸控裝置直接不啟用追蹤(靜態白)。**踩過的坑:`<use>` 複製體在 shadow DOM,外部 CSS 選不到子元素**——著色只能靠 `<use>` 上的可繼承屬性(fill/stroke),fill 只作用在封閉形(直線段面積零),漸層以各封閉形自身 bbox 取範圍反而做出「每個刻面各自紫→金」的分帶效果。
- [x] **中英雙語切換(i18n)+ 開源推廣配套**(2026-07 第八輪,for 英文推特/介紹/影片推廣):
  - **架構**(零邏輯改動,只動文字層):①動態字串 → `tx(zh,en)` 雙語內聯 helper(檔頭宣告 `UI_LANG`,約 40 處呼叫點:結算毒舌/勾銷警告/nextCutBar/羅盤/盲切/蒐集頁/詳情/confirm/alert 全含);②靜態 HTML → 檔尾 `I18N_STATIC` 選擇器表(~55 條,zh 原文首次套用時從 HTML 快取,所以**繁中以 HTML 為準**、英文在表裡);③資料物件 → `SYSTEMS`(nameEn/gemEn/shapeEn)、`DIAGRAMS`(nameEn/descEn)、`LAPS`(nameEn)、`GEM_NAMES_EN`、`TIER_LABEL_EN`(Pav/Crn/Gdl),取用走 `dgName()/dgDesc()/lapName()/tierLabel()` helper。
  - **切換**:`#langBtn`(主題鈕右邊/手機左下直排第三顆,顯示目標語言「EN/中」),`applyLang()` 即時切換=靜態表重套+標題重拆字(`renderTitle`)+晶系卡重生+各動態 label 依現況重刷;存 `localStorage gemcraft.lang`,預設繁中。
  - **陷阱備忘**:教學卡的觸控字眼替換(右鍵→單指)整合進 `applyStaticLang`,兩種語言各有替換對(EN 文案必須含 'Right-drag to orbit, scroll to zoom' 和 'hold the big purple button' 原句才替換得到);`PRESS_LABEL` 常數改成 `pressLabel()` 函式;毒舌鑑定英文版同冷峻語氣(佔位語氣範本,可全數替換);蒐集頁存檔內的石頭名稱存的是「當時語言」的字串,舊資料照原樣顯示不轉換。
  - **驗收**:繁中預設像素級不變;EN 全畫面走過(標題/選石/教學/coach/切割 HUD/指令表/結算/蒐集);遊戲中即時雙向切換各 label 全部跟上;五份圖紙 `#dev` 回歸 100%;console 零錯誤。
  - **開源配套**:`README.md` 改英文主體(Play Now 連結/特色/凸多面體裁切技術段/貢獻指引);**授權已裁定 GPL-3.0**(2026-07 用戶定案,LICENSE=官方全文,gemcraft.html 檔頭有版權聲明,CONTRIBUTING 明訂貢獻同授權,與 JewelCraft icon 的 GPL-3.0 相容);`CONTRIBUTING.md`(英文,自足版新增切型指南:格式+d 公式+五硬檢查+96 齒對稱規則+`__diag` 驗收清單+PR 格式);`.github/ISSUE_TEMPLATE/` 兩個表單(New Diagram Request 含折數下拉與拉長外形防呆勾選、Bug Report 含「真破面 vs 切得醜」區分)。
- [x] **亮色玻璃主題(Apple 風 liquid-glass)+ 明暗切換**(2026-07 第六輪):`#themeBtn`(🌙/☀️,`sndBtn` 右邊)一鍵切,存 `localStorage gemcraft.theme`,預設暗色。**只換 UI 外殼**,3D 切割場景(教堂光/霧/暗角/導覽器小視窗/hero 旋轉視窗)刻意維持原樣不動(用戶裁定範圍)。實作方式:整包疊在 `html[data-theme="light"]` 選擇器裡,一行都沒改原本的暗色規則本身——靠選擇器優先度覆蓋,零迴歸風險(已截圖比對確認暗色主題像素級不變)。分兩層:①核心變數(`--panel/--line/--accent/--accent2/--text/--dim/--warn/--gold`)重新賦值,套用到所有原本就用 `var()` 的規則(按鈕文字/邊框/hint 等大部分自動吃到);②約 20 條寫死 hex 顏色的規則(sysCard/diagCard/tierRow/idxChip/結算卡/教學卡/蒐集頁等)逐一加 `html[data-theme="light"] 選擇器{}` 明版覆蓋。**踩過的坑**:沒包在 `.panel`(沒有自己 `backdrop-filter`)、直接浮在 3D 場景上的裸 `button`(左側 `#leftTools` 三顆、`#tintRow`、`#coachBubble`)一開始只換了半透明白底沒加 blur,亮背景會把文字洗到快看不見——後來在 `html[data-theme="light"] button` 統一補 `backdrop-filter:blur(14px) saturate(160%)` 才解決;已包在 `.panel` 裡的子元素(console 內按鈕、tierRow 在 diagramPanel 裡)不需要自己 blur,吃父層的就夠。大面板(`.panel`/結算卡/蒐集頁/教學遮罩)用 `blur(22px) saturate(180%)`。

---

## 4. 待確認 / 已知小問題

- **方位尺金針的轉向與零點**：直接用 index 角度畫的,跟 3D 石頭視覺旋轉方向**可能左右相反或差一個 offset**。需實際比對。要修的話改 `updateCompassNeedle(deg)` 的 deg 正負或加常數;`buildCompass()` 是度數環,`updateCompassFold()` 是青點。**羅盤目標齒位(`updateCompassTargets`)刻意用同一套 `(t%96)*3.75` 慣例**,就算整體鏡像,金環跟金針永遠相對一致——要校正就一起改。
- `clipSolid` / `stitchLoop` 的極端切法破面風險(見 2.1)。SRB 57 面 + 24 腰稜(81 面)壓測通過,沒破面。**圖紙模式風險趨近於零**(角度/深度/index 都鎖在表定值,等於全跑過壓測);**自由切割沒有這層保護**——玩家可以用任意角度+任意深度連續下壓,沒人校過那個組合空間,是「破圖」回報最可能的來源(2026-07 用戶朋友玩舊版時發生)。目前只做了 UX 層防呆:選石畫面自由切割卡加「🔥匠人精神」警示角標(`.hardBadge`,見選石畫面 `#diagramRow` 第一張卡)區分於圖紙的「⭐推薦入門」,提示新手不要預設選它;**幾何層本身沒加防呆**,真的極端切法(例如同角度貼著切到只剩極薄一層)理論上仍可能讓 `stitchLoop` 縫不出封閉面。若之後再收到破圖回報,先問清楚是「幾何真的破洞/面缺角」還是「只是切得對稱很差、形狀很醜」——只有前者才是這裡要查的 bug。
- 結算估價/評級公式是隨手抓的(`showResult()` 裡),數值平衡沒調過。圖紙模式成品率天生偏低(預成形吃掉很多料,約 10–15%),評語 <15% 那句會常駐,要嫌煩就調門檻。
- 圖紙模式的深度止停滑桿玩家可以手動亂調(離開表定值),切了照樣不勾銷——是特性不是 bug(機器不會救你),但沒有明確提示為什麼沒打勾。
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

- ~~切割圖紙 / 目標範本~~ **已做**;~~擴充圖紙庫~~ **已做第一輪**(2026-07 加了 Asscher 49 / Portuguese 97 / Trillion 16,共 5 份,見第 3 節)。**再加新切型看 `新增切型指南.md`**(完整格式/數學/校準流程/授權注意,可直接發包給其他模型)。
- ~~魔法陣列快切~~ **已做**(`#arrayCutBtn`)。GemCutter 的 mirror split/offset 進階模式還沒做,要做花式切割再說。
- **附魔系統**:指定石種名稱 + 處理方式(加熱/輻照/充填/擴散/鍍膜),並用附魔當「清除 dop 蠟痕、恢復透明度」的敘事理由。(轉色部分已做,見 🎨 附魔轉色)
- **Minecraft 第一人稱選石手**:選石畫面目前是純卡片,沒有持 dop 的第一人稱手。
- **多種 index 齒數(80 齒)**:5 折對稱需要(96 不整除 5)。工程量與改動點分析見 `新增切型指南.md` 第 6 節。
- ~~音效~~ **已做**(全程序化 WebAudio `SFX`,見程式地圖)。
- ~~研磨機模型導入~~ **已導入**(見第 3 節)。`machine_model/` 資產:`gem_faceting_machine.blend`(含魔法陣閃爍動畫 fr1-250)、`.glb`、`build_machine.py`(全程序化,改參數重跑 25 秒重生一台)、`inject_glb.ps1`(重生後把 GLB 重新 base64 注入 gemcraft.html)、三張 render。
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
| **指令表面板 / tier 帶入 / 勾銷** | `renderDiagramPanel`、`activateTier`、`recordDiagramCut`、`flashWarn` |
| **陣列快切** | `#arrayCutBtn` 的 onclick |
| **圖紙結算稽核** | `auditDiagram`、`showResult` 的 `dg` 分支 |
| **#dev 校準工具** | 檔尾 `location.hash.includes('dev')` 區塊(`__diag.run`/`__diag.dump`) |
| 傾斜/自旋/翻面 | `rigQuaternion`、`stoneQuaternion`、`expectedNormal`、`setCrown`、`updateNavCam` |
| 石頭外觀/材質/lap 階段 | `LAPS`、`rebuildStone`、`buildGeometry` |
| 盲切手感 | `startPress`/`endPress`、`MAX_DEPTH`、`DEPTH_RATE`、`animate` 裡的深度條 |
| index / 折數 / 錶盤 | `setIndex`、`.presetRow` 的 onclick、`setActiveFold` |
| 方位尺羅盤 | `buildCompass`、`updateCompassNeedle`、`updateCompassFold`、`updateCompassTargets`(金環) |
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
| **下一刀資訊帶** | `#nextCutBar`、`updateNextCutBar`、`nextTargetIndex`(與羅盤粗環共用) |
| **縮圖擷取 / hero 旋轉** | `shotR`、`ensureShotScene`、`captureStoneThumb`、`startHero`/`stopHero` |
| **儲存 Vault** | `Vault`(load/save/upsert/toggleFav/trim)、`stoneRecordFromState`、`genId`/`todayKey` |
| **鏟寶石結算** | `scoopSVG`、`stonePileHTML`(id hash 定位)、`renderResultScoop`、CSS `pourIn` |
| **蒐集頁 / 石頭詳情** | `openGallery`/`renderGallery`/`openStoneDetail`、`#galleryScreen`/`#stoneDetail` |
| **標題演出** | `.tsChar` 逐字動畫、`armBase`/`armCur`(工作姿勢↔抬臂) |
| **音效(全程序化 WebAudio)** | `SFX`(init/toggle/startBGM/grindStart/grindStop/enchant)、`#sndBtn`;無音檔,BGM=音墊+五聲鐘,磨石=帶通噪聲+6.5Hz 顫抖,結算=琶音→收銀;mute 存 localStorage `gemcraft.mute`;必須在使用者手勢後 init(自動播放政策) |
| **附魔轉色** | `TINTS` 陣列、`#tintBtn`/`#tintRow`(leftTools 內原地展開,in-flow 非浮動),reset dot=回原石色 |
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
