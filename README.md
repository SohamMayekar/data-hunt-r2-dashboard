AI used: Yes, for [fill in] and we can explain every part.

# THE DATA HUNT, Round 2

Team name: [add team name]  
TeamID: [add TeamID]  
Members: [add member names]

## What this shows

The dashboard compares booked and delivered revenue, product margins, discount tiers, order outcomes and customer value. It uses one scrolling page with global filters. The default revenue basis is Booked.

## Cleaning

The app reads `data/R_Questions.csv` at startup and writes `data/cleaned_orders.csv`.

- Removed 20 exact duplicate rows.
- Removed 12 lines with discounts above 100%. Their recorded revenue was negative ₹8,592. The true discount is unknown.
- Set 10 negative shipping-day values to missing.
- Left other missing values blank. No imputation was used.
- Added category/subcategory labels, month, age bands and order-status flags.

The clean file contains 11,647 item lines, 7,995 orders and 1,492 customers.

## Q1 to Q5

### Q1. Money

Booked revenue is ₹47,291,531.56 and booked profit is ₹15,240,690.01. Margin is 32.23%. Electronics has the most revenue at ₹14,080,094. Sports has a large revenue share but a lower profit share: 19.9% of revenue and 17.4% of profit when calculated from the cleaned data. Fashion has the highest category margin at 35.6%.

### Q2. Trend

Revenue was broadly flat in 2025. July had the highest monthly revenue at ₹4,130,653. March had the highest profit. Revenue rose 3.3% from Q1 to Q4 while profit rose 1.0%; margin moved from 32.5% to 31.8%. The data does not show campaign, traffic or stock information, so it cannot explain monthly order changes.

### Q3. Problems

There is no statistically clear return or cancellation hotspot in the tested categories, regions, payment methods or shipping bands. The overall return rate is 7.78% and cancellation rate is 8.23%. Shipping time, discount and rating relationships are negligible. The analysis does not support a claim that faster shipping or deeper discounts would fix returns or ratings.

### Q4. Customers

The top 10% of customers account for 21.4% of profit. The top 20% account for 37.4%. Customer value is more closely associated with purchase frequency than the demographic fields. Mumbai has the most city profit, while Lucknow has the highest profit per customer.

### Q5. Actions

1. Review the 28 products below 26% margin. They represent ₹13.81M revenue and ₹3.02M profit. A 30% margin target would add about ₹1.12M profit if revenue stayed constant. The data cannot show whether higher prices would reduce orders.
2. Test a 10% discount cap on one category. The 15% and 20% tiers account for ₹1.69M in discounts across 2,334 item lines. The cap would retain about ₹0.65M revenue and ₹0.21M profit under the recorded cost formula. The data cannot show what buyers would have done without a discount.
3. Resolve old Pending orders. There are 291 Pending orders older than 90 days, with ₹1.67M in booked revenue at the 31 December 2025 reference date. No customer group stands out as the problem.

## Other findings and limits

The cost formula calculates estimated cost from discounted revenue. This makes recorded margin look nearly flat across discount tiers. The dashboard also shows a sensitivity that holds cost at list price. That line is based on an assumption, not an observed cost.

The source uses the same subcategory label, Accessories, in Electronics and Fashion. Product views use product IDs. Customer age has a floor at 18, so age bands are descriptive only. Ratings and shipping times appear on some non-delivered lines. Profit and revenue are recorded for every status, including cancelled orders.

Other checks found 20 duplicate rows, 12 impossible discount lines and 10 negative shipping values. These are removed or marked missing as described above. The 100 products have margins from 18.3% to 47.6%, even though category margins vary less. The 86 customers recorded at age 18 may reflect an age floor. These ages are not used to claim that 18-year-olds behave differently.

Pending age uses 31 December 2025 as its reference date. The data cannot establish why orders changed over time, whether discounts caused higher sales, or whether price changes would alter demand.

## Run it

Use Python 3.10 or newer. From the repository folder:

```sh
pip install -r requirements.txt
streamlit run app.py
```

The raw CSV is `data/R_Questions.csv`. The app applies `clean.py` on startup and refreshes `data/cleaned_orders.csv`. It prints the Section O validation values and results to the terminal before rendering the page. If a check fails, it stops with an error.

## Validation reference

The app computes and prints every required Section O value from the raw file at startup. Expected headline values are 11,647 lines, 7,995 orders, 1,492 customers, ₹47,291,531.56 revenue, ₹15,240,690.01 profit and 32.23% margin. The displayed dashboard values are calculated from the same cleaned data.
