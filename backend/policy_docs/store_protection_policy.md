# Store Protection Policy

## Purpose
Protect scarce store inventory from being consumed by digital orders when doing so creates elevated risk of stockout for in-store demand.

## Policy Rules
- If post-allocation available inventory at a store is at or below protection quantity, that option should be treated as high risk.
- If a store item has high local velocity and replenishment is more than 3 days away, preference should shift toward DC or alternate nodes when customer promise can still be met.
- If the option consumes one of the last units at a store, the option should be deprioritized unless no feasible alternative exists.

## Guidance
- Prefer store fulfillment when it improves service and inventory is healthy.
- Avoid store fulfillment when inventory is scarce, velocity is high, and replenishment is delayed.