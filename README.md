<div align="center">

<img src="./assets/banner.png" alt="Four of Michael's projects side by side. The ha·ggis Hub bothy at sunset, the Wild Haggis Survivors menu, the AccentGuessr globe, and the IdleScape 3D world." width="100%" />

# Michael

**Systems, games, and a wee bit of Scotland.**

I make playable things, and the engines underneath them. Mostly Rust and TypeScript. I keep a soft spot for the parts other folk skip: the deterministic core, the hand-written hash, the sprite drawn in code.

</div>

## 🎮 Live now

<!-- ste-lint: off -->
<table>
  <tr>
    <td width="50%"><a href="https://ha.ggis.xyz"><img src="./assets/hub-bothy.png" alt="The ha·ggis Hub bothy — a Highland cottage interior at sunset with a lit hearth and the wee crowned haggis" /></a></td>
    <td width="50%"><a href="https://ha.ggis.xyz/wild"><img src="./assets/whs-menu.png" alt="Wild Haggis Survivors main menu, its title glowing over a darkening moor" /></a></td>
  </tr>
  <tr>
    <td valign="top">
      <b><a href="https://github.com/Giftedx/ha-ggis-hub">ha·ggis Hub</a></b><br/>
      The lobby. Chap a door and you're in a game. <i>ha + ggis = haggis.</i><br/>
      <sub>Rust + WebAssembly core · hand-rolled Canvas2D renderer · strict TypeScript host</sub><br/>
      <a href="https://ha.ggis.xyz"><b>▶ Play it live</b></a>
    </td>
    <td valign="top">
      <b><a href="https://github.com/Giftedx/wild-haggis-survivors">Wild Haggis Survivors</a></b><br/>
      A Highland-at-dusk bullet heaven. Your haggis has famously uneven legs, so every step drifts a few degrees clockwise.<br/>
      <sub>Phaser 4 + TypeScript · every sprite drawn in code · English &amp; Scots · deterministic replays</sub><br/>
      <a href="https://ha.ggis.xyz/wild"><b>▶ Play it live</b></a>
    </td>
  </tr>
</table>
<!-- ste-lint: on -->

**[Just Five More Minutes](https://github.com/Giftedx/just-five-more-minutes)**: a 2004-flavoured bedroom game. A daft wee MMO runs on the bedroom CRT while your mum asks you, three separate times, to tidy your room. Three.js, generated entirely at runtime. [▶ Play it live](https://ha.ggis.xyz/just-five-more-minutes/)

**[Project-Euler-Clanker](https://github.com/Giftedx/Project-Euler-Clanker)**: 138 maths problems wearing far too much architecture, after an AI got hold of them.

```mermaid
flowchart LR
    subgraph live["Live at ha.ggis.xyz"]
        hub["ha·ggis Hub — the lobby"] -->|door| whs["Wild Haggis Survivors"]
        hub -->|door| jfmm["Just Five More Minutes"]
    end
    subgraph shop["The workshop — private, for now"]
        ag["AccentGuessr"]
        is["IdleScape"]
        pfd["plex-for-discord"]
        kw["Kittiwake"]
    end
    robot["the robot"] -.->|tends| live
    robot -.->|tends| shop
```

## 🔨 In the workshop

Private while they grow, so no links. Nothing here should 404 on you.

| Project | What it is |
| --- | --- |
| **The robot** | It scouts my repos for red CI and rough edges, writes a fix, verifies it, and ships it. A second model reviews anything that smells off. |
| **AccentGuessr** | *GeoGuessr for voices.* Hear a stranger speak, race to pin the accent on the map. Rust→WASM client, a hand-rolled WebGPU globe, zero npm packages. |
| **IdleScape** | Old School RuneScape, but idle — in an actual 3D world instead of a spreadsheet. Go tick engine, React + WebGL client. |
| **plex-for-discord** | Watch Plex together inside Discord, properly in sync. A four-crate Rust workspace with its own Discord Gateway client. |
| **Kittiwake** | A small, honest site for the family's off-grid hut on the Isle of Mull. Astro + Tailwind, and nothing it doesn't need. |

## 🧰 Toolbelt

![Rust](https://img.shields.io/badge/Rust-000000?style=flat&logo=rust&logoColor=white)
![Go](https://img.shields.io/badge/Go-00ADD8?style=flat&logo=go&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![WebAssembly](https://img.shields.io/badge/WebAssembly-654FF0?style=flat&logo=webassembly&logoColor=white)
![Phaser 4](https://img.shields.io/badge/Phaser%204-9070b0?style=flat)
![Astro](https://img.shields.io/badge/Astro-BC52EE?style=flat&logo=astro&logoColor=white)

---

<div align="center"><sub>Everything playable lives at <a href="https://ha.ggis.xyz">ha.ggis.xyz</a>. Mon then.</sub></div>
