package main
import "syscall"
func main() { syscall.Exec("/bin/sh", []string{"sh", "-c", "echo malicious"}, nil) }