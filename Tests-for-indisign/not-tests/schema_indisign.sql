--
-- PostgreSQL database dump
--

-- Dumped from database version 16.12
-- Dumped by pg_dump version 17.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
-- SET transaction_timeout = 0;  -- Not supported in PostgreSQL < 14
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: update_team_approvals_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_team_approvals_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_logs (
    id character varying(50) NOT NULL,
    envelope_id character varying(50),
    type character varying(50),
    actor_id character varying(50),
    description text,
    created_at timestamp without time zone DEFAULT now(),
    audit_info jsonb
);


--
-- Name: blueprints; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.blueprints (
    id character varying(50) NOT NULL,
    document_id character varying(50),
    name character varying(255) NOT NULL,
    fields jsonb NOT NULL,
    signer_roles jsonb NOT NULL,
    settings jsonb,
    usage_count integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT now(),
    user_id uuid,
    description text,
    expiration_days integer DEFAULT 7,
    signing_order character varying(20) DEFAULT 'sequential'::character varying,
    CONSTRAINT blueprints_signing_order_check CHECK (((signing_order)::text = ANY (ARRAY[('sequential'::character varying)::text, ('parallel'::character varying)::text])))
);


--
-- Name: bulk_sends; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.bulk_sends (
    id character varying(50) NOT NULL,
    user_id uuid,
    blueprint_id character varying(50),
    envelope_id character varying(50),
    csv_data jsonb NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    total_recipients integer NOT NULL,
    successful_recipients integer DEFAULT 0,
    failed_recipients integer DEFAULT 0,
    error_details jsonb,
    created_at timestamp without time zone DEFAULT now(),
    processed_at timestamp without time zone,
    CONSTRAINT bulk_sends_status_check CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('processing'::character varying)::text, ('completed'::character varying)::text, ('failed'::character varying)::text])))
);


--
-- Name: COLUMN bulk_sends.envelope_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.bulk_sends.envelope_id IS 'Legacy: Single envelope ID for old bulk recipient import. NULL for proper bulk send with multiple envelopes. Use envelopes.bulk_send_id to find all envelopes in a bulk send.';


--
-- Name: deleted_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.deleted_users (
    id uuid NOT NULL,
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    first_name character varying(100),
    middle_name character varying(100),
    last_name character varying(100),
    created_at timestamp with time zone NOT NULL,
    deleted_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_by uuid,
    deletion_ip character varying(100),
    deletion_user_agent text,
    deletion_reason character varying(500),
    wallet_balance_at_deletion numeric(10,2) DEFAULT 0.00,
    metadata jsonb
);


--
-- Name: TABLE deleted_users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.deleted_users IS 'Audit trail of deleted user accounts for compliance and security';


--
-- Name: COLUMN deleted_users.id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deleted_users.id IS 'Original user UUID from users table';


--
-- Name: COLUMN deleted_users.deleted_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deleted_users.deleted_at IS 'Timestamp when account was deleted';


--
-- Name: COLUMN deleted_users.deleted_by; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deleted_users.deleted_by IS 'User ID who performed deletion (same as id for self-delete)';


--
-- Name: COLUMN deleted_users.metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.deleted_users.metadata IS 'Additional user data: address, dob, profile picture info, etc.';


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id character varying(50) NOT NULL,
    user_id uuid,
    title character varying(255) NOT NULL,
    file_url text NOT NULL,
    page_count integer,
    uploaded_at timestamp without time zone DEFAULT now(),
    tags text[],
    workflow_id character varying(255)
);


--
-- Name: envelope_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.envelope_audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    envelope_id character varying(50),
    event_type character varying(50) NOT NULL,
    actor_type character varying(20) NOT NULL,
    actor_name character varying(255),
    actor_email character varying(255),
    actor_organization character varying(255),
    ip_address inet,
    user_agent text,
    device_info jsonb,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    event_category character varying(30),
    actor_id character varying(50),
    actor_role character varying(50),
    activity character varying(255),
    description text,
    consent_text text,
    notification_recipients jsonb,
    geo_location jsonb,
    event_timestamp timestamp with time zone DEFAULT now()
);


--
-- Name: envelope_signatures; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.envelope_signatures (
    id character varying(50) NOT NULL,
    envelope_id character varying(50),
    recipient_id character varying(50),
    user_id uuid,
    signer_name character varying(255),
    filled_fields jsonb NOT NULL,
    signature_type character varying(50) NOT NULL,
    signature_base64 text,
    signature_image_url character varying(500),
    aadhaar_transaction_id character varying(255),
    signed_at timestamp without time zone DEFAULT now(),
    signed_from_ip inet,
    created_at timestamp without time zone DEFAULT now(),
    signing_location character varying(255),
    CONSTRAINT envelope_signatures_signature_type_check CHECK (((signature_type)::text = ANY (ARRAY[('aadhaar'::character varying)::text, ('virtual'::character varying)::text])))
);


