$ContainerName = "kanban-studio"

$existing = docker ps -a --format "{{.Names}}" | Where-Object { $_ -eq $ContainerName }
if ($existing) {
    docker stop $ContainerName
    docker rm $ContainerName
    Write-Host "Kanban Studio stopped."
} else {
    Write-Host "No running container named '$ContainerName' found."
}
