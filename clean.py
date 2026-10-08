"""Cleaning rules for THE DATA HUNT R2. Keeps decisions explicit and auditable."""
from pathlib import Path

import numpy as np
import pandas as pd


def clean_orders(source: str | Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(source)
    duplicate_mask = raw.duplicated(keep="first")
    duplicate_revenue = float(raw.loc[duplicate_mask, "revenue"].sum())
    duplicate_profit = float(raw.loc[duplicate_mask, "profit"].sum())
    df = raw.drop_duplicates().copy()
    duplicate_rows = len(raw) - len(df)
    bad_discount = df.discount_pct > 1.0
    bad_rows = df.loc[bad_discount].copy()
    df = df.loc[~bad_discount].copy()
    negative_shipping = df.shipping_days < 0
    negative_shipping_count = int(negative_shipping.sum())
    df.loc[negative_shipping, "shipping_days"] = np.nan
    df["order_date"] = pd.to_datetime(df.order_date)
    df["month"] = df.order_date.dt.month
    df["month_name"] = df.order_date.dt.strftime("%b")
    df["cat_sub"] = df.category + " / " + df.subcategory
    df["age_group"] = pd.cut(
        df.customer_age, [17, 24, 34, 44, 54, 100],
        labels=["18-24", "25-34", "35-44", "45-54", "55+"],
    )
    df["is_delivered"] = df.order_status.eq("Delivered")
    df["is_returned"] = df.order_status.eq("Returned")
    df["is_cancelled"] = df.order_status.eq("Cancelled")
    df["is_pending"] = df.order_status.eq("Pending")
    # Sensitivity only: the list-price cost assumption is not observed fact.
    df["profit_list_cost"] = df.revenue - df.gross_sales * df.cost_ratio
    audit = {
        "raw_rows": len(raw), "duplicate_rows": duplicate_rows,
        "bad_discount_rows": int(bad_discount.sum()),
        "bad_discount_revenue": float(bad_rows.revenue.sum()),
        "negative_shipping_rows": negative_shipping_count,
        "clean_rows": len(df), "clean_orders": int(df.order_id.nunique()),
        "raw_revenue": float(raw.revenue.sum()), "raw_profit": float(raw.profit.sum()),
        "duplicate_revenue": duplicate_revenue, "duplicate_profit": duplicate_profit,
    }
    return df, audit


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    cleaned, log = clean_orders(root / "data" / "R_Questions.csv")
    cleaned.to_csv(root / "data" / "cleaned_orders.csv", index=False)
    print(log)
