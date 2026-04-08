-- Tubee Subscriptions Table
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New Query)

create table if not exists public.subscriptions (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete cascade,
  stripe_customer_id text,
  stripe_subscription_id text,
  plan text check (plan in ('starter', 'pro')),
  status text default 'active',
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Create index for fast lookups
create index if not exists idx_subscriptions_user_id on public.subscriptions(user_id);
create index if not exists idx_subscriptions_stripe_customer_id on public.subscriptions(stripe_customer_id);

-- Enable Row Level Security
alter table public.subscriptions enable row level security;

-- Users can view their own subscription
create policy "Users can view own subscription"
  on public.subscriptions for select
  using (auth.uid() = user_id);

-- Service role can do everything (used by webhook handler)
-- Note: service_role key bypasses RLS by default, so no explicit policy needed for it.

-- Updated_at trigger
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger on_subscription_updated
  before update on public.subscriptions
  for each row execute function public.handle_updated_at();
