# src/task.py
import os
import io
import base64
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import markdown
from datetime import datetime
import argparse

# ---------------- 工具 ----------------

def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    # 固定邊界與 DPI，避免每張圖被不同程度裁切
    fig.savefig(buf, format="png", bbox_inches=None, dpi=150, pad_inches=0.05)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")

def _daily_series(sales: pd.DataFrame, sales_info: pd.DataFrame) -> pd.DataFrame:
    df = sales.merge(sales_info, on="product_code")
    df["total"] = df["amount"] * df["price"]
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    return df.groupby("sale_date", as_index=False)["total"].sum().sort_values("sale_date")

def group_by_sales_id(sales, sales_info, top_n=None):
    df = sales.merge(sales_info, on="product_code")
    df["total"] = df["amount"] * df["price"]
    out = df.groupby("sale_id", as_index=False)["total"].sum().sort_values("total", ascending=False)
    return out.head(top_n) if top_n else out

def group_by_product_name(sales, sales_info, top_n=None):
    df = sales.merge(sales_info, on="product_code")
    df["total"] = df["amount"] * df["price"]
    out = df.groupby("product_name", as_index=False)["total"].sum().sort_values("total", ascending=False)
    return out.head(top_n) if top_n else out

def group_by_client_name(sales, sales_info, client, top_n=None):
    df = sales.merge(sales_info[["product_code", "price"]], on="product_code", how="left")
    df = df.merge(client[["client_id", "client_name"]], on="client_id", how="left")
    df["total"] = df["amount"] * df["price"]
    out = df.groupby("client_name", as_index=False)["total"].sum().sort_values("total", ascending=False)
    return out.head(top_n) if top_n else out

def pie_b64(df, label_col, title):
    fig, ax = plt.subplots(figsize=(4.2, 4.2), constrained_layout=False)
    wedges, texts, autotexts = ax.pie(
        df["total"],
        labels=df[label_col],
        autopct="%.1f%%",
        startangle=90,
        labeldistance=1.05,   # 統一標籤距離
        pctdistance=0.75,
        radius=1.0
        )
    ax.set_aspect("equal")

    # ax.set_title(title, pad=4)

    # 圖例放下方，避免影響圓的可用空間
    ax.legend(
        wedges,
        df[label_col],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=2,
        frameon=False,
        fontsize=8
    )

    # 固定子圖邊界，確保三張圖留白一致
    fig.subplots_adjust(left=0.15, right=0.95, top=0.88, bottom=0.12)

    return _fig_to_base64(fig)

def line_daily_b64(sales: pd.DataFrame, sales_info: pd.DataFrame, max_xticks: int = 12) -> str:
    plt.rcParams.update({
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
    })

    daily = _daily_series(sales, sales_info).sort_values("sale_date")
    x = daily["sale_date"].dt.strftime("%Y-%m-%d")

    fig, ax = plt.subplots(figsize=(5, 1.5))
    ax.plot(daily["sale_date"], daily["total"], linewidth=1)

    step = max(1, len(x) // max_xticks)
    ax.set_xticks(daily["sale_date"][::step])
    ax.set_xticklabels(x[::step], rotation=45, ha="right")

    ax.set_xlabel("Sale Date", labelpad=3)
    ax.set_ylabel("Total Sales")
    # ax.set_title("Daily Sales Trend", pad=4)

    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.32)
    return _fig_to_base64(fig)

def render_template(md_template: str, mapping: dict) -> str:
    """以 {{key}} 形式替換，避免與 CSS 的大括號衝突。"""
    out = md_template
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out

# ---------------- 主流程 ----------------

if __name__ == "__main__":
    # 路徑
    BASE = os.path.dirname(os.path.abspath(__file__))             # .../projects/Report_Automation_System/src
    ROOT = os.path.abspath(os.path.join(BASE, ".."))              # .../projects/Report_Automation_System

    TEMPLATE_MD = os.path.join(ROOT, "templates/pdf_templates.md")          # 你的模板放 src/pdf_templates.md
    
    generated_on_filename = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_DIR = os.path.join(ROOT, "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    OUT_HTML = os.path.join(OUTPUT_DIR, f"report_{generated_on_filename}.html")
    OUT_PDF  = os.path.join(OUTPUT_DIR, f"report_{generated_on_filename}.pdf")

    # weasyprint.exe 路徑（放專案根目錄）
    WEASY_EXE = os.path.join(ROOT, "weasyprint.exe")
    if not os.path.isfile(WEASY_EXE):
        raise FileNotFoundError(f"找不到 weasyprint.exe：{WEASY_EXE}")

    # 存取參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--sales", required=True, help="Path to sales.csv")
    parser.add_argument("--sales-info", required=True, help="Path to sales_info.csv")
    parser.add_argument("--client", required=True, help="Path to client.csv")
    args = parser.parse_args()

    sales = pd.read_csv(args.sales)
    sales_info = pd.read_csv(args.sales_info)
    client = pd.read_csv(args.client)

    # 聚合與作圖
    by_client = group_by_client_name(sales, sales_info, client, top_n=6)
    by_prod   = group_by_product_name(sales, sales_info, top_n=6)
    by_id     = group_by_sales_id(sales, sales_info, top_n=6)

    img_client = pie_b64(by_client, "client_name", "By Client")
    img_prod   = pie_b64(by_prod, "product_name", "By Product")
    img_id     = pie_b64(by_id, "sale_id", "By Sale ID")
    img_line   = line_daily_b64(sales, sales_info)

    total_rev   = f"{by_client['total'].sum():,.0f}"
    top_client  = by_client.iloc[0]["client_name"] if len(by_client) else "N/A"
    top_product = by_prod.iloc[0]["product_name"] if len(by_prod) else "N/A"

    # 讀模板並代入
    with open(TEMPLATE_MD, "r", encoding="utf-8") as f:
        md_tpl = f.read()

    generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    md_text = render_template(md_tpl, {
        "img_client": img_client,
        "img_prod": img_prod,
        "img_id": img_id,
        "img_line": img_line,
        "total_rev": total_rev,
        "top_client": top_client,
        "top_product": top_product,
        "generated_on": generated_on,
    })

    # Markdown -> HTML（保留你在 md 裡的 <style> 與 HTML）
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "tables", "sane_lists", "toc", "attr_list"]
    )
    html_full = "<!doctype html><html><meta charset='utf-8'><body>" + html_body + "</body></html>"

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_full)

    # HTML -> PDF（呼叫獨立可執行檔，不需任何系統 DLL）
    subprocess.run([WEASY_EXE, OUT_HTML, OUT_PDF], check=True)

    print("OK ->", OUT_PDF)
