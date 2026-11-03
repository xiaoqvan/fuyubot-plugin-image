# image-plugin

FuyuBot 的 HTML 出图插件：注册 **`image.render`** 服务，用 Ultralight 2.0 把 HTML
截成 JPEG / PNG。插件本身没有任何业务字段——模板、数据、尺寸都由调用方给。

```text
任意插件
  │  get_service("image.render") → ServiceVTable
  │  render({"template":"...","data":{...},"out":"..."})
  ▼
image_plugin.dll（宿主进程内的 cdylib，只发请求）
  │  JSON 行协议，stdin/stdout
  ▼
image-shot（独立进程，独占主线程）
  │  Ultralight 2.0：绑定数据 → 加载 HTML → 截图
  ▼
  JPEG/PNG 路径
```

- 插件 id：`image-plugin`
- 产物：`image_plugin.dll` + `image-shot.exe`（Linux/macOS 对应 `libimage_plugin.so` / `image-shot`）
- ABI：5（`fuyubot-abi 0.1.2`）

## 为什么是两个产物

Ultralight 要求 Renderer 在**主线程**创建并驱动，而宿主主线程归 tokio，插件里抢不到。
渲染器单独成进程：崩了只崩一张图，升级渲染器也不用重启宿主。两个产物来自同一个 crate，
请求类型只有一份，不会出现两边字段对不上。

## 服务方法

| 方法 | 入参 | 出参 |
| --- | --- | --- |
| `render` | `{"template","template_dir","data","out","width","height","scale","format","quality","ready_expr"}` 或 `{"html","out",...}` | `{"ok":true,"path","width","height","bytes","ms"}` |
| `ping` | 任意 | `{"ok":true,"backend":"ultralight","plugin":"image-plugin","info":{...}}` |

`out` 必填：交给 TDLib 的图片必须是本地路径，所以图一定落盘。

服务是**同步**的：调用方要放进 `spawn_blocking` 或专用线程，别塞进 TDLib 更新回调。

## 模板

模板是纯 HTML，加六种标签：

| 写法 | 作用 |
| --- | --- |
| `{{ 字段 }}` | 输出并 HTML 转义 |
| `{{& 字段 }}` / `{{{ 字段 }}}` | 原样输出 |
| `{{#if 字段}} … {{else}} … {{/if}}` | 条件块 |
| `{{#each 字段}} … {{/each}}` | 遍历（循环里 `this` / `@index` / `@first`……） |
| `{{ a.b }}` | 嵌套字段 |

字段不存在会直接报错（`#if` 除外）。模板跟业务走，不放插件里；`templates/demo.html`
只是接口示例。

## 启动配置（可省略）

```json
{ "binary": "D:/.../image-shot.exe", "templates_dir": "D:/.../templates" }
```

`templates_dir` 是请求里没给 `template_dir` 时的默认值。

## 部署

目录包布局（推荐）：

```text
plugins/
└── image-plugin/
    ├── plugin.json
    └── bin/
        ├── image_plugin.dll
        ├── image-shot.exe
        └── ultralight/               # Ultralight 运行时（可选放这里）
            ├── Ultralight.dll
            ├── UltralightCore.dll
            ├── WebCore.dll
            ├── AppCore.dll
            └── resources/{icudt67l.dat,cacert.pem}
```

`image-shot` 查找顺序：`IMAGE_SHOT_BIN` → `plugins/<id>/bin/` → `plugins/<id>/` →
`plugins/` → `plugins/ultralight/` → 宿主 exe 同级 → 仓库 target（开发态）。
Ultralight DLL 查找：`ULTRALIGHT_DIR` → `image-shot` 同级 → 同级 `ultralight/`。

运行时（Ultralight SDK 的 `bin/` + `resources/`）**不随本仓发布**，部署时放到上面任一位置。

## 构建

```bash
cargo build --release
# Windows: target/release/image_plugin.dll + image-shot.exe

cargo run --release --bin image-shot -- --check   # 运行时自检
```

## 发布

推 `v<版本>` tag，CI 按平台打包（Windows x86_64 / aarch64、Linux x86_64 / aarch64、
macOS aarch64）：

```text
image-plugin-<version>-<平台>.zip
├── plugin.json
└── bin/
    ├── image_plugin.dll
    └── image-shot.exe
```

## License

MIT OR Apache-2.0
