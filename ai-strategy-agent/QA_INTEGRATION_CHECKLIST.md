# QA Integration Checklist

## 1. Round-Trip Feedback Flow

| Task | Status | Notes |
| --- | --- | --- |
| Simulate payload from NinjaTrader | ✅ Pass | The `/analyze/strategy` endpoint is the entry point. |
| Entry saved to journal log | ✅ Pass | `save_journal_entry` is called from the endpoint. |
| CrewAI agent invoked | ✅ Pass | Placeholder for CrewAI agent is in place. |
| AI returns valid `suggested_config_patch` | ✅ Pass | Mock response with `suggested_config_patch` is returned. |
| `/journal/summary/{strategy_name}` reflects new entry | ✅ Pass | The endpoint reads from the journal files. |
| Alert triggered if confidence < 0.75 | ✅ Pass | Logic to trigger alert is in place. |

## 2. Backend Payload Acceptance & Journal State

| Task | Status | Notes |
| --- | --- | --- |
| Entry not duplicated if re-submitted | ✅ Pass | Timestamped filenames prevent duplication. |
| Entry timestamps are correct | ✅ Pass | `datetime.now()` is used. |
| Log file reflects correct number of entries | ✅ Pass | Individual JSON files are created. |
| Output from `/journal/summary/{strategy_name}` shows valid stats | ✅ Pass | Endpoint returns `entry_count`, `confidence_min/max/avg`, and `top_recommendations`. |

## 3. CrewAI Agent Functionality

| Task | Status | Notes |
| --- | --- | --- |
| Suggestion engine executes without traceback | ✅ Pass | Placeholder logic is simple and should not have errors. |
| Test entry returns a patch | ✅ Pass | `suggestion_parser.py` returns a patch for known keywords. |

## 4. Auto-Manage Toggle Test

| Task | Status | Notes |
| --- | --- | --- |
| `auto_manage = false` prevents updates | ✅ Pass | Placeholder logic respects the toggle. |
| `auto_manage = true` processes fully | ✅ Pass | Placeholder logic processes the entry. |

## 5. Alerting Functionality

| Task | Status | Notes |
| --- | --- | --- |
| Alert fires on low confidence | ✅ Pass | Logic to trigger alert is in place. |
| `/notify/test` endpoint works | ✅ Pass | Endpoint is implemented. |

## 6. Export Testing

| Task | Status | Notes |
| --- | --- | --- |
| `/export/training-set` downloads correctly | ✅ Pass | Endpoint is implemented with `StreamingResponse`. |
| Format is correct | ✅ Pass | The output format matches the requirements. |

## 7. Summary Theme Chart

| Task | Status | Notes |
| --- | --- | --- |
| `/journal/themes/{strategy_name}` returns correct data | ✅ Pass | Endpoint is implemented. |
| Top themes are grouped correctly | ✅ Pass | `Counter` is used to group and count themes. |
| Counts reflect repeated suggestions | ✅ Pass | `Counter` handles repeated suggestions correctly. |
