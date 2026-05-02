import logging
from livekit.agents import function_tool, RunContext
import requests
from ddgs import DDGS
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional
import asyncio
import time

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str,
    max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 5)
    """
    start_time = time.time()
    
    try:
        # Use DDGS for direct DuckDuckGo search
        with DDGS() as ddgs:
            # Perform the search
            search_results = list(ddgs.text(query, max_results=max_results))
            
        if not search_results:
            logging.warning(f"No search results found for query: '{query}'")
            return f"No search results found for '{query}'. Try rephrasing your search or using different keywords."
        
        # Format the results
        formatted_results = _format_search_results(search_results, query)
        
        # Log successful search
        search_time = time.time() - start_time
        logging.info(f"Search completed for '{query}': {len(search_results)} results in {search_time:.2f}s")
        
        return formatted_results
        
    except Exception as e:
        search_time = time.time() - start_time
        error_msg = f"Error searching the web for '{query}': {str(e)}"
        logging.error(f"{error_msg} (took {search_time:.2f}s)")
        
        # Provide helpful error message based on error type
        if "timeout" in str(e).lower():
            return f"Search request timed out for '{query}'. Please try again with a more specific query."
        elif "network" in str(e).lower() or "connection" in str(e).lower():
            return f"Network error while searching for '{query}'. Please check your internet connection and try again."
        else:
            return f"An error occurred while searching for '{query}'. Please try rephrasing your search query."


def _format_search_results(results: list, query: str) -> str:
    """
    Format search results into a readable string.
    
    Args:
        results: List of search result dictionaries
        query: Original search query
        
    Returns:
        Formatted string containing search results
    """
    if not results:
        return f"No results found for '{query}'."
    
    formatted_output = f"Search results for '{query}':\n\n"
    
    for i, result in enumerate(results, 1):
        title = result.get('title', 'No title')
        url = result.get('href', 'No URL')
        snippet = result.get('body', 'No description available')
        
        # Truncate snippet if too long
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        
        formatted_output += f"{i}. **{title}**\n"
        formatted_output += f"   {snippet}\n"
        formatted_output += f"   Source: {url}\n\n"
    
    # Add summary
    formatted_output += f"Found {len(results)} results. "
    if len(results) >= 5:
        formatted_output += "Try a more specific search for more targeted results."
    
    return formatted_output    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"