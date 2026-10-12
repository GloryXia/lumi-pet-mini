# Lumi look mechanics

Lumi is a small humanoid pet with a separate head, dark blue bob, teal eyes, and a star clip on her own left side. Her shoes and lower torso stay registered in every direction. Her eyes lead, then the head turns or pitches slightly; the shoulders and hair follow by a smaller amount. The clip remains attached to the hair and changes visibility naturally with the head turn. The dress, hands, and feet preserve their proportions.

- **000 up:** chin lifts a little, eyes look above the viewer, upper lids open, front of the neck becomes more visible. Still clearly distinct from neutral.
- **090 screen-right:** pupils and nose point to image right; face turns about three quarters right, making the far cheek narrower. Hair and clip follow the turn, while the feet remain in place.
- **180 down:** chin dips, eyes point below the viewer, upper lids lower, hair falls slightly forward.
- **270 screen-left:** pupils and nose point to image left; face turns about three quarters left, making the opposite cheek narrower. The star clip remains on Lumi's own left side and may be partially occluded.

Diagonal directions interpolate evenly between adjacent cardinals in 22.5-degree steps. No whole-sprite rotation, stretch, or tilt. At each step, eye placement changes first, with modest head and hair follow-through. Keep the feet, body size, dress, and baseline fixed. Do not add a background, frame, shadow, aura, particles, or labels.
