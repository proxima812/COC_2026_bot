on run
	set projectDir to "__PROJECT_DIR__/"
	set launchScript to quoted form of (projectDir & "scripts/launch_control_app.sh")
	do shell script launchScript & " >/dev/null 2>&1 &"
end run
