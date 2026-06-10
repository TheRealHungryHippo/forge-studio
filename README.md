First beta release of Forge Studio.

Includes:
- Python code editor
- Run/stop code
- Output console
- 2D game preview
- 3D viewport preview
- Installer
__________________________________
Source Only Zip was created because
of false antivirus detections, use
the zip if you are scared about the
detections. Otherwise, use the exe.
__________________________________
If you are confused about the zip, dont worry you need to run as .bat, watch tutorials if you are confused. Or use another software to turn the code and raw scripts into an exe.
__________________________________
Forge Studio v1.5

Forge Studio is a desktop Python coding app with a project panel, code editor, syntax highlighting, output console, syntax checker, templates, game preview, and theme modes.

Run it:
1. Double-click Forge Studio.exe
2. Or install it with Forge Studio Installer.exe and choose where it should go.

GitHub download:
For the public beta, upload the source code and the folder/zip build instead of a one-file installer. Unsigned one-file EXEs can trigger antivirus false positives.

Main features:
- Create, open, and save Python files
- Open a project folder and browse files
- Run Python code from inside the app
- Stop running code
- See program output in the built-in console
- Check syntax before running
- Play Forge game scripts inside the Game Preview panel
- Test simple 2D games with keyboard input
- Test simple 3D wireframe games with an editor-style viewport
- Move the 3D viewport with mouse drag, wheel zoom, WASD, and Q/E
- Insert starter templates
- Switch between Forge, Neon, Calm, Focus, and Teach modes
- Uses a custom app icon

Game Preview:
Use the 2D or 3D buttons in the Game Preview panel to load a playable template. Preview scripts can define setup(), update(dt), and draw(). The built-in preview functions include clear(), rect(), circle(), line(), text(), key(), width(), height(), distance(), cube3d(), grid3d(), set_camera(), and move_camera().

3D viewport controls:
- Left-drag rotates the camera
- Right-drag pans the camera
- Mouse wheel zooms
- WASD moves while preview is playing
- Q and E move down/up
- Reset Cam restores the default view

Privacy note:
The installer starts with a blank install location so screenshots do not reveal the builder's Windows username.

Security note:
If antivirus flags a build, do not upload that EXE. Prefer the source code and folder build for public releases until the app is code-signed.

Note:
For the strongest code-running experience, Python should be installed on the computer. If Python is not found, Forge Studio can still try an internal runner for simple scripts, but installed Python is recommended. Larger pygame, Panda3D, Ursina, or other engine projects can still be run with the normal Run button and will usually open their own game window.
