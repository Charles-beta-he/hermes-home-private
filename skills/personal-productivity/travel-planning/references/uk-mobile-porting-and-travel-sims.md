# UK Mobile Number Porting and Travel SIM Selection

Scope: travel/connectivity planning for UK trips or UK-based mobile setup, especially when comparing giffgaff-style PAYG SIMs with CTExcel/China Telecom UK services.

## Key distinction

A physical SIM from one operator cannot directly take another operator's tariff. A giffgaff SIM cannot directly bind a CTExcel plan. To use CTExcel tariffs while keeping a giffgaff number, the user must port the mobile number to CTExcel after obtaining and activating a CTExcel SIM/eSIM.

## CTExcel evidence captured from site inspection

CTExcel's public site text indicates:

- CTExcel supports keeping an existing UK mobile number and transferring it to CTExcel.
- The transfer flow is:
  1. Order a CTExcel SIM or eSIM.
  2. Activate the CTExcel SIM/eSIM.
  3. Get a PAC/STAC code from the current provider.
  4. Submit a porting application to CTExcel.
  5. Transfer normally takes about 1–3 working days and may involve a short service interruption.
- CTExcel copy mentions PAC/STAC format as 3 letters + 6 digits, e.g. `ABC123456`.
- CTExcel site text says port-in users may receive a transfer promotion after successful transfer: first spend over £9 may receive £5 credit + 2GB; second/third spend over £9 may receive 2GB each. Treat promotions as time-bound and verify current terms before purchase.
- CTExcel UK service highlights include UK plans, China/UK calling, China number or virtual number services, roaming/China-related benefits, and Chinese-language support.

## Practical recommendation pattern

- If the user only needs fast/cheap UK data: activate the existing giffgaff SIM with a giffgaff plan.
- If the user needs China/UK features, Chinese-language support, China number linkage, or longer-term UK number management: order CTExcel SIM/eSIM and port the giffgaff number into CTExcel.
- Do not tell the user that a CTExcel tariff can be placed on a giffgaff physical SIM.
- Warn the user not to share activation codes, PAC/STAC codes, full ICCID, or phone-number verification codes in chat.

## Physical eSIM adapters such as ESTKme

When the user shows an ESTKme / 5ber / eSIM.me-style product page, classify it as an **eSIM carrier/adapter**, not an operator plan:

- It is a physical SIM-like card that can store/manage eSIM profiles for phones that lack native eSIM support.
- It does not itself provide a CTExcel/giffgaff number, tariff, credit, roaming entitlement, or network service.
- A CTExcel number that has been ported from giffgaff can use CTExcel plans on a CTExcel SIM/eSIM; that does not automatically prove the CTExcel eSIM profile can be written to a third-party adapter.
- Before recommending an adapter path, verify with CTExcel/adapter support whether the CTExcel eSIM QR/profile supports third-party eSIM adapter provisioning and whether there are EID/device/region restrictions.
- CTExcel site copy observed: CTExcel eSIM/physical SIM activation may need to occur in the UK/EU; mainland China-market phones may lack native eSIM support. Treat those as purchase-risk checks, not guaranteed blockers for all devices.

Default advice: if reliability matters and the phone has no native eSIM, prefer CTExcel physical SIM + port-in over a third-party eSIM adapter unless compatibility is confirmed.

## Minimal user-facing answer shape

"Yes, after porting the number to CTExcel you can use CTExcel plans/promotions, but you first need a CTExcel SIM/eSIM. The giffgaff card itself cannot directly carry a CTExcel plan. Order/activate CTExcel, get PAC from giffgaff, submit CTExcel port-in, wait 1–3 working days, then subscribe to CTExcel plans."
