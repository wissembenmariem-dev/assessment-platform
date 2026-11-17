DO $$
DECLARE
    cname text;
BEGIN
    SELECT conname INTO cname
    FROM pg_constraint
    WHERE conrelid = 'questions'::regclass
      AND contype = 'u'
      AND array_length(conkey, 1) = 1
      AND conkey[1] = (
          SELECT attnum FROM pg_attribute
          WHERE attrelid = 'questions'::regclass AND attname = 'slug'
      )
    LIMIT 1;

    IF cname IS NOT NULL THEN
        EXECUTE format('ALTER TABLE questions DROP CONSTRAINT %I', cname);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'questions'::regclass
          AND contype = 'u'
          AND conname = 'questions_slug_lang_unique'
    ) THEN
        ALTER TABLE questions
        ADD CONSTRAINT questions_slug_lang_unique UNIQUE (slug, lang);
    END IF;
END $$;
