$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$ContainerName = "kanban-studio"
$ImageName = "kanban-studio"
$Port = 8000

# Stop and remove any existing container with this name
$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }
if ($existing) {
    Write-Host "Removing existing container..."
    docker stop $ContainerName 2>$null
    docker rm $ContainerName
}

Write-Host "Building image..."
docker build -t $ImageName $ProjectDir

Write-Host "Starting container..."
docker run -d --name $ContainerName -p "${Port}:8000" --env-file "$ProjectDir\.env" $ImageName

Write-Host "Kanban Studio running at http://localhost:$Port"
