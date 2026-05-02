import logging
import os
import subprocess
import sqlite_utils
from datetime import datetime
from livekit.agents import function_tool, RunContext
from typing import List, Optional

# Initialize Reminder DB
import os
DB_PATH = "db/reminders.db"
os.makedirs("db", exist_ok=True)
db = sqlite_utils.Database(DB_PATH)
if "reminders" not in db.table_names():
    db["reminders"].create({
        "id": int,
        "task": str,
        "datetime": str,
        "completed": bool,
    }, pk="id")

@function_tool()
async def create_file(
    context: RunContext, # type: ignore
    filename: str,
    content: str
) -> str:
    """
    Create a text or markdown file with the specified content.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File {filename} created successfully, Sir."
    except Exception as e:
        logging.error(f"File creation failed: {e}")
        return f"Failed to create file: {str(e)}"

@function_tool()
async def read_file(
    context: RunContext, # type: ignore
    filepath: str
) -> str:
    """
    Read the contents of a file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f"Contents of {filepath}:\n\n{f.read()}"
    except Exception as e:
        logging.error(f"File read failed: {e}")
        return f"Failed to read file: {str(e)}"

@function_tool()
async def list_directory(
    context: RunContext, # type: ignore
    path: str = "."
) -> str:
    """
    List files and folders in a directory.
    """
    try:
        files = os.listdir(path)
        return f"Directory listing for {path}:\n" + "\n".join(files)
    except Exception as e:
        logging.error(f"Directory list failed: {e}")
        return f"Failed to list directory: {str(e)}"

@function_tool()
async def search_files(
    context: RunContext, # type: ignore
    keyword: str,
    directory: str = "."
) -> str:
    """
    Search for files containing a specific keyword in their name or content.
    """
    try:
        matches = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if keyword in file:
                    matches.append(os.path.join(root, file))
                else:
                    try:
                        with open(os.path.join(root, file), 'r', errors='ignore') as f:
                            if keyword in f.read():
                                matches.append(os.path.join(root, file))
                    except:
                        pass
        return f"Found {len(matches)} matches for '{keyword}':\n" + "\n".join(matches)
    except Exception as e:
        logging.error(f"File search failed: {e}")
        return f"Error searching files: {str(e)}"

@function_tool()
async def open_file(
    context: RunContext, # type: ignore
    filepath: str
) -> str:
    """
    Open a file with the default system application.
    """
    try:
        if os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', filepath])
        return f"Opening {filepath}, Sir."
    except Exception as e:
        logging.error(f"Open file failed: {e}")
        return f"Failed to open file: {str(e)}"

@function_tool()
async def add_reminder(
    context: RunContext, # type: ignore
    task: str,
    datetime_str: str
) -> str:
    """
    Add a reminder to the system.
    datetime_str should be in the format 'YYYY-MM-DD HH:MM'.
    """
    try:
        db["reminders"].insert({
            "task": task,
            "datetime": datetime_str,
            "completed": False
        }, replace=False)
        return f"Reminder set: '{task}' for {datetime_str}, Sir."
    except Exception as e:
        logging.error(f"Add reminder failed: {e}")
        return f"Failed to add reminder: {str(e)}"

@function_tool()
async def get_reminders(
    context: RunContext, # type: ignore
) -> str:
    """
    Fetch all upcoming reminders.
    """
    try:
        reminders = db["reminders"].where("completed = 0")
        if not reminders:
            return "No upcoming reminders, Sir. Your schedule is clear."

        output = "Upcoming Reminders, Sir:\n"
        for r in reminders:
            output += f"- [{r['id']}] {r['datetime']}: {r['task']}\n"
        return output
    except Exception as e:
        logging.error(f"Get reminders failed: {e}")
        return f"Failed to retrieve reminders: {str(e)}"

@function_tool()
async def delete_reminder(
    context: RunContext, # type: ignore
    reminder_id: int
) -> str:
    """
    Remove a reminder by its ID.
    """
    try:
        db["reminders"].delete(reminder_id)
        return f"Reminder {reminder_id} deleted, Sir."
    except Exception as e:
        logging.error(f"Delete reminder failed: {e}")
        return f"Failed to delete reminder: {str(e)}"
