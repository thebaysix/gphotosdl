# PowerShell script to test Google Photos API with token

# Read token from token.pickle
$pythonCode = @"
import pickle
import os
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as f:
        saved = pickle.load(f)
        print(saved.get('token'))
"@

$token = python -c $pythonCode

if ($token) {
    Write-Host "Testing API with token..." -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "https://photoslibrary.googleapis.com/v1/mediaItems?pageSize=1" -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"}
        Write-Host "SUCCESS! API is accessible" -ForegroundColor Green
        Write-Host $response.Content
    } catch {
        Write-Host "FAILED!" -ForegroundColor Red
        Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
        Write-Host "Error: $($_.Exception.Message)"
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response Body: $responseBody"
        }
    }
} else {
    Write-Host "Could not read token from token.pickle" -ForegroundColor Red
}
