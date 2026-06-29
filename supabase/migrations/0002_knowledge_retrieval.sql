-- =====================================================================
-- Process Blueprint — Phase 3: knowledge retrieval + stakeholder input
-- Project: zrggqvgtthlhwbayckuc
-- =====================================================================

-- Vector similarity search over knowledge_chunks (cosine).
-- Returns the closest chunks, optionally filtered by source and/or engagement.
-- The app calls this via client.rpc('match_knowledge_chunks', {...}).
create or replace function public.match_knowledge_chunks(
    query_embedding   extensions.vector(1536),
    match_count       integer default 5,
    filter_source     text default null,
    filter_engagement uuid default null
)
returns table (
    id         uuid,
    source     text,
    title      text,
    content    text,
    similarity double precision
)
language sql
stable
as $$
    select
        kc.id,
        kc.source,
        kc.title,
        kc.content,
        1 - (kc.embedding <=> query_embedding) as similarity
    from public.knowledge_chunks kc
    where kc.embedding is not null
      and (filter_source is null or kc.source = filter_source)
      and (filter_engagement is null
           or kc.engagement_id is null
           or kc.engagement_id = filter_engagement)
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;

-- Stakeholder input — the qualitative WHY behind the data (closes the BABOK
-- Elicitation gap). One row per process owner / stakeholder per engagement.
create table public.stakeholder_inputs (
    id             uuid primary key default gen_random_uuid(),
    engagement_id  uuid not null references public.engagements(id) on delete cascade,
    role           text,
    pain_points    text[] not null default '{}',
    goals          text[] not null default '{}',
    constraints    text[] not null default '{}',
    notes          text,
    created_at     timestamptz not null default now()
);
create index idx_stakeholder_engagement on public.stakeholder_inputs(engagement_id);

-- Internal-only: lock the public API (service-role bypasses).
alter table public.stakeholder_inputs enable row level security;
