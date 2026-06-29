-- =====================================================================
-- Process Blueprint — Phase 1.5 schema (internal tool)
-- Project: zrggqvgtthlhwbayckuc (eu-west-1, Postgres 17)
--
-- Internal-only: NO client auth. The app connects with the service-role key
-- (server-side), which bypasses RLS. RLS is still ENABLED with no public
-- policies so the anon/public PostgREST API exposes NOTHING — important,
-- because these tables hold client data.
-- =====================================================================

-- pgvector for the knowledge/RAG layer (Phase 3). Supabase convention: the
-- extension lives in the `extensions` schema; reference the type qualified.
create extension if not exists vector with schema extensions;

-- ---------------------------------------------------------------------
-- clients
-- ---------------------------------------------------------------------
create table public.clients (
    id          uuid primary key default gen_random_uuid(),
    name        text not null,
    industry    text,
    created_at  timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- engagements — one consulting project for a client
-- ---------------------------------------------------------------------
create table public.engagements (
    id            uuid primary key default gen_random_uuid(),
    client_id     uuid not null references public.clients(id) on delete cascade,
    name          text not null,
    process_type  text,
    status        text not null default 'active'
                  check (status in ('active', 'delivered', 'archived')),
    created_at    timestamptz not null default now()
);
create index idx_engagements_client on public.engagements(client_id);

-- ---------------------------------------------------------------------
-- event_log_runs — one mining run on an uploaded event log
-- ---------------------------------------------------------------------
create table public.event_log_runs (
    id             uuid primary key default gen_random_uuid(),
    engagement_id  uuid not null references public.engagements(id) on delete cascade,
    source_file    text,
    algorithm      text,
    n_events       integer,
    n_cases        integer,
    status         text not null default 'completed'
                   check (status in ('running', 'completed', 'failed')),
    created_at     timestamptz not null default now()
);
create index idx_runs_engagement on public.event_log_runs(engagement_id);

-- ---------------------------------------------------------------------
-- process_facts — the ProcessFacts contract (full jsonb + queryable columns)
-- ---------------------------------------------------------------------
create table public.process_facts (
    id                       uuid primary key default gen_random_uuid(),
    run_id                   uuid not null references public.event_log_runs(id) on delete cascade,
    schema_version           text not null,
    process_type             text,
    n_cases                  integer,
    n_variants               integer,
    avg_cycle_time_seconds   double precision,
    model_fitness            double precision,
    model_precision          double precision,
    facts                    jsonb not null,          -- full ProcessFacts.to_dict()
    created_at               timestamptz not null default now()
);
create index idx_facts_run on public.process_facts(run_id);
create index idx_facts_jsonb on public.process_facts using gin (facts);

-- ---------------------------------------------------------------------
-- knowledge_chunks — RAG corpus (engagement_id null = firm-wide)
-- ---------------------------------------------------------------------
create table public.knowledge_chunks (
    id             uuid primary key default gen_random_uuid(),
    engagement_id  uuid references public.engagements(id) on delete cascade,
    source         text not null
                   check (source in ('benchmark', 'methodology', 'client_doc')),
    title          text,
    content        text not null,
    -- 1536 = OpenAI text-embedding-3-small. Adjust to your embedding model
    -- (e.g. 1024 for Voyage). Change before loading data.
    embedding      extensions.vector(1536),
    metadata       jsonb not null default '{}'::jsonb,
    created_at     timestamptz not null default now()
);
create index idx_chunks_engagement on public.knowledge_chunks(engagement_id);
create index idx_chunks_embedding on public.knowledge_chunks
    using hnsw (embedding extensions.vector_cosine_ops);

-- ---------------------------------------------------------------------
-- recommendations — Requirements Lifecycle Mgmt: trace / prioritise / approve
-- ---------------------------------------------------------------------
create table public.recommendations (
    id              uuid primary key default gen_random_uuid(),
    engagement_id   uuid not null references public.engagements(id) on delete cascade,
    run_id          uuid references public.event_log_runs(id) on delete set null,
    title           text not null,
    detail          text,
    babok_technique text,
    priority        text not null default 'medium'
                    check (priority in ('low', 'medium', 'high', 'critical')),
    status          text not null default 'proposed'
                    check (status in ('proposed', 'approved', 'in_progress', 'done', 'rejected')),
    owner           text,
    est_impact      text,
    created_at      timestamptz not null default now()
);
create index idx_recs_engagement on public.recommendations(engagement_id);

-- ---------------------------------------------------------------------
-- Lock down the public API: enable RLS, add NO policies.
-- Service-role (server-side app) bypasses RLS; anon/public sees nothing.
-- ---------------------------------------------------------------------
alter table public.clients          enable row level security;
alter table public.engagements      enable row level security;
alter table public.event_log_runs   enable row level security;
alter table public.process_facts    enable row level security;
alter table public.knowledge_chunks enable row level security;
alter table public.recommendations  enable row level security;
