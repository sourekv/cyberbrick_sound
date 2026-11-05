# Speaks the names of the engine_lab sounds with Piper text-to-speech and writes firmware/include/voice_prompts.h.
#
# Voice: en_US-ljspeech-medium (https://huggingface.co/rhasspy/piper-voices, en/en_US/ljspeech/medium), trained on the
# LJ Speech dataset, which its model card lists as public domain. Piper itself:
# https://github.com/rhasspy/piper/releases (piper_windows_amd64.zip, release 2023.11.14-2).
# Download both once, outside the repository, then run from the repository root:
#   pwsh tools/make_voice_prompts.ps1 -Piper <folder with piper.exe> -Model <path to en_US-ljspeech-medium.onnx>
# (the .onnx.json file must lie next to the .onnx file). Without the header the engine_lab firmware beeps instead.
param(
    [Parameter(Mandatory = $true)][string]$Piper,
    [Parameter(Mandatory = $true)][string]$Model
)
$ErrorActionPreference = "Stop"
# Keep in step with SOUND_NAMES in firmware/src/engine_lab/main.cpp
$texts = @("One. Truck.", "Two. Truck with E Q.", "Three. Old synth.", "Four. Diesel.", "Five. Petrol, four cylinder.", "Six. V eight.", "Seven. V twelve.")
$exe = Join-Path $Piper "piper.exe"
$dir = Join-Path ([System.IO.Path]::GetTempPath()) "cyberbrick_voice"
New-Item -ItemType Directory -Force $dir | Out-Null
$files = @()
for ($i = 0; $i -lt $texts.Count; $i++) {
    $f = Join-Path $dir "voice_$($i + 1).wav"
    $texts[$i] | & $exe --model $Model --output_file $f 2>$null
    if (-not (Test-Path $f)) { throw "piper did not write $f" }
    $files += $f
}
python -I tools/make_voice_header.py @files
