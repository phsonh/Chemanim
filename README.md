# Chemanim

Chemanim 是一个 C++20 + Lua 的二维有机反应机理动画引擎。画面内容只使用透明 PNG 纹理；引擎不提供文字排版对象。电子转移曲箭头由引擎按路径绘制和动画。

默认视频和逻辑画布均为 1920×1080、60 FPS。Lua 画布坐标系以画面中心为 `(0,0)`，X 向右、Y 向上。视频分辨率与逻辑分辨率可以独立设置。

## 构建与运行

```powershell
./build.ps1
./build/release/chemanim.exe aldol
```

程序根据模组名自动加载 `mod/<模组名>/main.lua`。若 `mod/` 中只有一个含 `main.lua` 的模组，也可以省略名称：

```powershell
./build/release/chemanim.exe
```

输出文件直接生成在：

```text
media/<模组名>/<模组名>_YYYY-MM-DD_HH-MM-SS.mp4
```

引擎使用 Windows Media Foundation 直接编码 H.264/MP4，不生成临时 PNG，也不依赖 FFmpeg。编码成功后自动调用系统默认视频应用播放。自动化或调试时可用 `--no-open` 禁止打开播放器：

```powershell
./build/release/chemanim.exe aldol --no-open
```

推荐目录结构：

```text
Chemanim/
├─ mod/
│  └─ aldol/
│     ├─ main.lua
│     └─ *.png
└─ media/
   └─ aldol/
```

## GUI 编辑器

`tools/editor.py` 是一个线性节点编辑器。界面参考 LuaSTG Nepy Editor，并针对 Chemanim 的顺序式动画脚本简化为“顶部节点库 + 单列节点序列 + 实时场景画布 + 右侧属性表”：一个节点对应一条 Lua 语句，节点从上到下就是最终代码顺序。

编辑器可用于：

- 从顶部分类栏选择节点类别，单击节点按钮将其插到当前节点之后。
- 在单列节点序列中查看当前帧、操作名称和关键参数，并可拖放排序或用 `Alt+↑`、`Alt+↓` 精确移动。
- 在右侧属性表编辑当前节点；对象名和纹理名会从已有声明节点中列出。
- 中央画布按选定帧显示真实 PNG、透明度、缩放、旋转、锚点、层级和动态箭头；底部滑块可检查任意帧。
- 选择“设定位置”节点后可直接拖动画布纹理，位置会回写到该节点。
- 选择“对象间贝塞尔箭头”节点后会显示起点、终点、两个控制点和辅助线，四个手柄均可直接拖动。
- 双击节点或按 `Ctrl+E` 可临时禁用语句；禁用节点显示为灰色删除线。
- 按 `F4` 展开或收起只读 Lua 视图；代码行和节点选择会互相定位。
- 使用 `Ctrl+Z`、`Ctrl+Y` 撤销或重做节点及属性修改。
- 保存 `.cmm`、生成 `mod/<模组>/main.lua`，并直接启动 MP4 渲染。

羟醛缩合范例的节点工程是 `mod/aldol/aldol.cmm`。直接打开它：

```powershell
./tools/run_editor.ps1 ./mod/aldol/aldol.cmm
```

不传文件时打开空白工作区，不自动猜测工程：

```powershell
./tools/run_editor.ps1
```

如果尚未安装 PyQt6：

```powershell
py -3 -m pip install -r ./tools/requirements.txt
```

常用操作：`Ctrl+S` 保存，`Ctrl+D` 复制节点，`Delete` 删除节点，`F6` 生成 Lua，`F5` 渲染。预览区的“播放/暂停”按钮按场景 FPS 逐帧播放，到末帧自动停止。对象下拉框按当前节点位置过滤已删除对象；新插入的参数节点会优先继承当前或上次选择的同类型对象。编辑属性只修改 `.cmm` 内存模型；点击“生成 Lua”或“渲染 MP4”时才改写入口脚本。`.cmm` 的字段说明见 [tools/CMM_FORMAT.md](tools/CMM_FORMAT.md)。

节点工具栏只有“通用 / 分子 / 箭头”三类。通用栏直接显示场景搭建、资源加载、批量资源加载、等待和 Lua 代码；分子、箭头再按创建、设定、插值、删除分组。

## 视频分辨率与逻辑分辨率

```lua
chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    background = "FFFFFFFF",
    title = "aldol"
}
```

编辑器的场景背景使用可视化颜色控件，提供系统取色器、颜色预览和 R/G/B/A 数值框。文本输入同时接受 `RRGGBB`、`RRGGBBAA`、`rgb(r,g,b)`、`rgba(r,g,b,a)` 以及逗号分隔的 RGB(A)；六位 RGB 会自动使用不透明 Alpha。

