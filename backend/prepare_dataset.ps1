# PowerShell 脚本：准备数据集
$datasetId = "ds_20260115_212121"

Write-Host "正在准备数据集 $datasetId ..." -ForegroundColor Yellow

$body = @{
    split_ratio = @{
        train = 0.8
        val = 0.2
    }
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/datasets/$datasetId/prepare" -Method Post -Body $body -ContentType "application/json"

Write-Host "准备完成！" -ForegroundColor Green
$response | ConvertTo-Json -Depth 3