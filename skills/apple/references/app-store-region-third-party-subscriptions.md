# App Store region separation and third-party iOS subscription payments

Applicability: reusable procedure for Apple Account tasks where a user wants a separate App Store region account, wants to preserve the main iCloud account, or wants to pay for a third-party iOS subscription through App Store in-app purchase.

Anti-conditions: do not apply when the user wants full iCloud account migration, enterprise device management, unsupported-service bypassing, fraudulent payment, shared accounts, black-card payment, or one-off代充. Re-check current Apple and provider support pages when billing policy details matter.

Falsifier: if a provider explicitly documents that Apple in-app purchases are transferable between service accounts or managed entirely outside Apple subscriptions, narrow the entitlement-binding guidance for that provider.

## Core model

Separate three identities:

1. iCloud Apple Account: iCloud, Photos, Contacts, Backup, Find My, Keychain. Leave the user's main account signed in unless they explicitly want full migration.
2. Media & Purchases / App Store Apple Account: App Store region, downloads, in-app purchases, subscriptions, and Apple balance. This can be separate from iCloud.
3. App/service account inside the app: the account currently signed into the third-party app. This account receives the service entitlement.

Apple handles payment and subscription management; the logged-in app/service account usually receives the entitlement. For iOS in-app purchases, purchase only after confirming the target app account in the app settings.

## Separate App Store account flow

1. Create a fresh Apple Account for the target App Store region.
2. Verify email and phone. Phone number is for security verification and is not the same as account region.
3. Do not sign this account into top-level iCloud if the task is only App Store access.
4. App Store -> profile -> sign out from Media & Purchases/App Store -> sign in with the target-region Apple Account.
5. First App Store use may prompt account review; confirm region, accept terms, fill billing address, and choose `None` if available.
6. If `None` is unavailable, try activation from a free-app download flow before considering gift card or compliant payment.
7. For paid subscriptions, use region-matched Apple balance/gift card or a compliant payment method for that region.

## Third-party iOS subscription flow

1. Confirm App Store / Media & Purchases is signed into the intended store-region Apple Account.
2. Download or update the official app from that region's App Store.
3. If using Apple balance, redeem a gift card that matches the Apple Account region.
4. Open the app and sign into the exact target app/service account.
5. If using federated login, choose the exact identity account intended for the subscription.
6. Confirm the displayed app account/email before tapping Upgrade or Subscribe.
7. Purchase through Apple in-app purchase.
8. Manage cancellation and renewal in Apple subscriptions unless the provider explicitly says otherwise.

## Pitfalls

- Apple ID is the payer, not necessarily the service account that receives entitlement.
- Restore Purchase is normally a restore-to-associated-account mechanism, not a general transfer tool.
- If Apple shows an active subscription but the app account lacks entitlement, suspect the subscription is associated with a different app/service account.
- If purchased under the wrong app account, typical recovery is: cancel renewal, use the current entitlement until expiry if acceptable, repurchase under the correct account, or contact provider support with Apple order details.
- Do not tell the user to sign out of top-level iCloud for an App Store-only task.
