# Tubee Release Checklist

Do not call a fix done until these are verified on production.

## Auth and Access
- [ ] New user can sign up on production
- [ ] Existing user can log in on production
- [ ] Paid user lands in editor without bouncing to pricing
- [ ] Logged-out user hitting `/editor` gets sent to `/auth/login`
- [ ] Password reset email flow works

## Payments
- [ ] Stripe checkout opens from pricing page
- [ ] Successful payment updates Supabase subscription row
- [ ] Webhook endpoint is reachable and returns non-404
- [ ] Paid user is recognized by `/subscription-status/{user_id}`
- [ ] Manage subscription portal opens correctly

## Routing and Infra
- [ ] Auth/subscription checks do not depend on ngrok FFmpeg health
- [ ] Video processing can fall back to ngrok if Railway ffmpeg is unavailable
- [ ] Railway `/health` responds
- [ ] If ngrok is offline, login and paid access still work

## Editing
- [ ] Upload works
- [ ] Edit job starts
- [ ] Status polling works
- [ ] Download works

## Rules learned from April 2026 auth incident
1. Never mix raw token storage with Supabase session flow.
2. Never route auth/payment checks through the video-processing base selector.
3. Never mark a payment/access bug fixed without verifying end-to-end on production.
4. When a bug is fixed, document it here and in memory the same day.
