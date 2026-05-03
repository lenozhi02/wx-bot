
# 1. 先拉取远程最新（避免冲突）
git pull firt main --rebase

# 2. 查看变更
git status

# 3. 添加并提交
git add -A
git commit -m "feat: xxx"

# 4. 推送
git push firt main
