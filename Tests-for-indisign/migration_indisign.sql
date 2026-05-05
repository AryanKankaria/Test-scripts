-- Migration 000 (merged): Admin portal tables
-- Tables: admin_portal_users, support_tickets, ticket_comments, ticket_notifications, admin_action_audit_logs
--
-- Idempotent. Runs after schema.sql. Uses CREATE TABLE IF NOT EXISTS for fresh DBs
-- plus ALTER TABLE patches to reconcile drift on DBs already initialized from schema.sql.

-- =====================================================================
-- admin_portal_users
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.admin_portal_users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    name character varying(255) NOT NULL,
    dob date,
    role character varying(20) NOT NULL,
    password_hash text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    email_verified boolean DEFAULT false NOT NULL,
    phone_verified boolean DEFAULT false NOT NULL,
    last_login_at timestamp with time zone,
    address jsonb,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT admin_portal_users_password_hash_check CHECK (
        ((password_hash ~* '^[A-Fa-f0-9]{64}$'::text) OR
         ((password_hash ~~ '$2%'::text) AND (LENGTH(password_hash) = 60)))
    ),
    CONSTRAINT admin_portal_users_role_check CHECK (role = ANY (ARRAY['superadmin'::varchar, 'admin'::varchar, 'editor'::varchar]))
);

-- Reconcile role check (schema.sql ships an older constraint missing 'superadmin')
ALTER TABLE public.admin_portal_users DROP CONSTRAINT IF EXISTS admin_portal_users_role_check;
ALTER TABLE public.admin_portal_users
    ADD CONSTRAINT admin_portal_users_role_check
    CHECK (role = ANY (ARRAY['superadmin'::varchar, 'admin'::varchar, 'editor'::varchar]));

CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_portal_users_email ON public.admin_portal_users (email);
CREATE INDEX IF NOT EXISTS idx_admin_portal_users_role ON public.admin_portal_users (role);
CREATE INDEX IF NOT EXISTS idx_admin_portal_users_active ON public.admin_portal_users (is_active);
CREATE INDEX IF NOT EXISTS idx_admin_portal_users_last_login ON public.admin_portal_users (last_login_at DESC);

CREATE OR REPLACE FUNCTION public.set_admin_portal_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_admin_portal_users_updated_at ON public.admin_portal_users;
CREATE TRIGGER trg_admin_portal_users_updated_at
BEFORE UPDATE ON public.admin_portal_users
FOR EACH ROW
EXECUTE FUNCTION public.set_admin_portal_users_updated_at();

CREATE OR REPLACE FUNCTION public.enforce_admin_portal_email_isolated()
RETURNS TRIGGER AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM public.users u WHERE LOWER(u.email) = LOWER(NEW.email)
  ) THEN
    RAISE EXCEPTION 'Email % already exists in users table; admin portal user must be separate.', NEW.email;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_admin_portal_email_isolated ON public.admin_portal_users;
CREATE TRIGGER trg_admin_portal_email_isolated
BEFORE INSERT OR UPDATE OF email ON public.admin_portal_users
FOR EACH ROW
EXECUTE FUNCTION public.enforce_admin_portal_email_isolated();


-- =====================================================================
-- support_tickets
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.support_tickets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    ticket_type character varying(50) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'open'::character varying,
    priority varchar(20) NOT NULL DEFAULT 'medium',
    resolved_by_id uuid REFERENCES public.admin_portal_users(id) ON DELETE SET NULL,
    assigned_to uuid REFERENCES public.admin_portal_users(id) ON DELETE SET NULL,
    assigned_by uuid REFERENCES public.admin_portal_users(id) ON DELETE SET NULL,
    attachments jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    CONSTRAINT support_tickets_status_check CHECK (status = ANY (ARRAY['open'::varchar, 'in_progress'::varchar, 'resolved'::varchar, 'closed'::varchar])),
    CONSTRAINT support_tickets_priority_check CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    CONSTRAINT support_tickets_ticket_type_check CHECK (ticket_type IN ('document_workflow', 'wallet_balance', 'recipient_delivery', 'esign'))
);

-- Reconcile columns missing from schema.sql's older definition
ALTER TABLE public.support_tickets
    ADD COLUMN IF NOT EXISTS priority varchar(20) NOT NULL DEFAULT 'medium',
    ADD COLUMN IF NOT EXISTS assigned_to uuid REFERENCES public.admin_portal_users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS assigned_by uuid REFERENCES public.admin_portal_users(id) ON DELETE SET NULL;

-- Reconcile constraints (Postgres lacks ADD CONSTRAINT IF NOT EXISTS for CHECK)
ALTER TABLE public.support_tickets DROP CONSTRAINT IF EXISTS support_tickets_priority_check;
ALTER TABLE public.support_tickets
    ADD CONSTRAINT support_tickets_priority_check
    CHECK (priority IN ('critical', 'high', 'medium', 'low'));

ALTER TABLE public.support_tickets DROP CONSTRAINT IF EXISTS support_tickets_ticket_type_check;
ALTER TABLE public.support_tickets
    ADD CONSTRAINT support_tickets_ticket_type_check
    CHECK (ticket_type IN ('document_workflow', 'wallet_balance', 'recipient_delivery', 'esign'));

CREATE INDEX IF NOT EXISTS idx_support_tickets_user_id ON public.support_tickets (user_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON public.support_tickets (status);
CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at ON public.support_tickets (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_support_tickets_attachments ON public.support_tickets USING GIN (attachments);
CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_to ON public.support_tickets (assigned_to);
CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_by ON public.support_tickets (assigned_by);


-- =====================================================================
-- ticket_comments
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.ticket_comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid NOT NULL REFERENCES public.support_tickets(id) ON DELETE CASCADE,
  author_id uuid REFERENCES public.admin_portal_users(id) ON DELETE CASCADE,
  body text NOT NULL,
  is_closing_comment boolean NOT NULL DEFAULT false,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket_id ON public.ticket_comments (ticket_id);

-- Reconcile: older DBs created author_id as NOT NULL (system-generated comments need it nullable)
ALTER TABLE public.ticket_comments ALTER COLUMN author_id DROP NOT NULL;


-- =====================================================================
-- ticket_notifications
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.ticket_notifications (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_user_id uuid NOT NULL REFERENCES public.admin_portal_users(id) ON DELETE CASCADE,
  ticket_id uuid NOT NULL REFERENCES public.support_tickets(id) ON DELETE CASCADE,
  comment_id uuid NOT NULL REFERENCES public.ticket_comments(id) ON DELETE CASCADE,
  type varchar(50) NOT NULL DEFAULT 'new_comment',
  message text NOT NULL,
  read boolean NOT NULL DEFAULT false,
  read_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_notifications_admin_user_id ON public.ticket_notifications (admin_user_id);
CREATE INDEX IF NOT EXISTS idx_ticket_notifications_ticket_id ON public.ticket_notifications (ticket_id);


-- =====================================================================
-- admin_action_audit_logs
-- =====================================================================
CREATE TABLE IF NOT EXISTS public.admin_action_audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id uuid NOT NULL REFERENCES public.admin_portal_users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL DEFAULT 'support_ticket',
    entity_id uuid NOT NULL,
    affected_user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,
    reason TEXT,
    change_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_id ON public.admin_action_audit_logs (admin_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.admin_action_audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON public.admin_action_audit_logs (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_affected_user ON public.admin_action_audit_logs (affected_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.admin_action_audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_created ON public.admin_action_audit_logs (admin_id, created_at DESC);