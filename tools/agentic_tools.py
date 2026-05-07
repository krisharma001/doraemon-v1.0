"""
tools/agentic_tools.py — Full system/computer-use agentic tools.
Lets Doraemon autonomously control your Mac on your behalf.
"""
import os
import subprocess
import logging
import asyncio
import pyautogui
import pyperclip
from datetime import datetime
from typing import Optional
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("AgenticTools")

# Safety: always confirm before destructive actions (set to False to skip prompts)
REQUIRE_CONFIRM = False


# ─────────────────────────────────────────────
#  KEYBOARD & MOUSE CONTROL
# ─────────────────────────────────────────────

@function_tool()
async def type_text(context: RunContext, text: str) -> str:  # type: ignore
    """
    Type any text as if using the keyboard. 
    Useful for filling forms, writing emails, entering data.
    """
    try:
        await asyncio.sleep(0.3)
        pyautogui.typewrite(text, interval=0.04)
        logger.info(f"Typed: {text[:50]}")
        return f"Typed the text, Sir."
    except Exception as e:
        return f"Typing failed: {e}"


@function_tool()
async def press_key(context: RunContext, key: str) -> str:  # type: ignore
    """
    Press a keyboard key or shortcut.
    Examples: 'enter', 'escape', 'tab', 'command+c', 'command+v', 
              'command+space', 'command+tab', 'delete', 'f5'
    """
    try:
        keys = key.lower().split("+")
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        logger.info(f"Pressed key: {key}")
        return f"Key pressed: {key}, Sir."
    except Exception as e:
        return f"Key press failed: {e}"


@function_tool()
async def click_at(context: RunContext, x: int, y: int, button: str = "left") -> str:  # type: ignore
    """
    Click the mouse at screen coordinates (x, y).
    button can be 'left', 'right', or 'middle'.
    """
    try:
        pyautogui.click(x, y, button=button)
        logger.info(f"Clicked at ({x}, {y}) with {button} button")
        return f"Clicked at position ({x}, {y}), Sir."
    except Exception as e:
        return f"Click failed: {e}"


@function_tool()
async def move_mouse(context: RunContext, x: int, y: int) -> str:  # type: ignore
    """Move the mouse cursor to screen coordinates (x, y)."""
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        return f"Mouse moved to ({x}, {y}), Sir."
    except Exception as e:
        return f"Mouse move failed: {e}"


@function_tool()
async def scroll(context: RunContext, direction: str, amount: int = 3) -> str:  # type: ignore
    """
    Scroll the page. direction: 'up' or 'down'. amount: number of scrolls.
    """
    try:
        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)
        return f"Scrolled {direction} {amount} times, Sir."
    except Exception as e:
        return f"Scroll failed: {e}"


@function_tool()
async def get_screen_size(context: RunContext) -> str:  # type: ignore
    """Get the current screen resolution."""
    try:
        size = pyautogui.size()
        return f"Screen resolution: {size.width}x{size.height}, Sir."
    except Exception as e:
        return f"Failed to get screen size: {e}"


# ─────────────────────────────────────────────
#  CLIPBOARD OPERATIONS
# ─────────────────────────────────────────────

@function_tool()
async def copy_to_clipboard(context: RunContext, text: str) -> str:  # type: ignore
    """Copy text to the system clipboard."""
    try:
        pyperclip.copy(text)
        return f"Copied to clipboard, Sir."
    except Exception as e:
        return f"Clipboard copy failed: {e}"


@function_tool()
async def paste_from_clipboard(context: RunContext) -> str:  # type: ignore
    """Read and return the current clipboard content."""
    try:
        content = pyperclip.paste()
        return f"Clipboard contains: {content}"
    except Exception as e:
        return f"Clipboard read failed: {e}"


@function_tool()
async def paste_at_cursor(context: RunContext) -> str:  # type: ignore
    """Paste clipboard content at the current cursor position (Cmd+V on Mac)."""
    try:
        pyautogui.hotkey("command", "v")
        return f"Pasted clipboard content, Sir."
    except Exception as e:
        return f"Paste failed: {e}"


