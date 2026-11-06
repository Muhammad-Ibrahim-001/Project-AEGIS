
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0

$docPath = 'D:\Semester Projects\DWBI LAB Project\Phase_1_Submission\docx\Phase_1_Project_Execution_Plan.docx'
$pdfPath = 'D:\Semester Projects\DWBI LAB Project\Phase_1_Submission\pdf\Phase_1_Project_Execution_Plan.pdf'

Write-Host "Opening $docPath..."
$doc = $word.Documents.Open($docPath, $false, $true)
Write-Host "Exporting..."
$doc.ExportAsFixedFormat($pdfPath, 17)
Write-Host "Closing..."
$doc.Close(0)
$word.Quit()
Write-Host "File created: $(Test-Path $pdfPath)"
