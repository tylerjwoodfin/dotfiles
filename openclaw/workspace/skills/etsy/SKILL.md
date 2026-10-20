---
name: etsy
description: >-
  Operate the passive Etsy digital-product experiment. Use when a message
  mentions Etsy, the shop, a listing, the septic workbook, or the weekly
  business report. Do not publish, pay, or refund without a recorded approval.
user-invocable: false
metadata:
  {
    "openclaw":
      {
        "emoji": "📒",
        "requires": { "bins": ["python3"] },
      },
  }
---

# Etsy digital products

The shop experiment lives in `~/git/etsy`. Cherry does not open
Etsy in a browser and does not call the Etsy API until Tyler has approved an
app and the credentials are in Cabinet.

## Hard rules

- Do not open a shop, publish a listing, renew a listing, buy ads, or pay any fee unless that exact charge is approved.
- Do not send a customer a refund, a legal answer, or a promise of compensation.
- Do not report Etsy revenue, orders, or visits as `$0` or `0` when the shop is not connected. Say `unavailable`.
- Do not claim a product is handmade or human-designed. The draft listing discloses AI assistance.
- A weekly report is sent only by `etsy_cli.py tick` after `experiment_started` is true. If the tick did not send, stay quiet.

## Commands

```bash
python3 ~/git/etsy/scripts/etsy_cli.py report
python3 ~/git/etsy/scripts/etsy_cli.py tick --dry-run
python3 ~/git/etsy/scripts/etsy_cli.py fees 12
python3 ~/git/etsy/scripts/etsy_cli.py build
```

`etsy-business-tick` runs the tick at 8:15am Pacific. Before the experiment
starts, the tick does not message Tyler.

The prototype workbook is `workspace/products/septic-service-record/`. It is a
draft until Tyler approves it.