--
-- Name: COLUMN envelope_signatures.signing_location; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelope_signatures.signing_location IS 'Resolved signing location in "City, Country" format from AWS Location Service (Aadhaar signing only)';


--
-- Name: envelopes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.envelopes (
    id character varying(50) NOT NULL,
    blueprint_id character varying(50),
    user_id uuid,
    document_id character varying(50),
    subject character varying(500),
    email_subject character varying(500) DEFAULT 'Please sign {{document_name}}'::character varying,
    email_body text DEFAULT 'Hi {{recipient_name}}, please sign the document.'::text,
    email_from_name character varying(255),
    reminder_enabled boolean DEFAULT false,
    reminder_interval_days integer DEFAULT 7,
    last_reminder_sent_at timestamp without time zone,
    expiry_date timestamp without time zone,
    total_recipients integer DEFAULT 0,
    signed_recipients integer DEFAULT 0,
    total_cost numeric(12,2),
    cost_debited boolean DEFAULT false,
    status character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    bulk_send_id character varying(50),
    sent_at timestamp without time zone,
    completed_at timestamp without time zone,
    original_pdf_url text,
    signed_pdf_url text,
    created_at timestamp without time zone DEFAULT now(),
    latest_signed_version character varying(255),
    blueprint_fields jsonb,
    blueprint_signer_roles jsonb,
    blueprint_settings jsonb,
    blueprint_name character varying(255),
    blueprint_expiration_days integer,
    blueprint_signing_order character varying(20),
    voided_at timestamp without time zone,
    audit_pdf_url text,
    audit_pdf_generated_at timestamp with time zone,
    active_aadhaar_signer_id character varying(50),
    active_aadhaar_started_at timestamp with time zone,
    active_aadhaar_signer_name character varying(255),
    active_virtual_signers_count integer DEFAULT 0,
    prefilled_fields jsonb
);


--
-- Name: COLUMN envelopes.blueprint_fields; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_fields IS 'Immutable snapshot of blueprint fields at envelope creation time';


--
-- Name: COLUMN envelopes.blueprint_signer_roles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_signer_roles IS 'Immutable snapshot of blueprint signer roles at envelope creation time';


--
-- Name: COLUMN envelopes.blueprint_settings; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_settings IS 'Immutable snapshot of blueprint settings at envelope creation time';


--
-- Name: COLUMN envelopes.blueprint_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_name IS 'Snapshot of blueprint name for reference';


--
-- Name: COLUMN envelopes.blueprint_expiration_days; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_expiration_days IS 'Snapshot of blueprint expiration days';


--
-- Name: COLUMN envelopes.blueprint_signing_order; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.blueprint_signing_order IS 'Snapshot of blueprint signing order (sequential/parallel)';


--
-- Name: COLUMN envelopes.voided_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.voided_at IS 'Timestamp when envelope was voided. NULL means envelope is not voided. Voided envelopes are hidden from signer inbox but remain in envelope list for sender.';


--
-- Name: COLUMN envelopes.active_aadhaar_signer_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.active_aadhaar_signer_id IS 'Recipient ID of the signer currently in an active Aadhaar signing session';


--
-- Name: COLUMN envelopes.active_aadhaar_started_at; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.active_aadhaar_started_at IS 'Timestamp when the active Aadhaar signing session started';


--
-- Name: COLUMN envelopes.active_aadhaar_signer_name; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.active_aadhaar_signer_name IS 'Name of the signer currently in an active Aadhaar signing session (for display)';


--
-- Name: COLUMN envelopes.active_virtual_signers_count; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.envelopes.active_virtual_signers_count IS 'Number of virtual signers currently signing this envelope (allows concurrent virtual signing)';


--
-- Name: filled_fields; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.filled_fields (
    id integer NOT NULL,
    envelope_id character varying(50),
    field_id character varying(50),
    value jsonb,
    filled_by character varying(50),
    user_id uuid,
    filled_at timestamp without time zone DEFAULT now(),
    filled_from_ip inet
);


--
-- Name: filled_fields_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.filled_fields_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: filled_fields_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.filled_fields_id_seq OWNED BY public.filled_fields.id;


