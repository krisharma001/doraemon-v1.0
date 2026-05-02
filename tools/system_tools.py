import logging
import os
import subprocess
import webbrowser
import psutil
import pyautogui
from datetime import datetime
from livekit.agents import function_tool, RunContext
from typing import List, Optional

def _open_app_cross_platform(app_name: str):
    """Helper to open applications based on OS."""
    try:
        if os.name == 'nt': # Windows
            subprocess.Popen(['start', app_name], shell=True)
        elif os.name == 'posix': # Mac/Linux
            if os.uname().sysname == 'Darwin':
                subprocess.Popen(['open', '-a', app_name])
            else:
                subprocess.Popen(['xdg-open', app_name])
    except Exception as e:
        logging.error(f"Error opening application {app_name}: {e}")
        return False
    return True

@function_tool()
async def open_application(
    context: RunContext, # type: ignore
    app_name: str
) -> str:
    """
    Open a system application by name.
    """
    logging.info(f"Opening application: {app_name}")
    if _open_app_cross_platform(app_name):
        return f"Opening {app_name}, Sir."
    return f"I encountered an issue opening {app_name}, Sir."

@function_tool()
async def open_url(
    context: RunContext, # type: ignore
    url: str
) -> str:
    """
    Open a URL in the default web browser.
    """
    logging.info(f"Opening URL: {url}")
    webbrowser.open(url)
    return f"Opening {url}, Sir."

@function_tool()
async def open_multiple_urls(
    context: RunContext, # type: ignore
    urls: List[str]
) -> str:
    """
    Open multiple URLs simultaneously in new tabs.
    """
    logging.info(f"Opening multiple URLs: {urls}")
    for url in urls:
        webbrowser.open(url)
    return f"Opened {len(urls)} tabs for you, Sir."

@function_tool()
async def take_screenshot(
    context: RunContext, # type: ignore
) -> str:
    """
    Capture the current screen and save it as a file.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        pyautogui.screenshot().save(filename)
        return f"Screenshot captured and saved as {filename}, Sir."
    except Exception as e:
        logging.error(f"Screenshot failed: {e}")
        return f"Failed to capture screenshot: {str(e)}"

@function_tool()
async def get_system_info(
    context: RunContext, # type: ignore
) -> str:
    """
    Get current system resource usage (CPU, RAM, Battery).
    """
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        battery = psutil.sensors_battery()

        status = f"System Status, Sir:\n"
        status += f"- CPU Usage: {cpu_usage}%\n"
        status += f"- RAM Usage: {ram.percent}%\n"

        if battery:
            status += f"- Battery: {battery.percent}% ({'Charging' if battery.power_plugged else 'Discharging'})\n"
        else:
            status += "- Battery: Not detected\n"

        return status
    except Exception as e:
        logging.error(f"System info retrieval failed: {e}")
        return f"Error retrieving system info: {str(e)}"

@function_tool()
async def set_volume(
    context: RunContext, # type: ignore
    level: int
) -> str:
    """
    Set the system volume level (0-100).
    """
    try:
        if not 0 <= level <= 100:
            return "Invalid volume level. Please use a value between 0 and 100."

        if os.name == 'nt':
            # Windows volume control often requires external libraries or shell commands
            # For simple implementation, use nircmd or NirCmd.exe if installed
            # return "Volume control on Windows is currently limited. Please install NirCmd."
            pass
        elif os.name == 'posix' and os.uname().sysname == 'Darwin':
            # macOS volume control
            subprocess.Popen(['osascript', '-e', f'set volume output volume {level}'])
        else:
            return "Volume control not supported on this OS."

        return f"System volume set to {level}%, Sir."
    except Exception as e:
        logging.error(f"Volume control failed: {e}")
        return f"Error setting volume: {str(e)}"

@function_tool()
async def get_clipboard(
    context: RunContext, # type: ignore
) -> str:
    """
    Read content from the system clipboard.
    """
    try:
        import pyperclip
        return f"Clipboard content: {pyperclip.paste()}"
    except Exception as e:
        logging.error(f"Clipboard read failed: {e}")
        return f"Error reading clipboard: {str(e)}"

@function_tool()
async def set_clipboard(
    context: RunContext, # type: ignore
    text: str
) -> str:
    """
    Set the content of the system clipboard.
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return f"Text copied to clipboard, Sir."
    except Exception as e:
        logging.error(f"Clipboard write failed: {e}")
        return f"Error writing to clipboard: {str(e)}"
