-- Run as the migration role, after creating/granting gotrendlabs_auth_owner.
-- Repeat after migrations to grant UPDATE on new non-password columns.
ALTER TABLE gotrendlabs_users OWNER TO gotrendlabs_auth_owner;

CREATE OR REPLACE FUNCTION gotrendlabs_guard_django_password_write()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF current_user = 'gotrendlabs_django' THEN
        IF TG_OP = 'UPDATE' AND NEW.password IS DISTINCT FROM OLD.password THEN
            RAISE EXCEPTION 'Django may not change account passwords';
        ELSIF TG_OP = 'INSERT' AND NEW.password <> '' AND LEFT(NEW.password, 1) <> '!' THEN
            RAISE EXCEPTION 'Django may not create usable account passwords';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;
ALTER FUNCTION gotrendlabs_guard_django_password_write() OWNER TO gotrendlabs_auth_owner;

DROP TRIGGER IF EXISTS gotrendlabs_guard_django_password_write ON gotrendlabs_users;
CREATE TRIGGER gotrendlabs_guard_django_password_write
BEFORE INSERT OR UPDATE OF password ON gotrendlabs_users
FOR EACH ROW EXECUTE FUNCTION gotrendlabs_guard_django_password_write();

REVOKE ALL ON TABLE gotrendlabs_users FROM PUBLIC, gotrendlabs_django, gotrendlabs_fastapi;
GRANT SELECT, INSERT ON TABLE gotrendlabs_users TO gotrendlabs_django;
GRANT SELECT, INSERT, UPDATE ON TABLE gotrendlabs_users TO gotrendlabs_fastapi;

DO $$
DECLARE
    writable_columns text;
    user_sequence text;
BEGIN
    SELECT string_agg(format('%I', attname), ', ' ORDER BY attnum)
      INTO writable_columns
      FROM pg_attribute
     WHERE attrelid = 'gotrendlabs_users'::regclass
       AND attnum > 0 AND NOT attisdropped AND attname <> 'password';
    EXECUTE format('GRANT UPDATE (%s) ON TABLE gotrendlabs_users TO gotrendlabs_django', writable_columns);

    SELECT pg_get_serial_sequence('gotrendlabs_users', 'id') INTO user_sequence;
    IF user_sequence IS NOT NULL THEN
        EXECUTE format('ALTER SEQUENCE %s OWNER TO gotrendlabs_auth_owner', user_sequence);
        EXECUTE format('GRANT USAGE, SELECT ON SEQUENCE %s TO gotrendlabs_django, gotrendlabs_fastapi', user_sequence);
    END IF;
END;
$$;
