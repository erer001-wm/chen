#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把本地修复后的文件推送到 GitHub 仓库 erer001-wm/chen（绕过网页上传）。

步骤：
  1. 打开 GitHub -> 右上角头像 -> Settings -> Developer settings
     -> Personal access tokens -> Tokens (classic) -> Generate new token
     -> 勾选 repo 权限 -> 生成，复制那一串 token。
  2. 在本文件所在目录打开终端（PowerShell），运行：
        python upload_to_chen.py
  3. 按提示粘贴 token（输入时不显示文字，粘贴后回车即可）。
  4. 脚本会把 index.html 和 .github/workflows/build-apk.yml 推上去，
     然后你去 Actions 重跑 build-apk.yml 构建新 APK。
"""
import base64
import getpass
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "erer001-wm/chen"
BRANCH = "main"
BASE = "https://api.github.com/repos/%s/contents" % REPO
ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = [
    ("index.html", "index.html"),
    (".github/workflows/build-apk.yml", ".github/workflows/build-apk.yml"),
]


def api(method, path, token, data=None):
    url = BASE + "/" + path
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "upload-script")
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode("utf-8")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 404 and method == "GET":
                return None  # 文件尚不存在（新建）
            print("  HTTP %d: %s" % (e.code, body[:400]))
            if attempt == 2:
                raise
        except Exception as e:
            print("  网络错误: %s (重试 %d/3)" % (e, attempt + 1))
            if attempt == 2:
                raise


def main():
    token = getpass.getpass("粘贴 GitHub Personal Access Token（输入不显示）: ").strip()
    if not token:
        print("未输入 token，退出。")
        sys.exit(1)
    ok = True
    for local, repo_path in FILES:
        local_path = os.path.join(ROOT, local)
        if not os.path.exists(local_path):
            print("缺少本地文件: %s" % local_path)
            ok = False
            continue
        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode("ascii")
        print("处理 %s ..." % repo_path)
        sha = None
        existing = api("GET", repo_path, token)
        if existing:
            try:
                sha = json.loads(existing)["sha"]
            except Exception:
                sha = None
        payload = {
            "message": "fix: 修复错题本分组/相机拍照/打卡计数",
            "content": content,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha
        try:
            api("PUT", repo_path, token, payload)
            print("  [OK] 已更新 %s" % repo_path)
        except Exception as e:
            print("  [失败] 上传 %s 失败: %s" % (repo_path, e))
            ok = False
    print("\n%s" % ("全部完成，去 Actions 重跑构建。" if ok else "有文件失败，请检查上面的错误。"))
    print("Actions 地址: https://github.com/%s/actions" % REPO)


if __name__ == "__main__":
    main()