# ─────────────────────────────────────────────
#  APP & WINDOW MANAGEMENT
# ─────────────────────────────────────────────

@function_tool()
async def launch_app(context: RunContext, app_name: str) -> str:  # type: ignore
    """
    Launch any installed Mac application by name.
    Examples: 'Safari', 'Finder', 'Terminal', 'Spotify', 'VS Code', 
              'Slack', 'Zoom', 'Chrome', 'Notes', 'Calendar'
    """
    try:
        subprocess.Popen(["open", "-a", app_name])
        await asyncio.sleep(1.5)
        logger.info(f"Launched app: {app_name}")
        return f"Launching {app_name}, Sir."
    except Exception as e:
        return f"Failed to launch {app_name}: {e}"


@function_tool()
async def quit_app(context: RunContext, app_name: str) -> str:  # type: ignore
    """Quit a running application by name."""
    try:
        script = f'tell application "{app_name}" to quit'
        subprocess.run(["osascript", "-e", script])
        return f"Quit {app_name}, Sir."
    except Exception as e:
        return f"Failed to quit {app_name}: {e}"


@function_tool()
async def switch_to_app(context: RunContext, app_name: str) -> str:  # type: ignore
    """Bring an application to the foreground / switch focus to it."""
    try:
        script = f'tell application "{app_name}" to activate'
        subprocess.run(["osascript", "-e", script])
        return f"Switched to {app_name}, Sir."
    except Exception as e:
        return f"Failed to switch to {app_name}: {e}"


@function_tool()
async def get_running_apps(context: RunContext) -> str:  # type: ignore
    """Get a list of currently running applications."""
    try:
        script = 'tell application "System Events" to get name of every process whose background only is false'
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        apps = result.stdout.strip()
        return f"Running apps, Sir: {apps}"
    except Exception as e:
        return f"Failed to get running apps: {e}"


@function_tool()
async def minimize_window(context: RunContext) -> str:  # type: ignore
    """Minimize the current active window."""
    try:
        pyautogui.hotkey("command", "m")
        return "Window minimized, Sir."
    except Exception as e:
        return f"Minimize failed: {e}"


@function_tool()
async def close_window(context: RunContext) -> str:  # type: ignore
    """Close the current active window."""
    try:
        pyautogui.hotkey("command", "w")
        return "Window closed, Sir."
    except Exception as e:
        return f"Close failed: {e}"


# ─────────────────────────────────────────────
#  TERMINAL / SHELL COMMANDS
# ─────────────────────────────────────────────

@function_tool()
async def run_shell_command(context: RunContext, command: str) -> str:  # type: ignore
    """
    Run a shell command on the Mac and return output.
    Use for: listing files, checking git status, running scripts,
    installing packages, pinging servers, etc.
    Example commands: 'ls -la', 'git status', 'pip install requests',
                      'cat file.txt', 'echo hello', 'pwd'
    """
    try:
        logger.info(f"Running shell command: {command}")
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip() or result.stderr.strip() or "(no output)"
        return f"Command output:\n{output}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds, Sir."
    except Exception as e:
        return f"Shell command failed: {e}"


@function_tool()
async def open_terminal_and_run(context: RunContext, command: str) -> str:  # type: ignore
    """
    Open Terminal app and run a command visibly (so you can see it).
    Good for long-running tasks you want to monitor.
    """
    try:
        script = f'''
        tell application "Terminal"
            activate
            do script "{command}"
        end tell
        '''
        subprocess.Popen(["osascript", "-e", script])
        return f"Running '{command}' in Terminal, Sir."
    except Exception as e:
        return f"Failed to open Terminal: {e}"


# ─────────────────────────────────────────────
#  BROWSER CONTROL
# ─────────────────────────────────────────────

