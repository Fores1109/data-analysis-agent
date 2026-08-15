# 一键推送项目到 GitHub
# 用法：.\scripts\push_github.ps1 -Username 你的GitHub用户名
param(
    [Parameter(Mandatory = $true)][string]$Username,
    [string]$RepoName = "data-analysis-agent"
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# 1. 设置作者信息（占位符改为你的）
git config user.name $Username
git config user.email "$Username@users.noreply.github.com"

# 2. 关联远程仓库（已存在则先移除）
git remote remove origin 2>$null | Out-Null
git remote add origin "https://github.com/$Username/$RepoName.git"

# 3. 主分支名统一为 main 并推送
git branch -M main
Write-Host ''
Write-Host "正在推送 https://github.com/$Username/$RepoName.git ..." -ForegroundColor Cyan
Write-Host '如果提示输入 Username / Password：用户名填你的 GitHub 用户名，密码粘贴 Personal Access Token（见 GITHUB_UPLOAD.md 第 3 步）' -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 推送成功！打开 https://github.com/$Username/$RepoName 查看" -ForegroundColor Green
} else {
    Write-Host '❌ 推送失败，请检查：用户名是否正确 / 令牌是否有效（见 GITHUB_UPLOAD.md 常见问题）' -ForegroundColor Red
}
