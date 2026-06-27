// evil.go
package main

import "os/exec"

func main() {
    exec.Command("calc.exe").Run()
}