# Isolated staging creation checklist

No production writes. Production Worker voxgo-api, D1 voxgo and api.voxgo.cn remain
unchanged with TELEMETRY_ENABLED=false.

1. Create a new D1 database named voxgo-staging. Record its Database ID; it must
   differ from production 3fd6ba24-2e44-412e-972c-0929a10cfd06.
2. On this NEW database only, run voxgo-api repository migrations/0001_telemetry.sql.
   No legacy ALTER statements are needed on a new database.
3. Create Worker voxgo-api-staging from the same tested repository entry src/index.js.
   Use a dedicated Wrangler staging config/explicit environment, not the production
   wrangler.jsonc unchanged. Otherwise deployment targets production.
4. Bind DB to voxgo-staging ONLY. Binding name DB matches shared code; isolation is
   provided by the separate resource ID, not by renaming the binding.
5. Staging variables: TELEMETRY_ENABLED=false initially,
   TELEMETRY_SAMPLE_RATE=1, SYNC_INTERVAL_SECONDS=900. Do not modify production vars.
6. Create staging-only rate-limit bindings IP_LIMITER and INSTALL_LIMITER with
   unused account namespace IDs (e.g.43011/43012 after checking), limits60/60sec
   and14/60sec. Do not share production namespace IDs43001/43002.
7. Register hourly cron 17 * * * * for this Worker and its staging DB.
8. Keep workers.dev enabled. Do not bind api.voxgo.cn or any production route.
9. Deploy disabled. Verify health database:ready and config telemetry_enabled:false.
10. Recheck the DB resource ID and bindings, then enable TELEMETRY_ENABLED=true
    ONLY on staging for synthetic testing. Keep deployment config aligned so a
    later build cannot overwrite intended values.
11. Send the staging HTTPS URL and staging Database ID/name to the implementer.
    Never send account secrets or API tokens in chat.

Acceptance after creation: use isolated temporary client state, new synthetic UUID,
zero/text-free numeric metrics. Test config, exact POST acknowledgment, duplicate,
newer then older revision, conflict, invalid schema/hash, and query staging D1 to
confirm single latest row. Test disabled switch, cleanup of controlled expired
staging rows and desktop connectivity. Remove synthetic rows only in staging when
finished. Browser GET success alone does not demonstrate desktop write success.

No staging environment exists as of this implementation: real HTTP write acceptance
is BLOCKED on these resources, not reported as passed. Test fixtures/local transport
simulations must never be relabeled staging validation.