- `width`、`height` 是最终 MP4 的实际像素尺寸。
- `logic_width`、`logic_height` 是 Lua 坐标和纹理工作的逻辑画布尺寸。
- 不填写逻辑尺寸时，它们分别等于视频宽高，保持 1:1。
- 1920×1080 视频配 960×540 逻辑画布时，1 个逻辑单位对应 2×2 个视频像素；100×100 PNG 默认显示为 200×200 视频像素。
- 坐标范围是 X `[-logic_width/2, logic_width/2]`、Y `[-logic_height/2, logic_height/2]`。
- 纹理、坐标、曲箭头路径、箭头宽度和箭头头部都会参与逻辑到视频的缩放。
- 不需要设置 `end_frame`。视频结束帧自动取脚本最终编排帧与所有未完成插值轨道结束帧的最大值。
- 旧脚本如果仍填写 `end_frame`，它会作为最短输出长度继续生效。

## 脚本结构

```lua
local chem = require("chem")

chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    background = "FFFFFFFF",
    title = "aldol"
}

chem.load_texture("phcome", "phcome.png", 0, 0)

local molecule = chem.NewMol()
molecule.SetPos(300, 240)
molecule.SetImage("phcome")
molecule.SetAlpha(0)

-- Lerp 非阻塞：两条插值在当前帧同时开始。
molecule.LerpAlpha(255, 30, 0)
molecule.LerpPosX(500, 30, 0)

-- 只有 Wait 推进编排时间。
chem.Wait(60)
molecule.LerpAlpha(0, 30, 0)
```

对象是实际的 Lua table。方法是绑定到具体对象的函数，因此推荐并支持脚本里的点调用写法：

```lua
molecule.SetPos(100, 200)
```

也兼容冒号调用，但没有必要：

```lua
molecule:SetPos(100, 200)
```

## 纹理与锚点

```lua
chem.load_texture(texture_name, png_path, anchor_x, anchor_y)
```

- `texture_name`：脚本中使用的资源名。
- `png_path`：相对 Lua 文件目录的 PNG 路径。
- `anchor_x`、`anchor_y`：可省略，默认都是 `0.5`。
- 在编辑器中通过文件选择器选择 PNG 时，资源名会同步为文件名去掉 `.png` 的部分；同步只发生在选择文件的当下，之后仍可单独修改资源名。
- “加载纹理”节点会直接显示当前 PNG 的缩略图和 `宽×高 px`；分子对象的“选择纹理”和“过渡更换纹理”节点也使用可视化资源选择器。所有缩略图统一使用场景设置中的背景颜色，以接近实际视频观感；选项直接显示资源名、文件名和原始尺寸，节点序列摘要也会显示尺寸。
- 锚点坐标以纹理左下角为 `(0,0)`、右上角为 `(1,1)`。
- 这里说的是纹理内部锚点坐标；画布坐标仍以画面中心为 `(0,0)`。
- 同一纹理的所有对象默认使用资源锚点；对象可用 `SetAnchor()` 单独覆盖。

例如：

```lua
chem.load_texture("centered", "centered.png")       -- 中心锚点
chem.load_texture("bottom_left", "mol.png", 0, 0)  -- 左下角锚点
chem.load_texture("bond_site", "mol.png", 0.82, 0.46)
```

## 时间轴语义

- 帧号从 0 开始。
- `Set*` 在当前帧瞬间设值。
- `Lerp*` 在当前帧启动插值，但不推进当前帧。
- `chem.Wait(n)` 把当前帧向后移动 `n` 帧。
- `chem.SetFrame(n)` 跳到绝对帧，适合精确回填动画。
- `chem.GetFrame()` 返回当前编排帧。
- 同一对象可以同时运行位置、透明度和缩放轨道。

插值模式：

| 模式 | 函数 |
|---:|---|
| `0` | `linear(x) = x` |
| `1` | `easeIn2(x) = x²` |
| `2` | `easeIn3(x) = x³` |
| `3` | `easeOut2` |
| `4` | `easeOut3` |
| `5` | `easeInOut2` |
| `6` | `easeInOut3` |

## 纹理对象 API

创建与生命周期：

```lua
local object = chem.NewMol()
object.Delete()                          -- 从当前帧起删除
```

瞬间设置：

```lua
object.SetImage("texture_name")
object.SetPos(x, y)
object.SetPosX(x)
object.SetPosY(y)
object.SetAlpha(alpha)          -- 0 到 255
object.SetColor(r, g, b)
object.SetScale(scale)          -- 等比
object.SetScale(x, y)           -- 横纵独立
object.SetScaleX(x)
object.SetScaleY(y)
object.SetRotation(degrees)
object.SetLayer(layer)
object.SetVisible(true_or_false)
object.SetAnchor(x, y)
```

