import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

out_dir = Path("files")
out_dir.mkdir(exist_ok=True)

# ---- Sales ----
# 一筆交易：哪位客戶，在什麼時間，買了多少
np.random.seed(0)
dates = pd.date_range(end=datetime.today(), periods=30).tolist()

df_sales = pd.DataFrame({
    "sale_id": np.char.zfill(np.random.randint(1, 25, size=3000).astype(str), 4),
    "client_id": np.random.randint(1001, 1357, size=3000),
    "sale_date": sorted(np.random.choice(dates, size=3000)),
    "amount": np.random.randint(1000, 8000, size=3000),
    "product_code": np.random.choice(["A01","A02","B11","B21"], size=3000)
})

# ---- Client ----
# 客戶基本資料
df_client = pd.DataFrame({
    "client_id": [1001, 1002, 1003, 1004, 1005],
    "client_name": ["Ravindo Co","Alpha Ltd","Zen Corp","MLine Inc","BlueStar"],
    "region": ["North","East","East","South","North"]
})

# ---- Sales_info ----
# 產品資訊，例如價格與分類
df_sales_info = pd.DataFrame({
    "product_code": ["A01","A02","B11","B21"],
    "product_name": ["Widget S","Widget L","Gadget X","Gadget Y"],
    "category": ["Widget","Widget","Gadget","Gadget"],
    "price": [500, 800, 1200, 1500]
})

# print(df_sales.head())
# print(df_client)
# print(df_sales_info)
# print(df_sales['sale_date'])


df_sales.to_csv(out_dir / "sales.csv", index=False)
df_client.to_csv(out_dir / "client.csv", index=False)
df_sales_info.to_csv(out_dir / "sales_info.csv", index=False)