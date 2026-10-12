# AstrBot Veo 视频插件

通过您自己的 Ace Data Cloud 账号，在 AstrBot 对话中生成一条 Veo 视频。`veo_generate_video` 提交一次文生视频或图生视频任务，`veo_get_task` 用同一个任务 ID 查询最终结果。

[English guide](../README.md) · [Veo 视频接口](https://platform.acedata.cloud/documents/veo-videos?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veoastrbot_readme_documents_veo_videos) · [Veo 任务接口](https://platform.acedata.cloud/documents/veo-tasks?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veoastrbot_readme_documents_veo_tasks) · [当前价格](https://platform.acedata.cloud/services/veo?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veoastrbot_readme_services_veo)

## 查找与安装

在 AstrBot WebUI 中打开 **扩展 → 插件 → AstrBot 插件市场**，搜索 **Veo**。核对卡片名称 **Veo by Ace Data Cloud**、作者 **acedatacloud** 和[当前 Veo 服务图标](https://cdn.acedata.cloud/8nxyy9.jpg)，安装后在**已安装**页检查加载状态。

官方 AstrBot Cloud 上架仍待完成。源码合并后，可通过**已安装 → 安装 (+) → 从 URL 安装**并填写 `https://github.com/AceDataCloud/VeoAstrBot` 预览。通过 URL 安装不代表已在官方市场上架。

## 配置密钥

首次使用请先注册并登录；如果应用页还没有通用应用，点击 **初始化通用应用（Initialize General Application）**，再按下面步骤管理密钥。

在 [Ace Data Cloud 应用管理](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen&utm_content=veoastrbot_readme_api_key)复制生成 API Key，或创建同时允许 `/veo/videos` 与 `/veo/tasks` 的 Key。提交前查看当前模型、分辨率价格和余额。将 Key 填入插件的 **Ace Data Cloud generation API key with Veo access** 配置项，不要添加 `Bearer `，也不要使用 `platform-...` 管理令牌。AstrBot WebUI 会遮蔽显示此字段，但原值保存在数据目录中，请保护该目录。

选择支持工具调用的对话模型，并在当前对话的 profile 与 persona 中允许两个 Veo 工具。

## 生成一次，然后查询

可以对机器人说：

> 用 `veo_generate_video` 生成一条黄色纸风筝从绿色草地升起的视频，模型 `veo31-fast`，使用默认分辨率。只提交一次并告诉我任务 ID。

工具会异步提交一次 `POST /veo/videos` 请求，返回 `status: submitted` 和任务 ID。这时还不能认为视频已完成。保存 ID，随后说：

> 用 `veo_get_task` 查询刚才的准确任务 ID `<task_id>`，告诉我状态与最终视频链接，不要重新生成。

如果仍是 pending，稍后继续查询同一个 ID。只有 `status: succeeded`、`success: true` 和最终 HTTPS 视频链接同时出现才算完成。插件不会自动重试付费提交。

首版文生视频支持 `veo3`、`veo3-fast`、`veo31` 和 `veo31-fast`。要让您有权处理的图片动起来，传入公开的 HTTPS `image_url`；该图生视频模式的 `aspect_ratio` 可为 `16:9` 或 `9:16`。省略 `resolution` 时使用 API 默认分辨率；也可在核对当前价格后明确选择 `1080p`、`4k` 或 `gif`。多图 ingredients、1080p 升采样和其他高级操作尚未覆盖。

## 核验与排查

在 Ace Data Cloud 用量记录中优先按返回的 trace ID 核对。任务结果可能包含以 Credits 计的公开 `cost` 字段；以实时用量记录为扣费依据。任务查询只读取已有任务，不会再次生成。

| 现象 | 检查 |
| --- | --- |
| 插件加载失败 | AstrBot 版本、**加载失败的插件**和**数据与日志 → 日志**。 |
| 看不到工具 | 插件启用、当前 profile 与 persona 允许两个工具、对话模型支持工具调用。 |
| HTTP 401/403 | Key 类型、两个 API 路径的权限和账号访问权限。 |
| 提交后网络报错 | 再次生成前先看请求历史；超时也可能已创建付费任务。 |
| 任务仍在进行 | 稍后查询同一个任务 ID。 |
| 任务失败 | 用任务 ID 或 trace ID 查请求历史。 |

Key 只会发送到 `https://api.acedata.cloud`，重定向会被拒绝。插件只把最终视频链接和公开的费用字段交给对话模型，不返回内部原始数据。运行时仅用 Python 标准库。

## 验收与品牌图标

在官方 AstrBot `v4.28.2` 的隔离实例中，editable 安装成功注册两个工具。ChatUI 用 `veo31-fast` 提交了一次文生视频任务，并通过 `veo_get_task` 查询同一个 ID 两次：首次 pending，第二次成功，没有重复生成。最终 MP4 返回 HTTP 200、`video/mp4`，H.264 视频和 AAC 音频，1280×720、8 秒。准确 trace ID 对应一条成功的 `/veo/videos` 用量记录，实扣 0.648 Credits；任务返回原价 0.72 Credits。见[脱敏实测证据](../tests/e2e-results.json)。图生视频、其他模型和可选分辨率仅做结构校验，未实际生成。这只是本地 editable 安装；Cloud 审核、市场安装以及市场包的首次调用仍待完成。

`logo.png` 是[当前 Veo 服务图标](https://cdn.acedata.cloud/8nxyy9.jpg)不改变画面的 PNG 编码，900×900。源 JPEG 的 SHA-256 为 `26bf44b131bf91b6e7b4ce1df82925346b7e850583d8f5fa8f449d4350fd5af8`；打包 PNG 的 SHA-256 为 `b9a18c80092c522aa8e11f4918c13def1ba340831bda83f9c935f76e0d011fa2`。
