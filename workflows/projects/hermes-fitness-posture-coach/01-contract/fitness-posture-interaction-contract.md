# Fitness Posture Interaction Contract

## Shared interaction output

```json
{
  "mode": "fitness_posture",
  "intent": "inspect_form|select_exercise|camera_setup|post_set_summary",
  "exercise_id": "string|null",
  "exercise_name": "string|null",
  "phase": "setup|eccentric|bottom|concentric|hold|unknown",
  "speak_text": "短促中文提示",
  "subtitle": "同 speak_text 或更完整解释",
  "camera_instruction": "fixed_full_body_side_view|front_view|move_back|improve_lighting|null",
  "confidence": 0.0,
  "risk_level": "low|medium|high|stop",
  "should_interrupt": false,
  "requires_confirmation": false,
  "overlay": [
    {"type": "skeleton|joint_highlight|angle|arrow|rep_count|warning", "target": "right_knee", "value": null}
  ],
  "evidence_refs": ["frame:f1", "pose:p1", "exercise_seed:0001"],
  "next_action": "continue|adjust_camera|stop|ask_user"
}
```

## Input evidence contract

- `exercise_seed` may come from the normalized metadata index.
- `frame` must be explicit local frame/clip evidence.
- `pose` must come from a named adapter receipt; text/VLM guesses cannot fill keypoints.
- Missing critical joints => camera instruction, not posture judgment.

## Initial low-risk moves

Start with bodyweight squat, push-up, plank, and lunge. Avoid loaded barbell analysis until the safety gate and multi-frame phase segmentation are validated.

## Safety gate

Stop / ask confirmation when:
- user reports pain, numbness, dizziness;
- heavy load is visible or declared;
- full body / critical joints are missing;
- pose confidence is low;
- model output tries to diagnose injury or prescribe treatment.