非阻塞插值：

```lua
object.LerpPos(x, y, frames, mode)
object.LerpPosX(x, frames, mode)
object.LerpPosY(y, frames, mode)
object.LerpAlpha(alpha, frames, mode)       -- alpha 为 0 到 255
object.LerpColor(r, g, b, frames, mode)
object.LerpScale(scale, frames, mode)       -- 等比
object.LerpScale(x, y, frames, mode)        -- 横纵独立
object.LerpScaleX(x, frames, mode)
object.LerpScaleY(y, frames, mode)
object.LerpRotation(degrees, frames, mode)
object.ChangeImage("next_texture", target_x, target_y, frames, mode)
```

`SetImage()` 是瞬间切换纹理的帧事件。`ChangeImage()` 则在同一个对象上交叉淡化：旧纹理固定在过渡开始时的旧坐标，目标纹理在给定的新坐标淡入；完成后对象正式采用目标纹理和目标坐标。两张纹理还会共同乘以对象该帧的实际 Alpha。因此对象 Alpha 为 120 时，线性过渡就是旧纹理 `120→0`、新纹理 `0→120`，而不是固定使用 255。命令只安排动画，不推进脚本时间：

```lua
object.ChangeImage("transition_state", 120, -35, 60, 0)
chem.Wait(60)
```

旧的三参数写法仍可运行，目标纹理会使用过渡开始帧的对象坐标。编辑器的“过渡更换纹理”节点使用五参数写法，并提供洋葱皮对齐：旧帧作为半透明参考，拖动新贴图，松开后才提交目标坐标。

同一对象、同一属性的后续插值会抢占尚未结束的前一个插值。后一个插值从抢占帧的实际状态继续，不会等前一个结束，也不会在之后跳回前一个目标。

新建纹理对象的 Alpha 默认为 `0`，通常直接用 `LerpAlpha()` 淡入；箭头的 Alpha 仍默认为 `255`。

## 动态电子箭头

使用逻辑画布绝对坐标定义三次贝塞尔曲线：

```lua
local arrow = chem.NewArrow()

-- 起点、控制点 1、控制点 2、终点，全部是以画布中心为原点的逻辑坐标。
arrow.SetCurve(-180, 40, -80, 170, 60, 150, 140, 20)
arrow.SetColor(25, 90, 170, 255)
arrow.LerpColor(190, 45, 75, 30, 0)
arrow.SetWidth(3)

-- 沿贝塞尔曲线的实际弧长擦出，不是矩形裁切。
arrow.LerpProgress(1, 30, 5)

-- 箭头使用完后淡出，再在淡出结束的脚本帧删除。
arrow.LerpAlpha(0, 20, 0)
chem.Wait(20)
arrow.Delete()
```

- 箭头不绑定纹理对象，所有点都直接使用逻辑画布绝对坐标；画布中心是 `(0, 0)`，Y 轴向上。
- 新建箭头的进度默认为 `0`，可以直接调用 `LerpProgress()` 擦出。
- 曲线严格使用三次贝塞尔的起点、控制点 1、控制点 2、终点。
- 默认箭身宽度为 `3`。三角头部完全由线宽等比例决定：头部长为 `line_width × 20/3`，底边宽为 `line_width × 5`。例如线宽 `3` 对应 `20 × 15`，线宽 `6` 对应 `40 × 30`，不提供独立的头部尺寸 API。
- `SetCurve(x1,y1,cx1,cy1,cx2,cy2,x2,y2)` 是箭头曲线 API；箭头只使用绝对坐标，不再提供对象绑定兼容 API。
- 箭头同样支持 `SetPos`、`SetAlpha`、`LerpAlpha`、`SetLayer` 和 `Delete`。`LerpAlpha` 只安排动画、不推进脚本帧；需要在淡出后删除时，先 `Wait` 相同帧数再调用 `Delete()`。
- 编辑器的箭头分类提供独立的颜色插值、透明度插值和删除节点；颜色插值生成 `arrow.LerpColor(r, g, b, frames, mode)`。

编辑器节点工具栏只分为“通用 / 分子 / 箭头”。“通用”中提供场景搭建、资源加载、批量资源加载、等待和 Lua 代码；文字请在 ChemDraw 中做好后导出 PNG，作为普通分子纹理使用。

## 当前范例

羟醛缩合脚本是 [mod/aldol/main.lua](mod/aldol/main.lua)。绝对坐标箭头范例是 [mod/arrow_demo/arrow_demo.cmm](mod/arrow_demo/arrow_demo.cmm)，可在编辑器中直接拖动四个贝塞尔手柄。

引擎仍保留少量第一版小写函数用于旧脚本迁移，但新脚本应使用本页的对象式 API。
