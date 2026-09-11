# CouponFinder 🎟️

CouponFinder is a high-converting coupons and discount codes landing page inspired by modern voucher platforms. It features an integrated, custom-themed CPA Content Locker powered by the OGAds API.

## Features

- **Rich Brand Catalog**: 30+ international brand coupons (SHEIN, Nike, McDonald's, Apple, Tesla, Adidas, etc.).
- **Multi-Stage Claim Flow**:
  - **Step 1**: Brand preview, incentive details, and rating statistics.
  - **Step 2**: Locked code box with custom themed API Locker (choosing 1 of 2 offers).
  - **Step 3**: Unlocked code reveal with one-click clipboard copying.
- **Strict Verification & Anti-Cheat**: Requires genuine completion of 1 offer from the CPA network before revealing the code.
- **Multi-Landing Page Postback Routing**: Pre-configured with `aff_sub4` tags to allow multiple landing pages on a single OGAds account.
- **10-Hour Bypass**: Saves verified sessions in `localStorage` for 10 hours of uninterrupted access.
- **Serverless Architecture**: Ready for 1-click deployment to [Vercel](https://vercel.com).

## Deployment

1. Push this repository to GitHub.
2. Import the project into **Vercel**.
3. (Optional) In your Vercel Project Settings, add the Environment Variable:
   - `OGADS_API_KEY`: `47558|DluqLUTirEcifKUEHLp0wrBpqTebJR7XbTqwtkL666b7e813`
4. Set your OGAds Postback URL:
   ```text
   https://your-domain.vercel.app/api/postback?ip={ip}&offerid={offer_id}&payout={payout}&site={aff_sub4}
   ```
