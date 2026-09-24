---
name: amazon-grocery
description: >-
  Add incomplete items from the macOS Reminders list named Grocery to Tyler's
  Amazon cart with ~/git/tools/amazon, leaving those reminders in the app.
  Use when asked to put the Grocery list, grocery reminders, or shopping list
  into the Amazon cart.
metadata:
  {
    "openclaw":
      {
        "emoji": "🛒",
        "os": ["darwin"],
        "requires": { "bins": ["python3", "osascript"] },
      },
  }
---

# Grocery list → Amazon cart

Read the Reminders list named **Grocery** on this Mac, then add each incomplete item with the Amazon cart tool. Leave every reminder in the app.

Cart tool (do not use the `amazon` shell alias; OpenClaw may not load it):

```bash
python3 ~/git/tools/amazon/main.py --yes "product description"
```

That script searches Amazon, picks a match, and adds it to the cart. It does not check out or buy anything. Setup and login: `~/git/tools/amazon/README.md`.

## Hard rules

- Never complete, delete, edit, or move a reminder. Reading the list is the only Reminders action.
- Never open checkout, place an order, or pass any flag that purchases.
- Only the list named `Grocery`. If that list is missing, say so and stop.
- Add an item only when Tyler asked to put the Grocery list (or named items from it) into the cart. A question about what is on the list is read-only.
- Claim an item was added only when that command printed `Added to cart:`.
- If there is no Playwright session, stop and tell Tyler to run `python3 ~/git/tools/amazon/main.py --login` once on this Mac. Do not invent a login.

## Read the list

```bash
osascript ~/git/dotfiles/openclaw/workspace/skills/amazon-grocery/scripts/list_grocery.applescript
```

One incomplete reminder per line: `title<TAB>notes`. Completed reminders are omitted. The script does not change Reminders.

If `osascript` errors or sits with no output, Reminders access is not granted to the process that ran it. Say that and stop. Do not retry in a loop.

## Add to cart

1. Run the list script. If there are no lines, say the Grocery list has no incomplete items and stop.
2. Search text is the title. If notes are a short product detail (brand, size, flavor), append them. Ignore empty notes.
3. Run one cart command at a time and wait for it to finish. Do not run them in parallel; they share one browser session.
4. Use `--yes` when Tyler already asked to cart the list (that request is the confirmation). Use `--dry-run` only when he asked to preview and not add.
5. Reply with each reminder title, whether it was added, and the product line from the tool. Say the reminders are still on the Grocery list.