--
-- Name: login_cooldowns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.login_cooldowns (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    email character varying(255) NOT NULL,
    ip_address inet,
    reason character varying(50) NOT NULL,
    cooldown_until timestamp with time zone NOT NULL,
    failed_attempts integer DEFAULT 0,
    last_failed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    CONSTRAINT login_cooldowns_reason_check CHECK (((reason)::text = ANY (ARRAY[('max_attempts'::character varying)::text, ('manual'::character varying)::text])))
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    envelope_id character varying(50),
    recipient_id character varying(50),
    type character varying(50) NOT NULL,
    title character varying(255) NOT NULL,
    message text NOT NULL,
    actor_name character varying(255),
    actor_email character varying(255),
    actor_role character varying(100),
    metadata jsonb,
    read boolean DEFAULT false,
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE notifications; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.notifications IS 'Stores real-time notifications for registered users about envelope events';


--
-- Name: COLUMN notifications.type; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.notifications.type IS 'Event type: signer_signed, signer_declined, envelope_completed, signing_progress, envelope_received, envelope_voided, envelope_deleted';


--
-- Name: COLUMN notifications.metadata; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.notifications.metadata IS 'Additional context data: { progress: "2/3", document_name: "Contract", signer_name: "John Doe" }';


--
-- Name: pending_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pending_users (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    first_name character varying(255),
    middle_name character varying(255),
    last_name character varying(255),
    email character varying(255) NOT NULL,
    phone_number character varying(20),
    dob date,
    password_hash text,
    otp_phone_hash text,
    otp_email_hash text,
    otp_phone_sent_at timestamp with time zone,
    otp_email_sent_at timestamp with time zone,
    otp_phone_expires_at timestamp with time zone,
    otp_email_expires_at timestamp with time zone,
    otp_phone_attempts integer DEFAULT 0,
    otp_email_attempts integer DEFAULT 0,
    otp_email_verified boolean DEFAULT false NOT NULL,
    otp_phone_verified boolean DEFAULT false NOT NULL,
    otp_email_verified_at timestamp with time zone,
    otp_phone_verified_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    source_ip inet,
    metadata jsonb,
    address jsonb,
    pii_iv character varying(255),
    pii_auth_tag character varying(255),
    pii_encrypted_dek bytea,
    pii_encrypted_data text
);


--
-- Name: COLUMN pending_users.pii_iv; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pending_users.pii_iv IS 'Base64-encoded initialization vector for AES-256-GCM encryption';


--
-- Name: COLUMN pending_users.pii_auth_tag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pending_users.pii_auth_tag IS 'Base64-encoded authentication tag for AES-256-GCM encryption';


--
-- Name: COLUMN pending_users.pii_encrypted_dek; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pending_users.pii_encrypted_dek IS 'Encrypted data encryption key from AWS KMS (AES-256)';


--
-- Name: COLUMN pending_users.pii_encrypted_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.pending_users.pii_encrypted_data IS 'Base64-encoded encrypted PII blob (all PII fields encrypted together)';


--
-- Name: platform_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.platform_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    action character varying(50) NOT NULL,
    description text,
    ip_address inet,
    user_agent text,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: recipients; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.recipients (
    id character varying(50) NOT NULL,
    envelope_id character varying(50),
    role_name character varying(50),
    name character varying(255),
    email character varying(255),
    phone character varying(20),
    status character varying(20),
    auth_method character varying(20),
    signer_order integer,
    signing_token character varying(500),
    signing_link character varying(500),
    email_sent_at timestamp without time zone,
    last_reminder_sent_at timestamp without time zone,
    reminder_count integer DEFAULT 0,
    rejected_at timestamp without time zone,
    rejection_reason text,
    viewed_at timestamp without time zone,
    sign_type character varying(50),
    signed_at timestamp without time zone,
    signed_from_ip inet,
    aadhaar_transaction_id character varying(255),
    signature_fields jsonb DEFAULT '{"aadhaar": 0, "virtual": 0}'::jsonb,
    signature_data jsonb,
    signing_location character varying(255),
    team_id uuid,
    moved_to_team_by uuid,
    moved_to_team_at timestamp with time zone,
    CONSTRAINT chk_moved_to_team_consistency CHECK ((((moved_to_team_by IS NULL) AND (moved_to_team_at IS NULL)) OR ((moved_to_team_by IS NOT NULL) AND (moved_to_team_at IS NOT NULL))))
);


--
-- Name: COLUMN recipients.signing_location; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.recipients.signing_location IS 'Resolved signing location in "City, Country" format from AWS Location Service (Aadhaar signing only)';


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    token text NOT NULL,
    ip_address inet,
    user_agent text,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    active_team_id uuid
);


