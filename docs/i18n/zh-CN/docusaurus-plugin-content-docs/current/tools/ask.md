---
title: "提问"
sidebar_position: 5
---

## 概述

`ask` 工具根据拉取请求的代码变更回答相关问题。提问时请尽量具体、清楚。
可以在任意拉取请求上评论来手动调用：

```
/ask "..."
```

## 使用示例

<img src="/img/ask_comment.png" alt="提问评论" width="512" />

<img src="/img/ask.png" alt="提问" width="512" />

## 对代码行提问 {#ask-lines}

可以在拉取请求的 diff 视图中，对特定代码行运行 `/ask`。工具会根据所选行中的代码变更回答问题。

- 点击行号旁的 “+” 以选中该行。
- 要选择多行，先点击第一行的 “+”，然后按住并拖动以选中其余行。
- 在评论框中写入 `/ask "..."`，然后按 `Add single comment` 按钮。

<img src="/img/Ask_line.png" alt="对代码行提问" width="512" />

请注意，该工具没有先前问题的“记忆”，每个问题都独立回答。

## 对图片提问

也可以针对评论中出现的图片提问，此时整个拉取请求代码会作为上下文。
<br>
基本语法是：

```
/ask "..."

[Image](https://real_link_to_image)
```

其中 `https://real_link_to_image` 是图片的直接链接。

请注意，GitHub 内置了在评论中粘贴图片的机制。但粘贴的图片不会提供直接链接。
要获得图片的直接链接，建议按以下步骤操作：

1\. 首先发布一条**只**包含图片的评论：

<img src="/img/ask_images1.png" alt="提问图片 1" width="512" />

2\. 引用回复该评论：

<img src="/img/ask_images2.png" alt="提问图片 2" width="512" />

3\. 在打开的界面中，于图片下方输入问题：

<img src="/img/ask_images3.png" alt="提问图片 3" width="512" />
<img src="/img/ask_images4.png" alt="提问图片 4" width="512" />

4\. 发布评论并收到回答：

<img src="/img/ask_images5.png" alt="提问图片 5" width="512" />

完整视频教程见[此处](https://codium.ai/images/pr_agent/ask_image_video.mov)

## 配置选项

<details open>
<summary>通用选项</summary>

<table>
  <tr>
    <td><b>ask_heading</b></td>
    <td>
      顶层 <code>/ask</code> 回答的纯文本标题。默认值为 <code>Ask</code>。
      Markdown 渲染器会转义标点，以保持周围格式和 ❓ 表情固定，
      而纯文本转换器会发布所配置的文本，不带转义字符。
      这不影响 <code>/ask_line</code> 回复，也不影响 <code>Answer</code> 节标题。
    </td>
  </tr>
  <tr>
    <td><b>extra_instructions</b></td>
    <td>给工具的可选附加指令。例如：“Do not answer questions that ask to rate PR quality on a scale of 1 to 10. Instead, tell the user this type of question is not allowed.”</td>
  </tr>
  <tr>
    <td><b>enable_help_text</b></td>
    <td>设为 true 时，工具会在评论中显示帮助文本。默认值为 false。</td>
  </tr>
  <tr>
    <td><b>use_conversation_history</b></td>
    <td>设为 true 时，工具在回答特定代码行上的问题时会使用对话历史（仅 GitHub）。默认值为 true。</td>
  </tr>
</table>

</details>

配置文件中的用法示例：

```toml
[pr_questions]
ask_heading = "Architecture Question"
extra_instructions = "Do not answer questions that ask to rate PR quality on a scale of 1 to 10."
```

上面的标题会渲染为 `### **Architecture Question** ❓`。

拉取请求评论中的用法示例：

```
/ask "What does this change do?" --pr_questions.extra_instructions="Answer in one short paragraph."
```
