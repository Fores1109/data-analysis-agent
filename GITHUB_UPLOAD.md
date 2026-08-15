# 🚀 上传到 GitHub 教程

> 你的项目已经在本地初始化好 git 仓库并完成了提交，**只差最后两步：在 GitHub 建仓库 + push**。
> 核心就 3 条命令，下面详细拆解，跟着做即可。

---

## 第 0 步：准备

1. 注册 GitHub 账号：https://github.com/signup （免费，3 分钟）
2. 记下你的**用户名**（登录后右上角头像旁的名字）

## 第 1 步：在 GitHub 网页上新建空仓库

1. 登录后点右上角 **＋** → **New repository**
2. Repository name 填：`data-analysis-agent`
3. 选 **Public**（求职作品建议公开，面试官才能看）
4. **不要勾选** Add a README / .gitignore / license（本地已有，勾了会冲突）
5. 点 **Create repository**

创建后页面会显示几条命令，我们只需要其中 3 条（第 2 步用）。

## 第 2 步：本地关联并推送（PowerShell）

```powershell
cd D:\dsharness\data-analysis-agent
git remote add origin https://github.com/你的用户名/data-analysis-agent.git
git branch -M main
git push -u origin main
```

> 也可以直接用我写好的脚本（自动设置你的名字 + 关联仓库 + 推送）：
> ```powershell
> .\scripts\push_github.ps1 -Username 你的用户名
> ```

## 第 3 步：身份验证（第一次 push 才会遇到）

GitHub 从 2021 年起**不允许用账号密码** push，要用 **Personal Access Token（个人访问令牌）** 当密码：

1. 打开 https://github.com/settings/tokens → **Generate new token** → **Tokens (classic)**
2. Note 随便写（如 `push-data-agent`）；Expiration 选 90 天或 No expiration
3. **勾选 `repo` 那一项**（完整仓库权限）→ 拉到最下 Generate token
4. **立即复制**令牌（只显示一次！形如 `ghp_xxxx...`）
5. 回到 PowerShell 执行 `git push -u origin main`：
   - Username 输入你的 GitHub 用户名
   - Password **粘贴令牌**（终端不显示输入内容，直接回车）
6. 看到 `main -> main` 和进度条即成功 🎉

## 第 4 步：验证

浏览器打开 `https://github.com/你的用户名/data-analysis-agent`，应该能看到 README 渲染、代码文件、数据目录。

## 以后更新代码

```powershell
cd D:\dsharness\data-analysis-agent
git add -A
git commit -m "更新说明"
git push
```

## ❓ 常见问题

| 问题 | 解决 |
|---|---|
| `remote origin already exists` | 先 `git remote remove origin` 再 add |
| push 报 `403` / `Authentication failed` | 令牌没勾 repo 权限或已过期，重新生成 |
| push 报 `Failed to connect` | 网络问题，重试；或改用 SSH（见下） |
| 想删掉传错的仓库 | GitHub 仓库页 → Settings → Danger Zone → Delete this repository |
| `.env` 会不会泄露密钥？ | 不会，`.gitignore` 已排除 `.env`，确认：`git ls-files | findstr env` 只应看到 `.env.example` |
| 仓库太大？ | 56MB 数据没问题（GitHub 单仓库限 1GB+，单文件限 100MB） |

## 进阶：SSH 方式（可免密推送，推荐长期用）

```powershell
ssh-keygen -t ed25519 -C "你的邮箱"     # 一路回车
type $env:USERPROFILE\.ssh\id_ed25519.pub   # 复制输出
```
GitHub → Settings → **SSH and GPG keys** → New SSH key → 粘贴保存。然后：

```powershell
git remote set-url origin git@github.com:你的用户名/data-analysis-agent.git
git push -u origin main
```
以后推送不再要输令牌。
