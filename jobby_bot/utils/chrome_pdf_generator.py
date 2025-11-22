"""Chrome CDP-based PDF generator (AIHawk approach)."""

import base64
import time
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def chrome_browser_options():
    """Configure Chrome options for headless PDF generation."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("window-size=1200x800")
    options.add_argument("--disable-logging")
    options.add_argument("--incognito")
    options.add_argument("--allow-file-access-from-files")
    options.add_argument("--disable-web-security")

    return options


def init_browser() -> webdriver.Chrome:
    """Initialize Chrome browser for PDF generation."""
    try:
        options = chrome_browser_options()
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        return driver
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Chrome browser: {str(e)}")


def html_to_pdf_chrome(html_content: str, output_path: str, driver: webdriver.Chrome = None) -> str:
    """
    Convert HTML to PDF using Chrome DevTools Protocol (AIHawk approach).

    This provides pixel-perfect rendering exactly as Chrome would print it.

    Args:
        html_content: HTML string to convert
        output_path: Where to save the PDF
        driver: Optional existing Chrome driver instance

    Returns:
        Path to the created PDF file
    """
    # Validate HTML content
    if not isinstance(html_content, str) or not html_content.strip():
        raise ValueError("HTML content must be a non-empty string")

    # Create driver if not provided
    should_quit = False
    if driver is None:
        driver = init_browser()
        should_quit = True

    try:
        # Encode HTML as data URL
        encoded_html = urllib.parse.quote(html_content)
        data_url = f"data:text/html;charset=utf-8,{encoded_html}"

        # Load HTML in browser
        driver.get(data_url)

        # Wait for page to fully render
        time.sleep(2)

        # Execute Chrome DevTools Protocol command to print to PDF
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,           # Include background colors/images
            "landscape": False,                # Portrait orientation
            "paperWidth": 8.5,                 # Letter size width in inches
            "paperHeight": 11,                 # Letter size height in inches
            "marginTop": 0.75,                 # Top margin in inches
            "marginBottom": 0.75,              # Bottom margin in inches
            "marginLeft": 0.5,                 # Left margin in inches
            "marginRight": 0.5,                # Right margin in inches
            "displayHeaderFooter": False,      # No header/footer
            "preferCSSPageSize": True,         # Use CSS page size if specified
            "generateDocumentOutline": False,  # No document outline
            "generateTaggedPDF": False,        # No tagged PDF
            "transferMode": "ReturnAsBase64"   # Return as base64 string
        })

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Decode and save PDF
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))

        return output_path

    except Exception as e:
        raise RuntimeError(f"Failed to convert HTML to PDF: {str(e)}")

    finally:
        if should_quit:
            driver.quit()


def create_resume_pdf_chrome(html_content: str, output_path: str) -> str:
    """
    Create resume PDF using Chrome CDP method.

    Args:
        html_content: Complete HTML document string
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    return html_to_pdf_chrome(html_content, output_path)


def create_cover_letter_pdf_chrome(html_content: str, output_path: str) -> str:
    """
    Create cover letter PDF using Chrome CDP method.

    Args:
        html_content: Complete HTML document string
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    return html_to_pdf_chrome(html_content, output_path)
