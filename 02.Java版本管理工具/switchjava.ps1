param (
    [Alias("l")]
    [switch]$List,

    [Alias("c")]
    [string]$ChangeVer,

    [Alias("a")]
    [string]$JavaPath,

    [Alias("d")]
    [string]$DeleteVer,

    [Alias("h")]
    [switch]$Help
)

function Write-Log {
    param (
        [string]$Type,
        [string]$Msg
    )
    switch ($Type.ToUpper()) {
        "OK"   { Write-Host "[OK]  $Msg" -ForegroundColor Green }
        "INFO" { Write-Host "[INFO] $Msg" -ForegroundColor Cyan }
        "WARN" { Write-Host "[WARN] $Msg" -ForegroundColor Yellow }
        "ERR"  { Write-Host "[ERR]  $Msg" -ForegroundColor Red }
        default { Write-Host "[LOG]  $Msg" }
    }
}

function Show-Help {
@"
Java 多版本管理工具

参数说明：
  -l                    列出可用 JAVA 版本
  -c <version>          切换 JAVA_HOME 到 JAVAx_HOME
  -a <path>             添加新的 Java 路径（支持带 bin）
  -d <version>          删除 JAVA${v}_HOME，并从 PATH 移除
  -h                    显示帮助信息

示例：
  .\switch-java.ps1 -c 17
  .\switch-java.ps1 -a "D:\Java\jdk1.8.0_301\bin"
  .\switch-java.ps1 -d 8
"@
}

function Show-List {
    $sysEnvVars = [Environment]::GetEnvironmentVariables("Machine")

    Write-Host "`n默认 JAVA_HOME："
    $defaultJava = $sysEnvVars["JAVA_HOME"]
    if ($defaultJava) {
        Write-Host ("{0,-20} {1}" -f "JAVA_HOME", $defaultJava)
    } else {
        Write-Log "WARN" "未设置 JAVA_HOME"
    }
    Write-Host ""

    Write-Host "可用版本 JAVA*_HOME 环境变量："
    Write-Host ("{0,-20} {1,-20} {2}" -f "Version", "VarName", "VarValue")
    $found = $false
    foreach ($varName in $sysEnvVars.Keys) {
        if ($varName -match "^JAVA(\d+)_HOME$") {
            $varId = $matches[1]
            $varValue = $sysEnvVars[$varName]
            Write-Host ("{0,-20} {1,-20} {2}" -f $varId, $varName, $varValue)
            $found = $true
        }
    }
    if (-not $found) {
        Write-Log "WARN" "未发现任何特定版本环境变量"
    }
    Write-Host ""
}

function AddToPath {
    param ([string]$NewOne)

    $sysPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $pathList = $sysPath -split ';'
    $newPathVar = "%$NewOne%\bin"

    if ($pathList -notcontains $newPathVar) {
        $pathList += $newPathVar
        $newSysPath = ($pathList -join ';').Trim(';')
        [Environment]::SetEnvironmentVariable("Path", $newSysPath, "Machine")
        Write-Log "OK" "添加 $newPathVar 到 PATH 成功"
    } else {
        Write-Log "INFO" "PATH 已有 $newPathVar，无需重复添加"
    }
}

