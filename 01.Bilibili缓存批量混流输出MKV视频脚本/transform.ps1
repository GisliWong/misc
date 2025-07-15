Get-ChildItem -Directory | ForEach-Object {
    $folder = $_.FullName
	$folderName = Split-Path $folder -Leaf
    Write-Host "处理目录: $folder"
    Push-Location $folder

    Get-ChildItem -Filter *.m4s | ForEach-Object {
		$inFile = $_.Name
		$tempFile = "$inFile.tmp"
		java -cp .. BufferedStreamCopy $inFile $tempFile
    }

		$DstFiles = Get-ChildItem -Filter *.m4s.tmp
		Write-Host "找到的 .m4s.tmp 文件数：" ($DstFiles.Count)

		if ($DstFiles.Count -eq 2) {
		$sorted = $DstFiles | Sort-Object -Property @{Expression={$_.Length}}
        $audio_file = $sorted[0]
        $video_file = $sorted[1]

        $outputFile = Join-Path $folder "$folderName.mkv"
        Write-Host "正在合并输出: $outputFile"

        & ffmpeg -y -i $video_file -i $audio_file -c copy "$folderName.mkv"

        # 删除所有临时文件
        Get-ChildItem -Filter "*.tmp" | Remove-Item -Force
        Write-Host "已删除临时文件"
    }
    else {
        Write-Host "未找到匹配音频或视频文件，跳过合并"
    }

    Pop-Location
}

Read-Host -Prompt "处理完成，按回车退出"