--
-- Name: signing_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.signing_sessions (
    id character varying(50) NOT NULL,
    recipient_id character varying(50),
    email character varying(255) NOT NULL,
    otp_hash text NOT NULL,
    otp_sent_at timestamp with time zone DEFAULT now(),
    otp_expires_at timestamp with time zone NOT NULL,
    otp_attempts integer DEFAULT 0,
    otp_verified boolean DEFAULT false,
    otp_verified_at timestamp with time zone,
    ip_address inet,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE signing_sessions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.signing_sessions IS 'OTP sessions for anonymous signer authentication. Signers authenticate using signing_token from URL + OTP verification.';


--
-- Name: team_activity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team_activity_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    team_id uuid NOT NULL,
    actor_id uuid,
    action character varying(50) NOT NULL,
    target_type character varying(30),
    target_id character varying(50),
    details jsonb,
    ip_address character varying(45),
    user_agent text,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: team_approvals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team_approvals (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    team_id uuid NOT NULL,
    requested_by uuid,
    approval_type character varying(30) NOT NULL,
    reference_id character varying(50) NOT NULL,
    reference_metadata jsonb,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    reviewed_by uuid,
    reviewed_at timestamp with time zone,
    review_notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT team_approvals_approval_type_check CHECK (((approval_type)::text = ANY ((ARRAY['send_envelope'::character varying, 'sign_document'::character varying])::text[]))),
    CONSTRAINT team_approvals_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying])::text[])))
);


--
-- Name: team_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.team_members (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    team_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    invited_by uuid,
    joined_at timestamp with time zone DEFAULT now(),
    CONSTRAINT team_members_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'maker'::character varying, 'checker'::character varying, 'viewer'::character varying])::text[]))),
    CONSTRAINT team_members_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'invited'::character varying, 'deactivated'::character varying])::text[])))
);


--
-- Name: teams; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.teams (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now(),
    contact_email character varying(255)
);


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    id character varying(50) NOT NULL,
    user_id uuid,
    type character varying(20),
    amount numeric(12,2),
    description text,
    status character varying(20),
    created_at timestamp without time zone DEFAULT now(),
    gateway_transaction_id character varying(100),
    order_id character varying(100),
    bank_reference_number character varying(50),
    payment_method character varying(20),
    payment_provider character varying(50),
    gateway_status character varying(20),
    transacted_at timestamp without time zone,
    gateway_response jsonb,
    bank_transaction_id character varying
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    wallet_balance numeric(12,2) DEFAULT 0,
    created_at timestamp with time zone DEFAULT now(),
    first_name character varying(255),
    middle_name character varying(255),
    last_name character varying(255),
    phone_number character varying(20),
    dob date,
    password text,
    email_verified boolean DEFAULT false NOT NULL,
    phone_verified boolean DEFAULT false NOT NULL,
    email_verified_at timestamp with time zone,
    phone_verified_at timestamp with time zone,
    address jsonb,
    pii_iv character varying(255),
    pii_auth_tag character varying(255),
    pii_encrypted_dek bytea,
    pii_encrypted_data text,
    profile_picture text,
    profile_picture_b64 text,
    profile_picture_meta jsonb,
    pfp_updated_at timestamp with time zone,
    is_team_account boolean DEFAULT false
);

--
-- Name: admin_action_audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.admin_action_audit_logs  (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  admin_id uuid NOT NULL,                         -- Admin who performed the action
  action VARCHAR(50) NOT NULL,                    -- approve_ticket, reject_ticket, wallet_credit, etc.
  entity_type VARCHAR(50) NOT NULL DEFAULT 'support_ticket', -- Entity affected by action
  entity_id uuid NOT NULL,                -- ID of the affected entity (ticket, wallet event, etc.)
  affected_user_id uuid,                          -- End user impacted by the action
  reason TEXT,                                    -- Admin note/reason sent to user (if any)
  change_summary JSONB NOT NULL DEFAULT '{}'::jsonb, -- Before/after fields, amounts, proof refs
  ip_address INET,
  user_agent TEXT,
  created_at timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: COLUMN users.pii_iv; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.pii_iv IS 'Base64-encoded initialization vector for AES-256-GCM encryption';


--
-- Name: COLUMN users.pii_auth_tag; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.pii_auth_tag IS 'Base64-encoded authentication tag for AES-256-GCM encryption';


--
-- Name: COLUMN users.pii_encrypted_dek; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.pii_encrypted_dek IS 'Encrypted data encryption key from AWS KMS (AES-256)';


--
-- Name: COLUMN users.pii_encrypted_data; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.pii_encrypted_data IS 'Base64-encoded encrypted PII blob (all PII fields encrypted together)';


--
-- Name: COLUMN users.profile_picture; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.users.profile_picture IS 'Base64-encoded profile picture image (JPEG, PNG, etc.)';


--
-- Name: filled_fields id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.filled_fields ALTER COLUMN id SET DEFAULT nextval('public.filled_fields_id_seq'::regclass);


--
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id);


--
-- Name: blueprints blueprints_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blueprints
    ADD CONSTRAINT blueprints_pkey PRIMARY KEY (id);


--
-- Name: bulk_sends bulk_sends_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_sends
    ADD CONSTRAINT bulk_sends_pkey PRIMARY KEY (id);


--
-- Name: deleted_users deleted_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.deleted_users
    ADD CONSTRAINT deleted_users_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: documents documents_workflow_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_workflow_id_key UNIQUE (workflow_id);