function Add-NewJava {
    param (
        [string]$JavaPath
    )

    if ($JavaPath -match "\\bin\\?$") {
        $JavaPath = Split-Path $JavaPath -Parent
        Write-Log "INFO" "检测到 bin 目录，已修正为：$JavaPath"
    }

    $javaExe = Join-Path $JavaPath "bin\java.exe"
    if (-not (Test-Path $javaExe)) {
        Write-Log "ERR" "找不到 java.exe：$javaExe"
        return
    }

    $verLine = (& $javaExe -version 2>&1)[0]
    Write-Host "版本检测输出: $verLine"
    if ($verLine -match "java version `"([0-9._]+)`"") {
        $ver = $matches[1]

        if ($ver -match '^1\.(\d+)') {
            $safever = $matches[1]
        } elseif ($ver -match '^(\d+)') {
            $safever = $matches[1]
        } else {
            Write-Log "ERR" "无法识别主版本号：$ver"
            return
        }

        $varName = "JAVA${safever}_HOME"
        [Environment]::SetEnvironmentVariable($varName, $JavaPath, "Machine")
        Write-Log "OK" "已设置环境变量 $varName = $JavaPath"

        $targetExe = Join-Path $JavaPath "bin\java${safever}.exe"
        if (-not (Test-Path $targetExe)) {
            Copy-Item $javaExe $targetExe
            Write-Log "INFO" "创建版本专用文件 java${safever}.exe"
        }

        AddToPath $varName
    } else {
        Write-Log "ERR" "无法解析 Java 版本，请检查输出格式："
        Write-Host $verLine -ForegroundColor DarkRed
    }
}

function ChangeToJava {
    param ([string]$ChangeVer)

    if ($ChangeVer -notmatch '^\d+$') {
        Write-Log "ERR" "版本号格式无效：$ChangeVer（只能包含数字）"
        return
    }

    $DstVarName = "JAVA${ChangeVer}_HOME"
    $DstVarValue = [Environment]::GetEnvironmentVariable($DstVarName, "Machine")
    if (-not $DstVarValue) {
        Write-Log "ERR" "$DstVarName 不存在，无法切换，请先添加或查看 -l"
        return
    }

    [Environment]::SetEnvironmentVariable("JAVA_HOME", $DstVarValue, "Machine")
    $env:JAVA_HOME = $DstVarValue

    $javaBin = Join-Path $DstVarValue "bin"
    $env:Path = "$javaBin;" + (($env:Path -split ';') | Where-Object { $_ -notmatch "java" }) -join ';'

    Write-Log "OK" "JAVA_HOME 已切换为 $DstVarValue（当前终端已生效）"
}

function DeleteJavaFromEnv {
    param (
        [string]$DeleteVer
    )

    if ($DeleteVer -notmatch '^\d+$') {
        Write-Log "ERR" "版本号格式无效：$DeleteVer（只能包含数字）"
        return
    }

    $varName = "JAVA${DeleteVer}_HOME"
    $varValue = [Environment]::GetEnvironmentVariable($varName, "Machine")

    if (-not $varValue) {
        Write-Log "INFO" "$varName 不存在，无需删除。"
        return
    }

    # 删除环境变量
    [Environment]::SetEnvironmentVariable($varName, $null, "Machine")
    Write-Log "OK" "$varName 已删除"

    # 从 PATH 中移除对应变量路径
    $sysPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $pathList = $sysPath -split ';'
    $targetPath = "%$varName%\bin"

    $newPathList = $pathList | Where-Object { $_ -ne $targetPath }

    if ($pathList.Count -ne $newPathList.Count) {
        $newPath = ($newPathList -join ';').Trim(';')
        [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
        Write-Log "OK" "已从 PATH 中移除 $targetPath"
    } else {
        Write-Log "INFO" "PATH 中未发现 $targetPath，无需处理"
    }
}


# 入口逻辑
echo ""

if ($Help) {
    Show-Help
    exit
}

if ($List) {
    Show-List
    exit
}

# 如果不是管理员，则重新以管理员权限重新运行该脚本
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Write-Log "ERR" "需要升级权限，以管理员权限重新运行。 "
    Pause
	exit
}

if ($JavaPath) {
    Add-NewJava $JavaPath
    exit
}

if ($ChangeVer) {
    ChangeToJava $ChangeVer
    exit
}

if ($DeleteVer) {
    DeleteJavaFromEnv $DeleteVer
    exit
}

if (-not ($List -or $ChangeVer -or $JavaPath -or $DeleteVer -or $Help)) {
    Write-Log "INFO" "请使用 -h 查看帮助信息"
    Show-Help
    exit
}
