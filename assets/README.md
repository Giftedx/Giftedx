# Banner provenance

`banner.png` is a 1600 x 300 pixel composite. It has four 400 x 300 pixel slots. Crop coordinates use source pixels from the top-left corner.

| Slot | Panel | Source capture | Source crop `(x, y, width, height)` | Crop width |
| --- | --- | --- | --- | --- |
| `x=0` | ha·ggis Hub bothy | `hub-bothy.png` (2560 x 1440) | `(560, 160, 1440, 1080)` | 1440 pixels |
| `x=400` | Wild Haggis Survivors menu | `whs-menu.png` (2560 x 1440) | `(632, 20, 1296, 972)` | 1296 pixels |
| `x=800` | AccentGuessr globe | The `x=800, y=0, width=400, height=300` slot in the current `banner.png`. No separate source capture is committed. | `(800, 0, 400, 300)` | 400 pixels |
| `x=1200` | IdleScape 3D world | The `x=1200, y=0, width=400, height=300` slot in the current `banner.png`. No separate source capture is committed. | `(1200, 0, 400, 300)` | 400 pixels |

To rebuild the banner, first copy the AccentGuessr and IdleScape slots from the current banner. Crop each committed source with its source rectangle. Resize each crop to 400 x 300 pixels with bicubic interpolation.

Create a 1600 x 300 pixel canvas. Place the panels at `x=0`, `x=400`, `x=800`, and `x=1200` in the table order.