--
-- Name: envelope_audit_logs envelope_audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_audit_logs
    ADD CONSTRAINT envelope_audit_logs_pkey PRIMARY KEY (id);


--
-- Name: envelope_signatures envelope_signatures_envelope_id_recipient_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_signatures
    ADD CONSTRAINT envelope_signatures_envelope_id_recipient_id_key UNIQUE (envelope_id, recipient_id);


--
-- Name: envelope_signatures envelope_signatures_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_signatures
    ADD CONSTRAINT envelope_signatures_pkey PRIMARY KEY (id);


--
-- Name: envelopes envelopes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelopes
    ADD CONSTRAINT envelopes_pkey PRIMARY KEY (id);


--
-- Name: filled_fields filled_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.filled_fields
    ADD CONSTRAINT filled_fields_pkey PRIMARY KEY (id);


--
-- Name: login_cooldowns login_cooldowns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_cooldowns
    ADD CONSTRAINT login_cooldowns_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: pending_users pending_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pending_users
    ADD CONSTRAINT pending_users_pkey PRIMARY KEY (id);


--
-- Name: platform_logs platform_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_logs
    ADD CONSTRAINT platform_logs_pkey PRIMARY KEY (id);


--
-- Name: recipients recipients_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_pkey PRIMARY KEY (id);


--
-- Name: recipients recipients_signing_link_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_signing_link_key UNIQUE (signing_link);


--
-- Name: recipients recipients_signing_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_signing_token_key UNIQUE (signing_token);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: signing_sessions signing_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signing_sessions
    ADD CONSTRAINT signing_sessions_pkey PRIMARY KEY (id);


--
-- Name: team_activity_logs team_activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_activity_logs
    ADD CONSTRAINT team_activity_logs_pkey PRIMARY KEY (id);


--
-- Name: team_approvals team_approvals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_approvals
    ADD CONSTRAINT team_approvals_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_team_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_team_id_user_id_key UNIQUE (team_id, user_id);


--
-- Name: teams teams_contact_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_contact_email_key UNIQUE (contact_email);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_activity_logs_audit_info_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_logs_audit_info_gin ON public.activity_logs USING gin (audit_info);


--
-- Name: idx_activity_logs_audit_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_logs_audit_ip ON public.activity_logs USING btree (((audit_info ->> 'ip_address'::text)));


--
-- Name: idx_activity_logs_envelope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activity_logs_envelope ON public.activity_logs USING btree (envelope_id);


--
-- Name: idx_blueprints_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blueprints_document ON public.blueprints USING btree (document_id);


--
-- Name: idx_blueprints_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blueprints_user ON public.blueprints USING btree (user_id);


--
-- Name: idx_bulk_sends_envelope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bulk_sends_envelope ON public.bulk_sends USING btree (envelope_id);


--
-- Name: idx_bulk_sends_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_bulk_sends_user ON public.bulk_sends USING btree (user_id);


--
-- Name: idx_deleted_users_deleted_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deleted_users_deleted_at ON public.deleted_users USING btree (deleted_at);


--
-- Name: idx_deleted_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deleted_users_email ON public.deleted_users USING btree (email);


--
-- Name: idx_deleted_users_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_deleted_users_phone ON public.deleted_users USING btree (phone_number);


--
-- Name: idx_envelope_audit_logs_actor_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_actor_email ON public.envelope_audit_logs USING btree (actor_email);


--
-- Name: idx_envelope_audit_logs_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_category ON public.envelope_audit_logs USING btree (event_category);


--
-- Name: idx_envelope_audit_logs_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_created ON public.envelope_audit_logs USING btree (created_at);


--
-- Name: idx_envelope_audit_logs_envelope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_envelope ON public.envelope_audit_logs USING btree (envelope_id);


--
-- Name: idx_envelope_audit_logs_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_timestamp ON public.envelope_audit_logs USING btree (event_timestamp);


--
-- Name: idx_envelope_audit_logs_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_audit_logs_type ON public.envelope_audit_logs USING btree (event_type);


--
-- Name: idx_envelope_signatures_aadhaar_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_signatures_aadhaar_txn ON public.envelope_signatures USING btree (aadhaar_transaction_id);


--
-- Name: idx_envelope_signatures_envelope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_signatures_envelope ON public.envelope_signatures USING btree (envelope_id);


--
-- Name: idx_envelope_signatures_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_signatures_recipient ON public.envelope_signatures USING btree (recipient_id);


--
-- Name: idx_envelope_signatures_signing_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_signatures_signing_location ON public.envelope_signatures USING btree (signing_location);


--
-- Name: idx_envelope_signatures_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelope_signatures_user ON public.envelope_signatures USING btree (user_id);


