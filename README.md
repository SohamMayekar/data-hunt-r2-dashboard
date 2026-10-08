AI used: Yes, for dashboard code, visual design, and README drafting, and we can explain every part.

# THE DATA HUNT, Round 2

Team name: SYNTORY  
Team ID: [add assigned Team ID]  
Members: Soham Mayekar, Devesh Kushe, Rudraksha Patil

## What the dashboard shows

The dashboard compares booked and delivered revenue, profit, product margins, discounts, order outcomes and customer value. It is one scrolling page with filters for date, region, category, segment and revenue basis. Revenue basis starts at Booked.

## Cleaning

The app reads `data/R_Questions.csv` at startup and refreshes `data/cleaned_orders.csv`.

- Removed 20 exact duplicate rows. Their recorded revenue was ₹76,218 and profit was ₹25,620.
- Removed 12 rows with discounts above 100%. Their recorded revenue was negative ₹8,592. The true discount is unknown.
- Set 10 negative shipping-day values to missing.
- Left other missing values blank. No values were imputed.
- Added category and subcategory labels, month, age bands and order-status flags.

The cleaned file has 11,647 item lines, 7,995 orders and 1,492 customers.

## Q1 to Q5

These are unfiltered values on the default Booked basis. Dashboard figures recalculate when filters change.

### Q1. Money

Booked revenue is ₹47,291,531.56. Booked profit is ₹15,240,690.01. Margin is 32.23%. Electronics has the highest revenue at ₹14,080,094 and the highest profit at ₹4,735,440. Sports has 19.9% of revenue and 17.4% of profit in the dashboard. Fashion has the highest category margin at 35.6%. Sports has the lowest at 28.3%.

### Q2. Trend

Revenue is broadly flat across 2025. July has the highest monthly revenue at ₹4,130,653. March has the highest monthly profit at ₹1,354,713. Revenue rose 3.3% from Q1 to Q4. Profit rose 1.0%. Margin moved from 32.5% to 31.8%. The data has no campaign, traffic or stock fields, so it cannot explain monthly changes.

### Q3. Problems

The return rate is 7.78% (622 of 7,995 orders). The cancellation rate is 8.23% (658 of 7,995). The tested categories, regions, payment methods, shipping bands, age bands and segments do not show a statistically clear hotspot. Shipping time, discount and rating relationships are small. These results do not show that faster shipping or deeper discounts would change returns or ratings.

### Q4. Customers

The top 10% of customers account for 21.4% of profit. The top 20% account for 37.4%. Purchase frequency is more closely associated with customer profit than the demographic fields. Mumbai has the most city profit. Lucknow has the highest profit per customer.

### Q5. Actions

1. Review the 28 products below 26% margin. They account for ₹13.81M revenue and ₹3.02M profit. A 30% margin target would add about ₹1.12M profit if revenue stayed the same. The data cannot show whether a price rise would reduce orders.
2. Test a 10% discount cap in one category. The 15% and 20% tiers account for ₹1.69M in discounts across 2,334 lines. Under the recorded cost formula, the cap retains about ₹0.65M revenue and ₹0.21M profit. The data cannot show what buyers would have done without a discount.
3. Review old Pending orders. There are 291 Pending orders older than 90 days, with ₹1.67M booked revenue at the 31 December 2025 reference date. No customer group stands out as a hotspot.

## Bonus findings

- Only ₹37.38M of ₹47.29M booked revenue was marked Delivered, or 79.0%. Profit is also recorded on non-delivered orders.
- The cost formula uses discounted revenue. This makes recorded margins look similar across discount tiers. The dashboard labels its list-price cost line as a sensitivity based on an assumption, not an observed cost.
- Product margins range from 18.3% to 47.6%. Category averages hide this spread.
- Pending orders occur throughout the year. 291 were more than 90 days old at the fixed 31 December 2025 reference date.
- The same subcategory label, Accessories, appears in Electronics and Fashion. Product comparisons use product IDs.
- Customer age has a floor at 18. There are 86 customers listed as 18, compared with 19 listed as 19. Age groups are descriptive only.
- Ratings and shipping days appear on some non-delivered lines. Profit and revenue are also recorded for cancelled orders.
- The raw data has 20 exact duplicates, 12 lines with 125% discounts and negative revenue, and 10 negative shipping-day values. Cleaning removes or marks these as described above.

## What the data cannot tell us

There is no campaign, traffic or inventory data. The file cannot explain why order counts changed. The discount comparison cannot show what buyers would have done without a discount. The cost-at-list-price line is a sensitivity based on an assumption. Pending age uses 31 December 2025 as its reference date. These results do not establish causes.

## Run the dashboard

Use Python 3.10 or newer. From the repository folder, run:

```sh
pip install -r requirements.txt
streamlit run app.py
```

The raw file is `data/R_Questions.csv`. The app runs `clean.py` at startup and writes `data/cleaned_orders.csv`. It prints every Section O validation value beside its expected value. The dashboard stops if any required check fails.

## Screenshots

The `screenshots/` folder should contain 3 or 4 dashboard screenshots at 1440 px wide. Capture the top of the page, the Money section, the Problems section, and the Customers and Actions sections with the data notes visible.
