"""Explicit, resumable analytics history backfill. Never modifies production on import."""

import argparse
import json

from apps.api.backend_api.analytics_history import consolidate_pending


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--execute",action="store_true",help="Write verified daily checkpoints")
    parser.add_argument("--limit-days",type=int,default=30)
    args=parser.parse_args()
    if args.limit_days<1 or args.limit_days>36500:
        parser.error("--limit-days must be between 1 and 36500")
    if not args.execute:
        print("dry_run: pass --execute to consolidate; raw events remain intact")
        return
    remaining=args.limit_days
    total={"days":0,"events":0}
    while remaining:
        batch=consolidate_pending(limit_days=min(remaining,30))
        total["days"]+=batch["days"]
        total["events"]+=batch["events"]
        remaining-=batch["days"]
        if batch["days"]==0 or batch["remaining"]==0:
            break
    print(json.dumps({**total,"remaining_days":batch["remaining"]}))


if __name__=="__main__":
    main()
