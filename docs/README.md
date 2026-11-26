# Documentation

Where to start, by what you want to do. Every document is in English; the files and folders of the whole repository are mapped in
[`contents.md`](contents.md). The documentation is licensed under [CC BY-SA 4.0](LICENSE).

## I want to build it

| Document | What you find there |
|---|---|
| [Getting started from scratch](getting-started.md) | **start here**: the whole way from the parts to the engine sound in the truck |
| [Soldering the shield and the printed stand](soldering.md) | J1, J3 and J4, both ways of fitting the servo header, the solder stand, pictures |
| [First install by cable](first-install.md) | the firmware and the default sound sets on a new module |
| [The shield board, rev A](shield-pcb.md) | the board that exists: schematic, parts to buy, ordering, connectors, first power-up |

## I want to drive it and change the sounds

| Document | What you find there |
|---|---|
| [User guide of the web app](user-guide.md) | the app at https://sourekv.github.io/cyberbrick_sound/: test, copy, edit and write sound sets, with pictures |
| [Controls](controls.md) | what each control of the transmitter does, all sound effects, power-up order |
| [CyberBrick app configurations](cyberbrick-config/README.md) | the configuration to import into the app |
| [Receiver programs](cyberbrick-code/README.md) | the MicroPython snippets that run on the receiver |
| [Bluetooth link](ble-link.md) | the Bluetooth link: PIN, module name, firmware update |

## I want to understand or extend it

| Document | What you find there |
|---|---|
| [Project overview](project-overview.md) | the whole project on one page |
| [Sound sets, the format and the USB protocol](user-sounds.md) | what a set contains, what a sample must meet, the protocol of the app |
| [Layered sound sets](layers-design.md) | the design of the loops recorded at several engine speeds |
| [Engine start, stop and horn](start-stop-horn.md) | the current design and the earlier notes |
| [Engine sound research](sound-research.md) | the constraints of a small speaker, approaches tried, lessons |
| [Bring-up of the prototype](bringup.md) | history of the breadboard prototype: wiring, measurements on the receiver, test order, the USB power rule; not needed with the shield board |
| [Rendered audio previews](audio-simulation/README.md) | the engine sounds as files |
| [Speaker measurements](speaker-measurement.md) | how the speaker was measured, results, 4 and 8 Ohm, the gain jumper |

## Plans, decisions and prices

| Document | What you find there |
|---|---|
| [Roadmap](roadmap.md) | everything that is still open |
| [Rejected ideas](rejected-ideas.md) | what was considered and dropped, and why |
| [First install from the web page](web-install-design.md) | design, not built: flashing a new module from the browser |
| [Next revisions of the board](shield-pcb-rev-b.md) | rev B (prepared, not ordered) and ideas; future state, may be out of date |
| [Price comparison of assembled boards](shield-cost-comparison.md) | PCBWay and JLCPCB |
| [Ideal against ordered parts](shield-bom-compare.md) | the differences between the full and the ordered bill of materials |
