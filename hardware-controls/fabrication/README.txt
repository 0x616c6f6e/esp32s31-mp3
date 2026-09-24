Q2 Controls B - PROTOTYPE ONLY
Finished size: 44 x 34 mm, R10; 2 copper layers; finished thickness 0.8 mm.
FR-4, 1 oz copper nominal. Apply insulating solder mask to both faces.
The three front touch electrodes MUST remain covered by solder mask.
No copper planes or conductive cover coating may be added over the touch area.
Suggested finish: ENIG. Confirm 0.15 mm trace/space capability with the fabricator.
Vias: 0.30 mm drill, 0.50 / 0.60 mm copper; tent both sides where mask permits.
controls-PTH.drl contains plated via drills.
controls-NPTH.drl contains four non-plated 1.80 mm mounting holes.
Do not combine or plate the mounting holes.
No impedance-control requirement. Confirm finished board thickness tolerance.
F.Paste/B.Paste are stencil data; they are not additional copper layers.
FFC mechanical alignment to hardware-q2-layout has been designed; physical mating not yet validated.
U1 AT42QT2120 (I2C 0x1C) and U2 TCA6408A (I2C 0x20) share SDA/SCL/INT.
J1 pin 3 = SDA, pin 4 = SCL (updated pin assignment).
Four keys are read by U2; POWER is independent on J1 pin 11, with R14 10k pull-up to +3V3.
POWER is high when released (board powered), low when pressed.
J1 pins 7-10 are NC. Do not use the old revision-A key wiring or Gerbers.
Assembly placement CSV and BOM are outside this Gerber archive, in output/.
Verify FPC pin 1 and IC orientation against the manufacturer drawings before assembly.
Check touch tracking, sensitivity, power consumption, mechanical key travel and
clearance with the selected battery and final nonconductive keycaps on prototypes.

J1 = HCTL HC-FPC-05-10-12RLTAG, bottom contact, 12P, 0.5 mm pitch.
Use 0.30 +/-0.03 mm cable terminals; do NOT use the old Hirose 0.2 mm cable.
J1 pins 13/14 are grounded shield tabs. Suggested FFC: 40 mm, type B opposite faces,
6.5 mm width, exposed fingers >=3 mm, reinforcement >=4 mm. Verify samples.
Rear-cover inner relief is required; old mainboard posts do not match new holes.
