param([string]$FfmpegPath = 'ffmpeg')
$ErrorActionPreference = 'Stop'
$nativeAudioRuntime = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../assets/audio'))
foreach ($nativeAudioCue in @('battle-rich','boss-dark','campus-air','quiet-birds','umc-room','hall-clock')) {
    & $FfmpegPath -v error -y -i (Join-Path $PSScriptRoot "masters/$nativeAudioCue.wav") -c:a libvorbis -q:a 5 (Join-Path $nativeAudioRuntime "$nativeAudioCue.ogg")
    if ($LASTEXITCODE -ne 0) { throw "Encoding failed: $nativeAudioCue" }
    & $FfmpegPath -v error -y -i (Join-Path $nativeAudioRuntime "$nativeAudioCue.ogg") -f s16le -ac 1 -ar 48000 (Join-Path $PSScriptRoot "$nativeAudioCue-check.pcm")
    if ($LASTEXITCODE -ne 0) { throw "Decoding failed: $nativeAudioCue" }
}
node (Join-Path $PSScriptRoot 'verify-native.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Native audio verification failed' }
foreach ($nativeAudioCue in @('battle-rich','boss-dark','campus-air','quiet-birds','umc-room','hall-clock')) {
    Remove-Item -LiteralPath (Join-Path $PSScriptRoot "$nativeAudioCue-check.pcm")
}
