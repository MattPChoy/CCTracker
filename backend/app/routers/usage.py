"""Idempotent usage ingestion from ccusage."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import UsageDailyModel, User, _now
from ..deps import get_session
from ..normalize import normalize_cost, normalize_model, normalize_tokens
from ..schemas import IngestIn, IngestOut

router = APIRouter(prefix="/v1", tags=["usage"])


@router.post("/usage", response_model=IngestOut)
def ingest(
    body: IngestIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> IngestOut:
    upserted = 0
    for day in body.days:
        # Collapse multiple raw model rows that normalize to the same family/day.
        merged: dict[str, dict] = {}
        for raw_row in day.models:
            family, label = normalize_model(str(raw_row.get("model", "")))
            toks = normalize_tokens(raw_row)
            cost = normalize_cost(raw_row)
            agg = merged.setdefault(
                family,
                {"label": label, "cost_usd": 0.0, **{k: 0 for k in toks}},
            )
            agg["label"] = label
            agg["cost_usd"] += cost
            for k, v in toks.items():
                agg[k] += v

        for family, agg in merged.items():
            stmt = pg_insert(UsageDailyModel).values(
                user_id=user.id,
                date=day.date,
                model=family,
                label=agg["label"],
                input_tokens=agg["input_tokens"],
                output_tokens=agg["output_tokens"],
                cache_creation_tokens=agg["cache_creation_tokens"],
                cache_read_tokens=agg["cache_read_tokens"],
                total_tokens=agg["total_tokens"],
                cost_usd=agg["cost_usd"],
                source=body.source,
                updated_at=_now(),
            )
            # Idempotent: (user_id, date, model) overwrites rather than doubles.
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id", "date", "model"],
                set_={
                    "label": stmt.excluded.label,
                    "input_tokens": stmt.excluded.input_tokens,
                    "output_tokens": stmt.excluded.output_tokens,
                    "cache_creation_tokens": stmt.excluded.cache_creation_tokens,
                    "cache_read_tokens": stmt.excluded.cache_read_tokens,
                    "total_tokens": stmt.excluded.total_tokens,
                    "cost_usd": stmt.excluded.cost_usd,
                    "source": stmt.excluded.source,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            session.execute(stmt)
            upserted += 1
    session.commit()
    return IngestOut(upserted_rows=upserted, days=len(body.days))