@function_tool()
async def browser_open_url(context: RunContext, url: str, browser: str = "Google Chrome") -> str:  # type: ignore
    """
    Open a URL in a specific browser.
    browser options: 'Google Chrome', 'Safari', 'Firefox'
    """
    try:
        if not url.startswith("http"):
            url = "https://" + url
        script = f'tell application "{browser}" to open location "{url}"'
        subprocess.run(["osascript", "-e", script])
        return f"Opened {url} in {browser}, Sir."
    except Exception as e:
        return f"Failed to open URL: {e}"


@function_tool()
async def browser_new_tab(context: RunContext, browser: str = "Google Chrome") -> str:  # type: ignore
    """Open a new tab in Chrome or Safari."""
    try:
        pyautogui.hotkey("command", "t")
        return f"New tab opened, Sir."
    except Exception as e:
        return f"Failed to open new tab: {e}"


@function_tool()
async def browser_go_back(context: RunContext) -> str:  # type: ignore
    """Go back in browser history."""
    try:
        pyautogui.hotkey("command", "left")
        return "Went back, Sir."
    except Exception as e:
        return f"Failed: {e}"


@function_tool()
async def browser_refresh(context: RunContext) -> str:  # type: ignore
    """Refresh the current browser tab."""
    try:
        pyautogui.hotkey("command", "r")
        return "Page refreshed, Sir."
    except Exception as e:
        return f"Refresh failed: {e}"


@function_tool()
async def search_in_browser(context: RunContext, query: str, browser: str = "Google Chrome") -> str:  # type: ignore
    """
    Open a browser and search Google for a query.
    """
    try:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded}"
        script = f'tell application "{browser}" to open location "{url}"'
        subprocess.run(["osascript", "-e", script])
        return f"Searching Google for '{query}', Sir."
    except Exception as e:
        return f"Search failed: {e}"


# ─────────────────────────────────────────────
#  FILE SYSTEM OPERATIONS
# ─────────────────────────────────────────────

@function_tool()
async def create_folder(context: RunContext, path: str) -> str:  # type: ignore
    """Create a folder at the given path."""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Folder created at {path}, Sir."
    except Exception as e:
        return f"Folder creation failed: {e}"


@function_tool()
async def delete_file(context: RunContext, path: str) -> str:  # type: ignore
    """
    Move a file to Trash (safe delete). Does NOT permanently delete.
    """
    try:
        subprocess.run(["osascript", "-e", f'tell application "Finder" to delete POSIX file "{path}"'])
        return f"Moved {path} to Trash, Sir."
    except Exception as e:
        return f"Delete failed: {e}"


@function_tool()
async def rename_file(context: RunContext, old_path: str, new_name: str) -> str:  # type: ignore
    """Rename a file. new_name is just the filename, not full path."""
    try:
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)
        os.rename(old_path, new_path)
        return f"Renamed to {new_name}, Sir."
    except Exception as e:
        return f"Rename failed: {e}"


@function_tool()
async def open_in_finder(context: RunContext, path: str = "~") -> str:  # type: ignore
    """Open a folder or file location in Finder."""
    try:
        subprocess.Popen(["open", os.path.expanduser(path)])
        return f"Opened {path} in Finder, Sir."
    except Exception as e:
        return f"Failed to open Finder: {e}"


# ─────────────────────────────────────────────
#  SYSTEM CONTROLS
# ─────────────────────────────────────────────

@function_tool()
async def set_system_volume(context: RunContext, level: int) -> str:  # type: ignore
    """Set Mac system volume. level is 0-100."""
    try:
        # Mac volume is 0-10 in AppleScript
        mac_level = int(level / 10)
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
        return f"Volume set to {level}%, Sir."
    except Exception as e:
        return f"Volume control failed: {e}"


@function_tool()
async def mute_system(context: RunContext) -> str:  # type: ignore
    """Mute the system volume."""
    try:
        subprocess.run(["osascript", "-e", "set volume with output muted"])
        return "System muted, Sir. Running silent."
    except Exception as e:
        return f"Mute failed: {e}"


@function_tool()
async def unmute_system(context: RunContext) -> str:  # type: ignore
    """Unmute the system volume."""
    try:
        subprocess.run(["osascript", "-e", "set volume without output muted"])
        return "System unmuted, Sir."
    except Exception as e:
        return f"Unmute failed: {e}"