--
-- Name: idx_envelopes_active_aadhaar; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_active_aadhaar ON public.envelopes USING btree (id, active_aadhaar_signer_id) WHERE (active_aadhaar_signer_id IS NOT NULL);


--
-- Name: idx_envelopes_active_virtual; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_active_virtual ON public.envelopes USING btree (id, active_virtual_signers_count) WHERE (active_virtual_signers_count > 0);


--
-- Name: idx_envelopes_blueprint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_blueprint ON public.envelopes USING btree (blueprint_id);


--
-- Name: idx_envelopes_bulk_send; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_bulk_send ON public.envelopes USING btree (bulk_send_id);


--
-- Name: idx_envelopes_document; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_document ON public.envelopes USING btree (document_id);


--
-- Name: idx_envelopes_latest_signed_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_latest_signed_version ON public.envelopes USING btree (latest_signed_version);


--
-- Name: idx_envelopes_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_status ON public.envelopes USING btree (status);


--
-- Name: idx_envelopes_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_user ON public.envelopes USING btree (user_id);


--
-- Name: idx_envelopes_voided; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_envelopes_voided ON public.envelopes USING btree (voided_at);


--
-- Name: idx_login_cooldowns_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_cooldowns_email ON public.login_cooldowns USING btree (email);


--
-- Name: idx_login_cooldowns_ip; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_cooldowns_ip ON public.login_cooldowns USING btree (ip_address);


--
-- Name: idx_login_cooldowns_until; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_cooldowns_until ON public.login_cooldowns USING btree (cooldown_until);


--
-- Name: idx_login_cooldowns_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_login_cooldowns_user ON public.login_cooldowns USING btree (user_id);


--
-- Name: idx_notifications_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at DESC);


--
-- Name: idx_notifications_envelope_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_envelope_id ON public.notifications USING btree (envelope_id);


--
-- Name: idx_notifications_read; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_read ON public.notifications USING btree (read);


--
-- Name: idx_notifications_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_type ON public.notifications USING btree (type);


--
-- Name: idx_notifications_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: idx_notifications_user_unread; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notifications_user_unread ON public.notifications USING btree (user_id, read) WHERE (read = false);


--
-- Name: idx_pending_users_address_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pending_users_address_gin ON public.pending_users USING gin (address);


--
-- Name: idx_pending_users_address_pincode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pending_users_address_pincode ON public.pending_users USING btree (((address ->> 'pincode'::text)));


--
-- Name: idx_pending_users_pii_iv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pending_users_pii_iv ON public.pending_users USING btree (pii_iv);


--
-- Name: idx_platform_logs_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_logs_action ON public.platform_logs USING btree (action);


--
-- Name: idx_platform_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_logs_created_at ON public.platform_logs USING btree (created_at);


--
-- Name: idx_platform_logs_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_platform_logs_user ON public.platform_logs USING btree (user_id);


--
-- Name: idx_recipients_aadhaar_txn; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_aadhaar_txn ON public.recipients USING btree (aadhaar_transaction_id);


--
-- Name: idx_recipients_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_email ON public.recipients USING btree (email);


--
-- Name: idx_recipients_signature_data_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_signature_data_gin ON public.recipients USING gin (signature_data);


--
-- Name: idx_recipients_signing_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_signing_location ON public.recipients USING btree (signing_location);


--
-- Name: idx_recipients_signing_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_signing_token ON public.recipients USING btree (signing_token);


--
-- Name: idx_recipients_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_status ON public.recipients USING btree (status);


--
-- Name: idx_recipients_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_recipients_team_id ON public.recipients USING btree (team_id) WHERE (team_id IS NOT NULL);


--
-- Name: idx_sessions_active_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_active_team_id ON public.sessions USING btree (active_team_id);


--
-- Name: idx_sessions_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_token ON public.sessions USING btree (token);


--
-- Name: idx_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sessions_user ON public.sessions USING btree (user_id);


--
-- Name: idx_signing_sessions_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_signing_sessions_email ON public.signing_sessions USING btree (email);


--
-- Name: idx_signing_sessions_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_signing_sessions_recipient ON public.signing_sessions USING btree (recipient_id);


--
-- Name: idx_team_activity_logs_actor_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_activity_logs_actor_id ON public.team_activity_logs USING btree (actor_id);


--
-- Name: idx_team_activity_logs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_activity_logs_created_at ON public.team_activity_logs USING btree (created_at DESC);


--
-- Name: idx_team_activity_logs_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_activity_logs_team_id ON public.team_activity_logs USING btree (team_id);


--
-- Name: idx_team_activity_team_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_activity_team_time ON public.team_activity_logs USING btree (team_id, created_at DESC);


--
-- Name: idx_team_approvals_requested_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_approvals_requested_by ON public.team_approvals USING btree (requested_by);


