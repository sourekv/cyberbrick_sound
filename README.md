# cyberbrick_sound

Zvukový modul (zvuk motoru) pro Bambu Lab CyberBrick RC. Modul odposlouchává PWM signál plynu ze serva portu přijímače, přehrává zvuk motoru podle plynu přes I2S zesilovač a původní signál nijak neovlivňuje.

## Stav
Fáze 1: prototyp na vývojové desce (Waveshare ESP32-S3-Zero-N8R8-M + MAX98357A + reproduktor 4 Ω). Vlastní PCB až po funkčním prototypu.

## Struktura
- `firmware/` – PlatformIO (Arduino) projekt
- `docs/` – zapojení, naměřené hodnoty, poznámky
- `3d/` – pouzdra, odkazy
- `hardware/` – později KiCad

## Plán firmwaru
1. Testovací tón přes I2S
2. Měření šířky pulzu (50 Hz servo PWM) a výpis na sériovou linku
3. Smyčka motoru s plynulou změnou rychlosti přehrávání podle plynu

## Zvukové vzorky
Viz `firmware/data/samples/LICENSE-SAMPLES.md`.
