# Lark task video-attachment triage

Scope: Global Lark/Feishu task-reading workflows where a task has native video evidence and the user asks to view, analyze, or triage the reported behavior.

Anti-condition: This reference is not a project-specific closeout policy and does not replace any project's final completion gates. It must not store any one task's result, URL, token, attachment URL, branch, or deployment fact.

## Applicability

- Task detail payload has `attachments[]` with a video filename such as `.mp4` or a `video/*` content type.
- The issue depends on temporal UI evidence: PWA install/add-to-home-screen, login/session transitions, navigation loops, stale screen flashes, or similar flows.
- The request is read/analyze/triage, not external writeback.

## Procedure

1. Direct-fetch the task by GUID/applink using the unified reader:
   ```bash
   python3 ~/.hermes/scripts/lark_task_flow.py --url '<lark-task-url>'
   ```
   Record title, comments, tasklists, members, and attachment metadata.

2. Try the rich-comment/native-attachment downloader first:
   ```bash
   python3 ~/.hermes/scripts/lark_rich_comment_image_downloader.py \
     --task-guid <guid> \
     --out-dir ~/.hermes/evidence/lark-rich-comment-images/<guid> \
     --debug --json
   ```

3. If the downloader reports `binary response exceeds max_bytes=8388608` for a video attachment, that is not evidence absence. It only means the image-oriented size cap blocked the video download. Use the task attachment payload's short-lived signed `url` when available, or Drive media fallback when appropriate, and save the video locally under the same evidence directory. Keep the URL/token out of notes.

4. Verify the video before interpreting it:
   ```bash
   ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,avg_frame_rate -of json <video.mp4>
   ```

5. Make contact sheets instead of watching ad hoc:
   ```bash
   ffmpeg -y -i <video.mp4> -vf "fps=1/4,scale=216:-1,tile=5x4" -frames:v 1 <contact_sheet.jpg>
   ```
   For decisive moments, extract narrower critical frames with `-ss <seconds>`.

6. Use vision on the contact sheet(s) and report only what the pixels prove:
   - start state / cleared storage / scanner or source page;
   - login or verification steps reached;
   - exact browser menu or add-to-home-screen action;
   - desktop shortcut/icon creation;
   - first screen after opening the shortcut;
   - whether the flow returns to auth/verification or reaches an authenticated/home page.

7. In the user-facing conclusion, separate task text, comments, video evidence, and classification (`issue_reproduced`, `evidence_incomplete`, or `not_proven`).

## PWA/auth-specific checklist

- Was browser/app storage cleared or was an existing session present?
- Was the user mid-login when installation happened?
- Was the shortcut installed as an app/PWA or merely a browser shortcut? Use visible browser UI, install prompt, shortcut label/icon, and launch container as evidence.
- After tapping the shortcut, did the app show splash only, auth screen, second-factor/PIN screen, or a real authenticated home page?
- If an authenticated page appears before final auth completion, classify it as a session/PWA launch-gate bypass risk, not a cosmetic shortcut issue.

## Pitfalls

- A downloader status like `no_images_found` can coexist with a native video attachment. Check `native_attachments` and `attachments_payload` before saying there is no visual evidence.
- The rich-comment downloader is image-oriented; its default size cap is too small for many videos. The durable lesson is to switch to explicit video download + ffprobe/contact-sheet verification, not to mark the tool broken.
- Do not infer the final state from a single early frame. For login-bypass reports, extract final frames around the shortcut launch and first post-launch route.