@function_tool()
async def lock_screen(context: RunContext) -> str:  # type: ignore
    """Lock the Mac screen."""
    try:
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "q" using {command down, control down}'])
        return "Screen locked, Sir. Keeping things secure."
    except Exception as e:
        return f"Lock screen failed: {e}"


@function_tool()
async def empty_trash(context: RunContext) -> str:  # type: ignore
    """Empty the Mac Trash."""
    try:
        subprocess.run(["osascript", "-e", 'tell application "Finder" to empty trash'])
        return "Trash emptied, Sir."
    except Exception as e:
        return f"Empty trash failed: {e}"


@function_tool()
async def show_notification(context: RunContext, title: str, message: str) -> str:  # type: ignore
    """
    Show a macOS system notification banner.
    Useful for alerts, reminders, or status updates.
    """
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script])
        return f"Notification sent, Sir."
    except Exception as e:
        return f"Notification failed: {e}"


@function_tool()
async def speak_text(context: RunContext, text: str) -> str:  # type: ignore
    """
    Use macOS text-to-speech to say something out loud via system voice.
    Separate from Doraemon's voice — uses the Mac's built-in TTS.
    """
    try:
        subprocess.Popen(["say", text])
        return f"Speaking via system TTS, Sir."
    except Exception as e:
        return f"TTS failed: {e}"


@function_tool()
async def take_screenshot_and_describe(context: RunContext) -> str:  # type: ignore
    """
    Take a screenshot and save it with a timestamp to the Desktop.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/Desktop/doraemon_screenshot_{timestamp}.png")
        pyautogui.screenshot(path)
        return f"Screenshot saved to Desktop as doraemon_screenshot_{timestamp}.png, Sir."
    except Exception as e:
        return f"Screenshot failed: {e}"


# ─────────────────────────────────────────────
#  SPOTLIGHT & QUICK SEARCH
# ─────────────────────────────────────────────

@function_tool()
async def spotlight_search(context: RunContext, query: str) -> str:  # type: ignore
    """
    Open Spotlight and search for anything — apps, files, contacts, etc.
    """
    try:
        pyautogui.hotkey("command", "space")
        await asyncio.sleep(0.5)
        pyautogui.typewrite(query, interval=0.05)
        return f"Spotlight opened and searching for '{query}', Sir."
    except Exception as e:
        return f"Spotlight search failed: {e}"


@function_tool()
async def set_reminder_notification(context: RunContext, message: str, delay_seconds: int) -> str:  # type: ignore
    """
    Set a reminder that fires a system notification after delay_seconds.
    Good for quick timed alerts (max 3600 seconds = 1 hour).
    """
    async def _fire():
        await asyncio.sleep(delay_seconds)
        script = f'display notification "{message}" with title "⏰ Doraemon Reminder"'
        subprocess.run(["osascript", "-e", script])
        logger.info(f"Reminder fired: {message}")

    asyncio.create_task(_fire())
    minutes = delay_seconds // 60
    seconds = delay_seconds % 60
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    return f"Reminder set for {time_str} from now, Sir. I'll notify you."


# ─────────────────────────────────────────────
#  AGENTIC TOOLS LIST
# ─────────────────────────────────────────────

AGENTIC_TOOLS = [
    type_text,
    press_key,
    click_at,
    move_mouse,
    scroll,
    get_screen_size,
    copy_to_clipboard,
    paste_from_clipboard,
    paste_at_cursor,
    launch_app,
    quit_app,
    switch_to_app,
    get_running_apps,
    minimize_window,
    close_window,
    run_shell_command,
    open_terminal_and_run,
    browser_open_url,
    browser_new_tab,
    browser_go_back,
    browser_refresh,
    search_in_browser,
    create_folder,
    delete_file,
    rename_file,
    open_in_finder,
    set_system_volume,
    mute_system,
    unmute_system,
    lock_screen,
    empty_trash,
    show_notification,
    speak_text,
    take_screenshot_and_describe,
    spotlight_search,
    set_reminder_notification,
]
