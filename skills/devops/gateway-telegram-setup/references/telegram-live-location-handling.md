# Telegram live-location handling

Applicability: Hermes Gateway Telegram adapter work involving user-shared location pins, venues, and Telegram live-location updates. This is about inbound Telegram location semantics, not generic maps/geocoding and not outbound bot live-location publishing.

## Key behavior verified

`python-telegram-bot` `MessageHandler(filters.LOCATION)` can dispatch both normal `update.message` location pins and `update.edited_message` live-location updates because the filter checks `Update.effective_message` and includes edited message payloads.

A representative fixture shape:

```python
payload = {
    "update_id": 100,
    "edited_message": {
        "message_id": 7,
        "date": 1700000000,
        "edit_date": 1700000005,
        "chat": {"id": 123, "type": "private", "first_name": "A"},
        "from": {"id": 123, "is_bot": False, "first_name": "A"},
        "location": {
            "latitude": 34.261,
            "longitude": 108.942,
            "live_period": 3600,
            "heading": 90,
            "horizontal_accuracy": 15,
        },
    },
}
```

Expected PTB facts:

```python
u = Update.de_json(payload, bot=None)
assert u.effective_message is u.edited_message
assert filters.LOCATION.check_update(u) is True
assert u.effective_message.location.live_period == 3600
```

## Hermes gateway inspection pattern

1. Check handler registration in `gateway/platforms/telegram.py`:
   - `TelegramMessageHandler(filters.LOCATION | filters.VENUE, self._handle_location_message)`
   - polling/webhook `allowed_updates=Update.ALL_TYPES`
2. Inspect `_handle_location_message` for whether it distinguishes:
   - normal pin vs venue;
   - live location (`location.live_period is not None`);
   - live-location edits (`update.edited_message is not None`);
   - metadata fields: `horizontal_accuracy`, `heading`, `proximity_alert_radius`, `edit_date`.
3. Verify whether the adapter keeps state keyed by `chat_id + message_id`. Telegram reuses the message id for a live-location stream, so this is the natural live-location state key.
4. Search for outbound APIs only if the task includes bot-originated location sharing: `send_location`, `edit_message_live_location`, `stop_message_live_location`. Absence means inbound-only support.

## Recommended inbound live-location design

Default behavior should not send every edited live-location update through the agent. Treat live locations as a stream:

- On first live-location message: notify the agent once that the user started sharing live location, including coordinates, live period, accuracy, heading, and a map link.
- On edited live-location updates: update adapter-local state and only notify the agent when a meaningful threshold is crossed.
- Suggested notification thresholds:
  - moved more than a configured distance, e.g. 100m;
  - enough time has passed since the last agent notification, e.g. 60-120s;
  - the active session is explicitly doing navigation/pickup/meetup work;
  - heading/accuracy changes materially for the task.
- Clean up state when `live_period` expires or when Telegram indicates the live location has stopped.

State fields to consider:

```text
chat_id, user_id, message_id, started_at, expires_at,
last_lat, last_lon, last_update_at, last_agent_notified_at,
horizontal_accuracy, heading, update_count
```

## Privacy and safety constraints

- Do not save live-location coordinates to durable memory.
- Avoid long-term full-track logs; keep only bounded, operational state needed for the active session.
- Do not cross-post live-location data to other platforms/channels unless explicitly requested and permission-safe.
- Preserve group mention/observe gating; unmentioned group live-location updates should not wake the agent merely because they are edited messages.

## Test checklist

Add focused tests when changing this area:

- normal location pin behavior remains unchanged;
- venue behavior remains unchanged;
- edited live-location payload hits `_handle_location_message`;
- first live-location update creates a `MessageEvent` with live metadata;
- subsequent edits inside the threshold update state without waking the agent;
- edits outside the threshold produce one update event;
- group unmentioned live locations follow observe/gating behavior;
- outbound live-location support is tested separately if `send_location`/`edit_message_live_location` is added.