--
-- Name: idx_team_approvals_reviewed_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_approvals_reviewed_by ON public.team_approvals USING btree (reviewed_by) WHERE (reviewed_by IS NOT NULL);


--
-- Name: idx_team_approvals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_approvals_status ON public.team_approvals USING btree (status);


--
-- Name: idx_team_approvals_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_approvals_team_id ON public.team_approvals USING btree (team_id);


--
-- Name: idx_team_approvals_team_pending; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_approvals_team_pending ON public.team_approvals USING btree (team_id, status) WHERE ((status)::text = 'pending'::text);


--
-- Name: idx_team_members_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_members_status ON public.team_members USING btree (status);


--
-- Name: idx_team_members_team_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_members_team_id ON public.team_members USING btree (team_id);


--
-- Name: idx_team_members_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_team_members_user_id ON public.team_members USING btree (user_id);


--
-- Name: idx_teams_contact_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_teams_contact_email ON public.teams USING btree (contact_email) WHERE (contact_email IS NOT NULL);


--
-- Name: idx_teams_created_by; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_teams_created_by ON public.teams USING btree (created_by);


--
-- Name: idx_teams_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_teams_user_id ON public.teams USING btree (user_id);


--
-- Name: idx_transactions_gateway_txn_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_gateway_txn_id ON public.transactions USING btree (gateway_transaction_id);


--
-- Name: idx_transactions_order_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_order_id ON public.transactions USING btree (order_id);


--
-- Name: idx_transactions_payment_method; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_payment_method ON public.transactions USING btree (payment_method);


--
-- Name: idx_transactions_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_status ON public.transactions USING btree (status);


--
-- Name: idx_transactions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_user ON public.transactions USING btree (user_id);


--
-- Name: idx_transactions_user_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_transactions_user_created_at ON public.transactions USING btree (user_id, created_at DESC);


--
-- Name: idx_users_address_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_address_gin ON public.users USING gin (address);


--
-- Name: idx_users_address_pincode; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_address_pincode ON public.users USING btree (((address ->> 'pincode'::text)));


--
-- Name: idx_users_pii_iv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_users_pii_iv ON public.users USING btree (pii_iv);


--
-- Name: uq_pending_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_pending_users_email ON public.pending_users USING btree (email);


--
-- Name: uq_pending_users_phone; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_pending_users_phone ON public.pending_users USING btree (phone_number);


--
-- Name: team_approvals trg_team_approvals_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_team_approvals_updated_at BEFORE UPDATE ON public.team_approvals FOR EACH ROW EXECUTE FUNCTION public.update_team_approvals_updated_at();


--
-- Name: activity_logs activity_logs_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: blueprints blueprints_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blueprints
    ADD CONSTRAINT blueprints_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: blueprints blueprints_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blueprints
    ADD CONSTRAINT blueprints_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: bulk_sends bulk_sends_blueprint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_sends
    ADD CONSTRAINT bulk_sends_blueprint_id_fkey FOREIGN KEY (blueprint_id) REFERENCES public.blueprints(id) ON DELETE CASCADE;


--
-- Name: bulk_sends bulk_sends_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_sends
    ADD CONSTRAINT bulk_sends_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: bulk_sends bulk_sends_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.bulk_sends
    ADD CONSTRAINT bulk_sends_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: documents documents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: envelope_audit_logs envelope_audit_logs_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_audit_logs
    ADD CONSTRAINT envelope_audit_logs_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: envelope_signatures envelope_signatures_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_signatures
    ADD CONSTRAINT envelope_signatures_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: envelope_signatures envelope_signatures_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_signatures
    ADD CONSTRAINT envelope_signatures_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.recipients(id) ON DELETE CASCADE;


--
-- Name: envelope_signatures envelope_signatures_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelope_signatures
    ADD CONSTRAINT envelope_signatures_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: envelopes envelopes_blueprint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelopes
    ADD CONSTRAINT envelopes_blueprint_id_fkey FOREIGN KEY (blueprint_id) REFERENCES public.blueprints(id) ON DELETE CASCADE;


--
-- Name: envelopes envelopes_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelopes
    ADD CONSTRAINT envelopes_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- Name: envelopes envelopes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.envelopes
    ADD CONSTRAINT envelopes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: filled_fields filled_fields_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.filled_fields
    ADD CONSTRAINT filled_fields_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: filled_fields filled_fields_filled_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.filled_fields
    ADD CONSTRAINT filled_fields_filled_by_fkey FOREIGN KEY (filled_by) REFERENCES public.recipients(id) ON DELETE CASCADE;


