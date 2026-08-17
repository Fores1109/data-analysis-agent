#!/usr/bin/env python3
"""下载 Olist 巴西电商数据集到 data/olist/（公开 GitHub 镜像，无需 Kaggle 账号）。

用法：
    python scripts/download_data.py              # 下载全部 CSV（已存在则跳过）
    python scripts/download_data.py --force      # 强制重新下载
    python scripts/download_data.py --dry-run    # 只检查远程文件是否存在，不下载

说明：
    - 数据集原始来源为 Kaggle（olistbr/brazilian-ecommerce）；
      本脚本使用包含完整 8 个 CSV 的公开 GitHub 镜像
      （angelynarthur/brazilian-ecommerce，文件与 Kaggle 原版一致），
      免去 Kaggle 账号 / API 凭据。
    - 全部文件约 60MB，下载后位于 data/olist/，已被 .gitignore 排除，不会进入 Git 仓库。
"""
import argparse
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "olist"

BASE_URL = "https://raw.githubusercontent.com/angelynarthur/brazilian-ecommerce/master/"
FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
]
MIN_EXPECTED_BYTES = 50_000  # 低于该大小视为下载失败（防止 404 页面被存成文件）


def _open(url: str, timeout: int, retries: int = 2):
    """带重试的 urlopen：网络抖动/代理不稳定时自动重试（默认额外 2 次）。"""
    req = urllib.request.Request(url, headers={"User-Agent": "data-analysis-agent"})
    last_err = None
    for attempt in range(retries + 1):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except (urllib.error.URLError, OSError, ValueError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))  # 简单退避
    raise last_err


def _reachable(url: str) -> bool:
    """用 Range GET 检查远程文件可下载（raw.githubusercontent 对 HEAD 支持不稳定）。"""
    try:
        resp = _open(url, timeout=30)
    except Exception:  # noqa: BLE001 - 探测失败即视为不可达
        return False
    with resp:
        return resp.status in (200, 206)


def download(url: str, dest: pathlib.Path, force: bool = False) -> str:
    if dest.exists() and dest.stat().st_size > MIN_EXPECTED_BYTES and not force:
        return f"跳过（已存在 {dest.stat().st_size / 1e6:.1f}MB）"
    print(f"  下载 {dest.name} ...", flush=True)
    with _open(url, timeout=180) as resp, open(dest, "wb") as f:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    size = dest.stat().st_size
    if size < MIN_EXPECTED_BYTES:
        dest.unlink(missing_ok=True)
        return f"失败（下载内容过小，疑似 404：{url}）"
    return f"完成（{size / 1e6:.1f}MB）"


def main() -> int:
    ap = argparse.ArgumentParser(description="下载 Olist 数据集到 data/olist/")
    ap.add_argument("--force", action="store_true", help="强制重新下载")
    ap.add_argument("--dry-run", action="store_true", help="只检查远程文件是否存在，不下载")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ok, fail = 0, 0
    for name in FILES:
        url = BASE_URL + name
        if args.dry_run:
            status = "存在" if _reachable(url) else "不存在/不可达"
            print(f"[dry-run] {name}: {status}")
            ok += status == "存在"
            fail += status != "存在"
            continue
        try:
            print("  -", download(url, DATA_DIR / name, force=args.force))
            ok += 1
        except Exception as e:  # noqa: BLE001 - 单文件失败不中断
            print(f"  - 失败：{e}")
            fail += 1

    print(f"\n完成：成功 {ok}，失败 {fail}（文件位于 {DATA_DIR}）")
    if fail:
        print("提示：网络受限时可手动从 https://github.com/angelynarthur/brazilian-ecommerce 下载后放入 data/olist/。")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
