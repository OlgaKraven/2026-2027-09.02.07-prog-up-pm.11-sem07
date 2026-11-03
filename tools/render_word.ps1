param([Parameter(Mandatory=$true)][string]$InputFile,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference='Stop'
$inputPath=(Resolve-Path -LiteralPath $InputFile).Path
$pdfPath=[IO.Path]::GetFullPath($OutputPdf)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($pdfPath)) | Out-Null
$word=New-Object -ComObject Word.Application
$word.Visible=$false
$word.DisplayAlerts=0
$document=$null
try {
 $document=$word.Documents.Open($inputPath,$false,$false)
 $document.Repaginate()
 foreach($toc in $document.TablesOfContents){$toc.Update()}
 $document.Fields.Update() | Out-Null
 $document.Repaginate()
 foreach($toc in $document.TablesOfContents){$toc.UpdatePageNumbers()}
 $document.Save()
 $document.ExportAsFixedFormat($pdfPath,17)
 Write-Output $pdfPath
} finally {
 if($null -ne $document){$document.Close($false);[Runtime.InteropServices.Marshal]::ReleaseComObject($document)|Out-Null}
 $word.Quit()
 [Runtime.InteropServices.Marshal]::ReleaseComObject($word)|Out-Null
}