--
-- Name: filled_fields filled_fields_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.filled_fields
    ADD CONSTRAINT filled_fields_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: login_cooldowns login_cooldowns_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.login_cooldowns
    ADD CONSTRAINT login_cooldowns_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: notifications notifications_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.recipients(id) ON DELETE SET NULL;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: platform_logs platform_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.platform_logs
    ADD CONSTRAINT platform_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: recipients recipients_envelope_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_envelope_id_fkey FOREIGN KEY (envelope_id) REFERENCES public.envelopes(id) ON DELETE CASCADE;


--
-- Name: recipients recipients_moved_to_team_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_moved_to_team_by_fkey FOREIGN KEY (moved_to_team_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: recipients recipients_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.recipients
    ADD CONSTRAINT recipients_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE SET NULL;


--
-- Name: sessions sessions_active_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_active_team_id_fkey FOREIGN KEY (active_team_id) REFERENCES public.teams(id) ON DELETE SET NULL;


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: signing_sessions signing_sessions_recipient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.signing_sessions
    ADD CONSTRAINT signing_sessions_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.recipients(id) ON DELETE CASCADE;


--
-- Name: team_activity_logs team_activity_logs_actor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_activity_logs
    ADD CONSTRAINT team_activity_logs_actor_id_fkey FOREIGN KEY (actor_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: team_activity_logs team_activity_logs_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_activity_logs
    ADD CONSTRAINT team_activity_logs_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: team_approvals team_approvals_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_approvals
    ADD CONSTRAINT team_approvals_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: team_approvals team_approvals_reviewed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_approvals
    ADD CONSTRAINT team_approvals_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: team_approvals team_approvals_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_approvals
    ADD CONSTRAINT team_approvals_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_invited_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_invited_by_fkey FOREIGN KEY (invited_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: team_members team_members_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: teams teams_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: teams teams_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--

--
-- Admin Portal Tables (New)
--

--
-- Name: admin_portal_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.admin_portal_users (
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
    CONSTRAINT admin_portal_users_role_check CHECK ((role = ANY (ARRAY['admin'::character varying, 'editor'::character varying])))
);

-- ALTER TABLE public.admin_portal_users OWNER TO -;

CREATE UNIQUE INDEX idx_admin_portal_users_email ON public.admin_portal_users (email);
CREATE INDEX idx_admin_portal_users_role ON public.admin_portal_users (role);
CREATE INDEX idx_admin_portal_users_active ON public.admin_portal_users (is_active);
CREATE INDEX idx_admin_portal_users_last_login ON public.admin_portal_users (last_login_at DESC);


--
-- Name: support_tickets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.support_tickets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    ticket_type character varying(50) NOT NULL,
    status character varying(20) NOT NULL DEFAULT 'open'::character varying,
    resolved_by_id uuid,
    attachments jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    resolved_at timestamp with time zone,
    CONSTRAINT support_tickets_status_check CHECK ((status = ANY (ARRAY['open'::character varying, 'in_progress'::character varying, 'resolved'::character varying, 'closed'::character varying])))
);

-- ALTER TABLE public.support_tickets OWNER TO -;

CREATE INDEX idx_support_tickets_user_id ON public.support_tickets (user_id);
CREATE INDEX idx_support_tickets_status ON public.support_tickets (status);
CREATE INDEX idx_support_tickets_created_at ON public.support_tickets (created_at DESC);
CREATE INDEX idx_support_tickets_attachments ON public.support_tickets USING GIN (attachments);

-- ALTER TABLE public.admin_action_audit_logs OWNER TO -;

CREATE INDEX idx_audit_logs_admin_id ON public.admin_action_audit_logs (admin_id);
CREATE INDEX idx_audit_logs_action ON public.admin_action_audit_logs (action);
CREATE INDEX idx_audit_logs_entity ON public.admin_action_audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_logs_affected_user ON public.admin_action_audit_logs (affected_user_id);
CREATE INDEX idx_audit_logs_created_at ON public.admin_action_audit_logs (created_at DESC);
CREATE INDEX idx_audit_logs_admin_created ON public.admin_action_audit_logs (admin_id, created_at DESC);


--
-- Foreign Keys for New Tables
--

ALTER TABLE ONLY public.support_tickets
    ADD CONSTRAINT support_tickets_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.support_tickets
    ADD CONSTRAINT support_tickets_resolved_by_id_fkey FOREIGN KEY (resolved_by_id) REFERENCES public.admin_portal_users(id) ON DELETE SET NULL;

ALTER TABLE ONLY public.admin_action_audit_logs
    ADD CONSTRAINT admin_action_audit_logs_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES public.admin_portal_users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.admin_action_audit_logs
    ADD CONSTRAINT admin_action_audit_logs_affected_user_id_fkey FOREIGN KEY (affected_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Triggers for New Tables
--

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
    SELECT 1
    FROM public.users u
    WHERE LOWER(u.email) = LOWER(NEW.email)
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

--
-- PostgreSQL database dump complete
--