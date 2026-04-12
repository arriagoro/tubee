-- Usage credits table for Tubee
-- Run this in Supabase SQL editor

CREATE TABLE IF NOT EXISTS usage_credits (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  -- AI edits (unlimited on $29 plan)
  edits_used integer DEFAULT 0,
  -- AI generation credits (Kling/Veo - limited)
  generation_credits_remaining integer DEFAULT 10,
  generation_credits_used integer DEFAULT 0,
  -- Reset monthly
  reset_at timestamptz DEFAULT (now() + interval '30 days'),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id)
);

-- Auto-create credits when subscription is created
CREATE OR REPLACE FUNCTION create_usage_credits_on_subscribe()
RETURNS trigger AS $$
BEGIN
  INSERT INTO usage_credits (user_id, generation_credits_remaining, plan_credits_total)
  VALUES (NEW.user_id, 10, 10)
  ON CONFLICT (user_id) DO UPDATE
    SET generation_credits_remaining = 10,
        reset_at = now() + interval '30 days',
        updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER on_subscription_created
  AFTER INSERT ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION create_usage_credits_on_subscribe();

-- RLS
ALTER TABLE usage_credits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own credits" ON usage_credits FOR SELECT USING (auth.uid() = user_id);
