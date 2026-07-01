# Collectible wine / spirits price check

Use when the user asks for a current value, resale range, or investment/aging claim for a specific vintage bottle (wine, Madeira, Port, whisky, baijiu, etc.).

## Procedure

1. Resolve the exact bottle before pricing.
   - Producer / brand
   - Vintage / bottling year
   - Style or grape / cuvee / cask type
   - Bottle size
   - Region and any special bottling/library release
   - If the user only gives a partial name, price the most likely matches and label the ambiguity.

2. Triangulate live retail prices from multiple merchant types.
   - Specialist merchants for the category.
   - Aggregators such as Wine-Searcher when accessible.
   - Regional shops where the user likely buys/sells.
   - Prefer pages with structured product data (`application/ld+json`, offer price, currency, availability) over search snippets.

3. Separate price classes.
   - Retail current asking price.
   - Out-of-stock historical/anchor price.
   - Domestic landed/stocked price after tax, freight, and margin.
   - Private resale / dealer buy price, usually discounted from retail.
   - Auction hammer price if available, net of fees.

4. Convert currency with a live rate and state the rate/date.
   - Show a compact RMB range, not just foreign prices.
   - If live FX lookup is blocked, state the assumed rate.

5. Evaluate investment/aging claims cautiously.
   - Fortified wines such as Madeira can be unusually stable and long-lived, but longevity does not imply guaranteed appreciation.
   - List the actual value drivers: producer reputation, rarity, grape/style, condition, fill level, label/capsule, provenance, invoice/import proof, market liquidity.
   - Flag high-pressure claims like “can store 100 years and must rise” as sales language unless supported by auction/liquidity evidence.

## Output shape

- Lead with the likely market value range in the user's currency.
- Then give 3–6 evidence points with merchant, price, currency, availability if known.
- Then give buy/sell guidance:
  - reasonable buy price,
  - likely private resale/dealer range,
  - conditions that justify a premium,
  - conditions that require a discount.
- Keep it decision-oriented; do not over-explain wine background unless asked.

## Pitfalls

- Do not treat one high retail listing as market value.
- Do not mix similar but different bottles (e.g. Verdelho vs Malvasia, 750ml vs 500ml, Madeira wine vs Madeira-finished whisky).
- Do not equate “can age for decades/centuries” with “will appreciate”.
- Do not omit availability: in-stock offers matter more than old/out-of-stock listings.
