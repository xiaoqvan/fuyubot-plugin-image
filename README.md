# image-plugin

FuyuBot 的 HTML 出图插件。注册 `image.render` 服务：给它 HTML 或「模板 + 数据」，
它返回一张 JPEG / PNG。

插件不带业务字段，模板、数据、尺寸都由调用方给。

## 安装

1. 把发布包解压到机器人的插件目录：

```text
plugins/
└── image-plugin/
    ├── plugin.json
    └── bin/
        ├── image_plugin.dll       # Linux: libimage_plugin.so / macOS: libimage_plugin.dylib
        ├── image-shot.exe         # 渲染器，必须和插件放在一起
        └── ultralight/            # Ultralight 运行时
```

2. 从 Ultralight 官网下载 SDK：<https://ultralig.ht/download>

3. 把 SDK 里的运行时文件放进 `bin/ultralight/`：

```text
bin/ultralight/
├── Ultralight.dll
├── UltralightCore.dll
├── WebCore.dll
├── AppCore.dll
└── resources/
    ├── icudt67l.dat
    └── cacert.pem
```

Linux / macOS 用 SDK 里对应的 `.so` / `.dylib`，文件名不变。

4. 重启机器人。渲染器默认按 `plugins/image-plugin/bin/` → `plugins/image-plugin/`
   → `plugins/` → `plugins/ultralight/` 的顺序查找运行时。

如果运行时放在别处，可以在配置里指定渲染器路径。

## 配置

```toml
[plugin.image-plugin]
binary = "D:/fuyubot/plugins/image-plugin/bin/image-shot.exe"
templates_dir = "D:/fuyubot/plugins/image-plugin/templates"
```

| 键 | 必填 | 说明 |
| --- | --- | --- |
| `binary` | 否 | `image-shot` 的路径；不写则按默认目录查找 |
| `templates_dir` | 否 | 请求里没给 `template_dir` 时使用的默认模板目录 |

也可以不写配置，把 `image-shot` 和 `ultralight/` 放到插件目录即可。

## 使用

服务名 `image.render`，两个方法：

| 方法 | 入参 | 返回 |
| --- | --- | --- |
| `render` | `template` + `data`，或直接给 `html` | `{"ok":true,"path","width","height","bytes","ms"}` |
| `ping` | 任意 | `{"ok":true,"backend":"ultralight","plugin":"image-plugin"}` |

`render` 的常用参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `out` | 是 | 输出图片路径，必须是本地路径 |
| `template` | 二选一 | 模板文件名（不含 `.html`），需要配合 `template_dir` |
| `template_dir` | 否 | 模板所在目录，不写则用 `templates_dir` |
| `data` | 否 | 绑定进模板的 JSON 对象 |
| `html` | 二选一 | 直接给完整 HTML，此时不用 `template` |
| `width` / `height` | 否 | CSS 视口尺寸，默认 1000 × 550 |
| `scale` | 否 | 设备像素比，默认 2.0（2× 超采样） |
| `format` | 否 | `jpeg` 或 `png`，默认 `jpeg` |
| `quality` | 否 | JPEG 质量，1–100，默认 90 |
| `ready_expr` | 否 | 等待页面里某个 JS 表达式为真后再截图 |

请求示例：

```json
{
  "template": "demo",
  "template_dir": "plugins/image-plugin/templates",
  "data": { "title": "Hello", "subtitle": "FuyuBot" },
  "out": "D:/tmp/card.png",
  "width": 1200,
  "height": 630,
  "format": "png"
}
```

模板是纯 HTML，支持这些占位符：

| 写法 | 作用 |
| --- | --- |
| `{{ 字段 }}` | 输出并转义 |
| `{{& 字段 }}` 或 `{{{ 字段 }}}` | 原样输出 |
| `{{#if 字段}} … {{else}} … {{/if}}` | 条件 |
| `{{#each 字段}} … {{/each}}` | 循环，循环内可用 `this`、`@index`、`@first` |
| `{{ a.b }}` | 嵌套字段 |

字段不存在会报错（`#if` 里除外）。`templates/demo.html` 是可直接改的示例。

## 注意

- `render` 是同步调用，可能耗时 0.2–1 秒；调用方应放到独立线程或 `spawn_blocking`，
  不要阻塞 TDLib 更新回调。
- 渲染器以独立进程运行；它崩溃只会让当前这张图失败，不会影响机器人。
- `out` 必须可写，目录不存在会报错。
