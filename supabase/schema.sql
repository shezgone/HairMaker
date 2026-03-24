-- HairMaker Database Schema
-- Run this in the Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- SALONS
-- ============================================================
CREATE TABLE IF NOT EXISTS salons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'starter',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DESIGNERS (linked to Supabase Auth users)
-- ============================================================
CREATE TABLE IF NOT EXISTS designers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  salon_id UUID REFERENCES salons(id) ON DELETE CASCADE,
  auth_user_id UUID UNIQUE,  -- Links to auth.users.id
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT DEFAULT 'designer',  -- designer | admin
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- HAIRSTYLE CATALOG
-- ============================================================
CREATE TABLE IF NOT EXISTS hairstyles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  style_tags TEXT[] DEFAULT '{}',
  face_shapes TEXT[] DEFAULT '{}',
  face_shape_scores JSONB DEFAULT '{}',
  gender_presentation TEXT[] DEFAULT '{"all"}',
  hair_length TEXT,
  maintenance_level INT DEFAULT 2,
  reference_image_url TEXT,
  reference_images TEXT[] DEFAULT '{}',
  simulation_prompt TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hairstyles_face_shapes ON hairstyles USING GIN (face_shapes);
CREATE INDEX IF NOT EXISTS idx_hairstyles_style_tags ON hairstyles USING GIN (style_tags);
CREATE INDEX IF NOT EXISTS idx_hairstyles_active ON hairstyles (is_active);

-- ============================================================
-- CUSTOMER SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  salon_id UUID REFERENCES salons(id) ON DELETE CASCADE,
  designer_id UUID REFERENCES designers(id),
  photo_url TEXT,
  processed_photo_url TEXT,
  face_analysis JSONB,
  selected_style_id UUID REFERENCES hairstyles(id),
  consultation_notes TEXT,
  status TEXT DEFAULT 'active',  -- active | completed | archived
  customer_consent BOOLEAN DEFAULT FALSE,
  expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_salon ON sessions (salon_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status);

-- ============================================================
-- SIMULATION JOBS
-- ============================================================
CREATE TABLE IF NOT EXISTS simulation_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  style_id UUID REFERENCES hairstyles(id),
  job_id TEXT,               -- Replicate prediction ID
  status TEXT DEFAULT 'pending',  -- pending | processing | done | error
  result_url TEXT,
  error_message TEXT,
  model_used TEXT DEFAULT 'flux-kontext-pro',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sim_jobs_session ON simulation_jobs (session_id);
CREATE INDEX IF NOT EXISTS idx_sim_jobs_status ON simulation_jobs (status);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Sessions: only accessible by the salon that created them
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- For now, service role bypasses RLS (used by FastAPI backend)
-- Add RLS policies when adding direct client access

-- ============================================================
-- STORAGE BUCKETS (create via Supabase Dashboard or CLI)
-- ============================================================
-- Bucket: session-photos  (private, file size limit 10MB)
-- Bucket: simulation-results  (private, file size limit 10MB)
-- Bucket: style-catalog  (public, read-only for anon)

-- ============================================================
-- DEMO DATA: Insert a demo salon for local development
-- ============================================================
INSERT INTO salons (id, name, slug, plan)
VALUES ('00000000-0000-0000-0000-000000000001', '데모 헤어샵', 'demo', 'starter')
ON CONFLICT (slug) DO NOTHING;

INSERT INTO designers (id, salon_id, email, name, role)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',
  'designer@demo.com',
  '데모 디자이너',
  'admin'
) ON CONFLICT (email) DO NOTHING;
