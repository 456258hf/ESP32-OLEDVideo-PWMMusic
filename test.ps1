$Destination = "G:\"

py.exe .\video2frames.py
py.exe .\frames2videohex.py
Get-ChildItem -Filter "video-*" -File | 
Where-Object { $_.Extension -eq ".hex" } |
ForEach-Object { Copy-Item $_.FullName -Destination $Destination }

ffmpeg.exe -i .\original.mp4 .\audio.wav
Copy-Item .\audio.wav -Destination $Destination
