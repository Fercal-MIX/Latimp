-- Verificări pentru memento-uri, pe baza reală. Totul se anulează la final (excepția „TOATE TREC”).
-- Se rulează în SQL Editor; dacă o verificare pică, mesajul spune care.
do $$
declare u uuid := gen_random_uuid(); n int;
begin
  insert into auth.users(id, instance_id, aud, role, email, created_at, updated_at)
    values (u, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated', 'test-memento@example.invalid', now(), now());
  perform set_config('request.jwt.claims', json_build_object('sub', u, 'role', 'authenticated')::text, true);

  -- 1. un memento ajuns la oră, încă netrimis, nu se pierde când telefonul retrimite lista (care are doar viitorul)
  insert into public.reminders(user_id, at, title, body, tag) values (u, now() - interval '2 minutes', 'T', 'due', 'lt-1~a');
  perform private.set_reminders(jsonb_build_array(jsonb_build_object('at', now() + interval '3 days', 'title', 'T', 'body', 'later', 'tag', 'lt-2~a')));
  select count(*) into n from public.reminders where user_id = u and body = 'due' and sent_at is null;
  if n <> 1 then raise exception 'PICĂ 1: memento-ul ajuns la oră a fost șters'; end if;

  -- 2. aceeași listă trimisă de două ori nu dublează memento-urile
  perform private.set_reminders(jsonb_build_array(jsonb_build_object('at', now() + interval '3 days', 'title', 'T', 'body', 'later', 'tag', 'lt-2~a')));
  select count(*) into n from public.reminders where user_id = u and body = 'later';
  if n <> 1 then raise exception 'PICĂ 2: memento dublat (% rânduri)', n; end if;

  -- 3. trimițătorul ia un memento o singură dată, chiar dacă rulează de două ori
  select count(*) into n from public.claim_reminders(1000) c where c.user_id = u;
  if n <> 1 then raise exception 'PICĂ 3: prima preluare a luat % rânduri', n; end if;
  select count(*) into n from public.claim_reminders(1000) c where c.user_id = u;
  if n <> 0 then raise exception 'PICĂ 3: a doua preluare a luat din nou % rânduri', n; end if;

  -- 4. memento-urile viitoare scoase din listă se șterg
  perform private.set_reminders('[]'::jsonb);
  select count(*) into n from public.reminders where user_id = u and body = 'later';
  if n <> 0 then raise exception 'PICĂ 4: memento-ul scos din listă a rămas'; end if;

  raise exception 'TOATE TREC (anulat)';
end $$;
