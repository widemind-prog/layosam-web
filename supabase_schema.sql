-- ══════════════════════════════════════════════════════════
-- LAYOSAM  ·  Supabase Schema
-- Run this entire script in your Supabase SQL Editor once.
-- ══════════════════════════════════════════════════════════

-- 1. PROJECTS TABLE
create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  title       text not null,
  location    text not null,
  category    text not null default 'Solar Installation',
  description text,
  image_url   text,
  featured    boolean not null default false,
  created_at  timestamptz not null default now()
);

-- 2. INDEX for fast ordering
create index if not exists projects_created_at_idx
  on public.projects (created_at desc);

-- 3. ROW-LEVEL SECURITY
--    Public: SELECT only (anyone can read projects for the website)
--    All mutations come from server-side using the service-role key,
--    which bypasses RLS automatically — no INSERT/UPDATE/DELETE policy needed.
alter table public.projects enable row level security;

drop policy if exists "Public read projects" on public.projects;
create policy "Public read projects"
  on public.projects
  for select
  using (true);

-- 4. STORAGE BUCKET
--    Run these only if you have not already created the bucket via the UI.
insert into storage.buckets (id, name, public)
values ('layosam-projects', 'layosam-projects', true)
on conflict (id) do nothing;

-- Public read policy on storage objects
drop policy if exists "Public read project images" on storage.objects;
create policy "Public read project images"
  on storage.objects
  for select
  using (bucket_id = 'layosam-projects');

-- ══════════════════════════════════════════════════════════
-- DONE.  Your Flask app uses the service-role key server-side
-- so all admin operations (INSERT / UPDATE / DELETE) bypass RLS.
-- ══════════════════════════════════════════════════════════
