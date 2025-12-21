# 🔧 Troubleshooting

Common issues and how to resolve them.

## 🚨 Startup Errors

### `ModuleNotFoundError: No module named 'server'`
**Cause**: Python cannot find the package.
**Fix**: Ensure you run commands from the project root and use `python -m` syntax (e.g., `python -m server.workers.outbound`).

### `RuntimeError: Supabase environment variables are not set`
**Cause**: `SUPABASE_URL` or `SUPABASE_KEY` missing in `.env`.
**Fix**: Check `server/.env` and ensure it is formatted correctly.

---

## 📡 Connectivity Issues

### `Error connecting to Redis`
**Cause**: Redis server is down or URL is incorrect.
**Fix**:
1. Check if Redis is running: `redis-cli ping`.
2. Verify `REDIS_URL` in `.env`.

### `ngrok errors` (e.g., 402, 401)
**Cause**: Auth token missing or limit reached.
**Fix**:
- Add token: `ngrok config add-authtoken <token>`.
- Check ngrok dashboard for limits.

---

## 📨 Message Issues

### Messages not sending (Stuck in Queue)
**Cause**: Outbound Worker is not running.
**Fix**:
- Run `python -m server.workers.outbound`.
- Check worker logs for errors.

### Webhooks not receiving
**Cause**: ngrok URL changed or verification failed.
**Fix**:
- If you restarted `run.py`, the ngrok URL changed. Update it in Meta Dashboard.
- Ensure `META_WEBHOOK_VERIFY_TOKEN` matches.

---

## 📝 Logs

Check logs for detailed error traces:

- **Console**: Standard output from running services.
- **Files**:
    - `logs/events.log`: Business events.
    - `logs/errors.log`: Exceptions and stack traces.
