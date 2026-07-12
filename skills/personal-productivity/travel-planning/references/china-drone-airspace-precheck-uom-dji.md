# China drone airspace precheck: UOM + DJI + local scenic gates

Applicability: Mainland China travel planning or live trip execution where the user wants to fly a consumer drone in scenic areas, road-trip stops, border-adjacent regions, airports/cities, bridges/highways, nature reserves, or managed scenic areas.

Anti-conditions:
- Do not treat this as legal advice or permission to fly.
- Do not infer legality from another traveler having flown there.
- Do not treat DJI GEO status as a substitute for UOM/UTMISS legal airspace status or scenic-area rules.
- Do not log in, submit applications, enter credentials, or perform identity/payment actions for the user unless explicitly authorized and safe.

## Core gate

Before recommending a drone flight, require all three layers:

1. **UOM / 民用无人驾驶航空器综合管理平台**: check current airspace under `运行管理 → 空域信息查询`; submit/prepare flight activity application when the location/time/height is not clearly within legal适飞 scope. Official UOM notice from 2026-05-14 says新版无人驾驶航空器适飞空域 is queried in that module.
2. **DJI FlySafe / DJI Fly GEO**: check whether the device/app shows red禁飞、blue授权、gray限高、警示/加强警示, or scenic demonstration / green zones. DJI GEO is operational/device-level only and may omit some legally restricted areas.
3. **Local authority / scenic spot**: check scenic-area游客中心、酒店/民宿、当地派出所/management staff. Scenic areas, border regions, wetland/wildlife areas, bridges/highways, checkpoints, airports, and crowds can still prohibit flight even if DJI does not lock the drone.

If any layer is unknown, denied, or requires approval not yet granted: advise **do not fly**.

## Pre-reporting shape

Do not report a whole route. Prepare candidate points by:

- exact takeoff point or small area;
- intended date/time window;
- altitude (keep ≤120m unless explicitly approved);
- radius/scope;
- drone model/serial/remote ID if required by the platform;
- purpose: personal travel filming;
- fallback: no-fly if wind/weather/crowd/road safety is bad.

For road trips, ask for or provide a candidate list such as: scenic-area parking edge away from crowds, non-road open viewpoint, lodging-approved open area, and explicit no-fly points (airport/city/bridge/highway/checkpoint/wetland/wildlife/core scenic crowd zones).

## DJI public map/API probe pattern

The DJI FlySafe web map at `https://fly-safe.dji.com/nfz/nfz-query` loads current public GEO zones. A useful read-only endpoint observed in 2026-07:

```text
https://flysafe-api.dji.com/api/qep/geo/feedback/areas/in_rectangle?ltlat=<north>&ltlng=<west>&rblat=<south>&rblng=<east>&zones_mode=flysafe_website&drone=dji-mavic-3&level=0,1,2,3,7,8,10
```

Interpretation cautions:

- Red / `level=2` airport-style zones indicate DJI no-fly/strong restriction.
- Blue/authorization/limit-height/warning zones require their corresponding DJI app unlock or caution.
- Green or dark-green scenic/suitable/demonstration zones are **not permission**; they mean continue to UOM + local scenic gates.
- DJI temporary notice list can be checked, but absence of a keyword is not proof that no government/scenic restriction exists.

## Session-derived Sayram Lake pattern (2026-07)

For a Xinjiang/Ili route, public DJI query around Sayram Lake returned `赛里木湖SHRZ`, dark green (`#377A26`), radius about 30km, level 10, height 1000m; no public DJI red no-fly/blue authorization hit at the sampled lake points. Operational conclusion: **candidate for precheck/reporting, not automatic permission**.

For Sayram Lake, recommend candidate UOM/DJI/local checks for:

- `赛里木湖东门/南门停车区域附近空旷点`;
- `环湖路非人群、非车流、非桥梁临时停车点`;
- avoid 果子沟大桥、高速/车流、游客中心/检票口/人群聚集、border-uncertain directions;
- lake wind/gusts are a hard safety gate.

## Output snippet for live travel

Use a short answer shape:

1. `结论`: can be a candidate / no-fly / unknown until UOM login.
2. `证据`: UOM access boundary + DJI result + local/scenic boundary.
3. `行动`: exact UOM search/report points and screenshots to send back.
4. `硬门`: UOM approved/适飞 + DJI GEO OK + scenic/local OK + weather/crowd OK; otherwise no-fly.
