-- Manual pre-launch rollback only. Run inside a DBA-reviewed transaction.
-- Refuses rollback after any Argon2id+pepper password has been created.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM gotrendlabs_users
        WHERE starts_with(password, 'argon2id_pepper_v1$')
    ) THEN
        RAISE EXCEPTION 'Auth boundary rollback refused: Argon2id password hashes exist';
    END IF;
END;
$$;

DROP TRIGGER IF EXISTS gotrendlabs_guard_django_password_write ON gotrendlabs_users;
DROP FUNCTION IF EXISTS gotrendlabs_guard_django_password_write();
ALTER TABLE gotrendlabs_users OWNER TO gotrendlabs_django;
DO $$
DECLARE
    user_sequence text;
BEGIN
    SELECT pg_get_serial_sequence('gotrendlabs_users', 'id') INTO user_sequence;
    IF user_sequence IS NOT NULL THEN
        EXECUTE format('ALTER SEQUENCE %s OWNER TO gotrendlabs_django', user_sequence);
    END IF;
END;
$$;
