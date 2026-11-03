param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$inputPath=(Resolve-Path -LiteralPath $InputFile).Path
$outPath=[IO.Path]::GetFullPath($OutputDirectory)
[IO.Directory]::CreateDirectory($outPath)|Out-Null
$app=New-Object -ComObject PowerPoint.Application
$presentation=$null
try {
 $presentation=$app.Presentations.Open($inputPath,$true,$false,$false)
 $presentation.Export($outPath,'PNG',1600,900)
 Write-Output ('Exported '+$presentation.Slides.Count+' slides')
} finally {
 if($null -ne $presentation){$presentation.Close();[Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)|Out-Null}
 $app.Quit();[Runtime.InteropServices.Marshal]::ReleaseComObject($app)|Out-Null
}
