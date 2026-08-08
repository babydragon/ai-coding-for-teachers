# 面向教师的 AI Coding 指南

> 让老师自己动手，用 AI 编程工具（Reasonix）制作给学生用的互动学习工具。
> 不需要会写代码 —— 会用中文把需求说清楚，就够了。

---

## 这份文档是给谁看的？

- **小学、初中各科老师**（尤其是不懂编程的）
- 想用 AI 提高备课、做教具效率的教师
- 想给班级做互动小游戏、练习页、课件页的班主任和科任老师

## 读完这份文档，你能做到什么？

| 目标 | 对应章节 |
| --- | --- |
| 看懂「Agent、LLM、MCP、Skill」这些词是什么意思 | [第一部分：AI Coding 基础知识](docs/01-ai-coding-basics/01-名词解释.md) |
| 明白 AI 是怎么一步步帮你干活的 | [Agent 编码原理](docs/01-ai-coding-basics/02-agent编码原理.md) |
| 装好 Reasonix，配好模型，会看界面 | [第二部分：工具使用手册](docs/02-tool-guide/01-安装与模型配置.md) |
| 亲手做一个「竖式乘法」动画小游戏 | [第三部分：动手做小游戏](docs/03-example/01-竖式乘法小游戏.md) |
| 用一份 AGENTS.md 让 AI 不乱发挥，按你的要求做 | [第四部分：AGENTS.md 的制定](docs/04-agents-md/01-什么是AGENTS.md.md) |
| 针对不同年级、科目快速选模板 | [第五部分：AGENTS.md 模板库](docs/05-templates/01-模板库.md) |
| 快速查词、查常见问题 | [附录：术语速查与 FAQ](docs/附录-术语速查与FAQ.md) |

## 建议的阅读路径

```
第一次接触 AI 编程的老师：
  名词解释 → Agent 原理 → 安装配置 → 跟着做小游戏 → 了解 AGENTS.md

已经会用 Reasonix 的老师：
  直接看第三部分做游戏，再看第四、五部分把 AGENTS.md 用起来
```

## 配套资源

- [示例游戏成品（竖式乘法，可直接双击打开）](examples/竖式乘法游戏/index.html)
- [可复制的 AGENTS.md 模板文件](templates/)

## 导出与发布

这份文档可以用一行命令导出成 PDF 或单文件网页版（**零依赖**：只需要系统里有 Python 3 和任意一个浏览器，Chrome/Edge 均可，无需安装任何库）：

```bash
./export.sh                # 导出完整 PDF 到 dist/
./export.sh --html         # 导出单文件 HTML（适合发布到网页）
./export.sh --file 路径.md  # 只导出某一个章节
./export.sh --out 自定义名   # 自定义输出文件名
```

- **离线阅读/打印**：用 `./export.sh` 得到 PDF，发给同事、打印都很方便。
- **在线查看（推荐给老师）**：把仓库推送到 GitHub，所有 `.md` 文件在 GitHub 上可直接阅读，章节之间的链接自动可点，无需任何配置。
- **做成好看的网页**：用 `./export.sh --html` 生成单文件 HTML，上传到 GitHub Pages 或 Cloudflare Pages 即可在线访问（参见 [发布到网页的三种方式](docs/02-tool-guide/03-发布到网页.md)）。

### 如何添加图片（如软件截图）

1. **图片统一放在根目录 `assets/` 文件夹**（没有就新建一个）。
2. 在章节里用相对路径引用，`alt` 写一句说明（屏幕阅读器也能读）：

   ```markdown
   ![Reasonix 主界面截图](../assets/reasonix-主界面.png)
   ```

   > ⚠️ 路径里的 `../` 是根据「md 文件所在的文件夹层级」来写的：`docs/01-ai-coding-basics/` 下的文件引用 `assets/` 要用 `../../assets/`；`docs/02-tool-guide/` 下用 `../assets/`。
3. 正常导出即可，**无需任何额外操作**：

   - **PDF / 单文件 HTML**：`export.sh` 会自动把图片以 base64 内联进文件，导出后图片照常显示，不需要带着图片文件夹一起拷贝。
   - **GitHub 直接查看**：相对路径的图片在 GitHub 上也能正常显示。
   - 若某张图找不到，导出时会打印 `⚠️ 找不到图片` 警告，但不会中断导出——检查一下路径即可。

### 文档约定

- 文中的 `Reasonix` 指本工具（桌面 GUI 版本）。
- 界面描述以 Reasonix 桌面版 v1.19.x 为基准，不同小版本可能略有差异。
- 需要你在电脑上操作的地方，都用「👉 动手做」标记。
- 提醒你注意的地方，都用「⚠️ 注意」标记。

## 更新日志

| 日期 | 内容 |
| --- | --- |
| 2026-08 | 初版：五个部分 + 附录全部完成 |
| 2026-08 | 新增「发布到网页」章节与 export.sh 导出脚本（PDF / 单文件 HTML） |
| 2026-08 | 发布到 GitHub（[github.com/babydragon/ai-coding-for-teachers](https://github.com/babydragon/ai-coding-for-teachers)），采用 CC BY 4.0 许可 |

## 许可证

本作品采用 [知识共享署名 4.0 国际许可协议（CC BY 4.0）](https://creativecommons.org/licenses/by/4.0/deed.zh-hans) 授权。

您可以自由地共享、复制、分发、修改本作品（包括用于教学和商业用途），唯一要求是保留对原作者（babydragon）的署名。详见 [LICENSE](LICENSE)。

---

▶️ **开始阅读：** [第一部分 · 名词解释 —— 认识 AI 编程里的基本词汇](docs/01-ai-coding-basics/01-名词解释.md)
