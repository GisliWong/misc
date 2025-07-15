Get-ChildItem -Directory | ForEach-Object {
    $folder = $_.FullName
	$folderName = Split-Path $folder -Leaf
    Write-Host "����Ŀ¼: $folder"
    Push-Location $folder

    Get-ChildItem -Filter *.m4s | ForEach-Object {
		$inFile = $_.Name
		$tempFile = "$inFile.tmp"
		java -cp .. BufferedStreamCopy $inFile $tempFile
    }

		$DstFiles = Get-ChildItem -Filter *.m4s.tmp
		Write-Host "�ҵ��� .m4s.tmp �ļ�����" ($DstFiles.Count)

		if ($DstFiles.Count -eq 2) {
		$sorted = $DstFiles | Sort-Object -Property @{Expression={$_.Length}}
        $audio_file = $sorted[0]
        $video_file = $sorted[1]

        $outputFile = Join-Path $folder "$folderName.mkv"
        Write-Host "���ںϲ����: $outputFile"

        & ffmpeg -y -i $video_file -i $audio_file -c copy "$folderName.mkv"

        # ɾ��������ʱ�ļ�
        Get-ChildItem -Filter "*.tmp" | Remove-Item -Force
        Write-Host "��ɾ����ʱ�ļ�"
    }
    else {
        Write-Host "δ�ҵ�ƥ����Ƶ����Ƶ�ļ��������ϲ�"
    }

    Pop-Location
}

Read-Host -Prompt "������ɣ����س��˳�"