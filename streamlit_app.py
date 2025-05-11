import os
import time
import datetime
import pytz
import io
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont
import base64

# Function to get Indian current datetime with AM/PM format
def get_indian_datetime():
    india_timezone = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(india_timezone)
    return now.strftime("%d-%m-%Y %I:%M:%S %p %Z")  # %I for 12-hour format, %p for AM/PM

# Function to add timestamp to screenshot with extra large size
def add_timestamp_to_image(image_bytes):
    # Convert bytes to PIL Image
    image = Image.open(io.BytesIO(image_bytes))
    
    # Get timestamp
    timestamp = get_indian_datetime()
    
    # Create draw object
    draw = ImageDraw.Draw(image)
    
    # Calculate font size based on image dimensions (about 10% of image height for much larger text)
    font_size = int(image.height * 0.10)  # Super large font size (doubled from previous)
    
    # Try to use a standard font or fall back to default
    try:
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        try:
            # Try another common font if Arial is not available
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
    
    # Calculate text position (top right with padding)
    text_width, text_height = draw.textbbox((0, 0), timestamp, font=font)[2:4]
    
    # Make semi-transparent background for better readability
    background_box = [(image.width - text_width - 30, 0), 
                      (image.width, text_height + 30)]
    draw.rectangle(background_box, fill=(0, 0, 0, 200))  # More opaque background
    
    # Position text on the background
    position = (image.width - text_width - 15, 15)
    
    # Draw text with extra visibility
    draw.text(position, timestamp, font=font, fill=(255, 255, 255, 255))
    
    # Convert back to bytes
    result_bytes = io.BytesIO()
    image.save(result_bytes, format='PNG')
    result_bytes.seek(0)
    
    return result_bytes

# Helper function to create a download button for images
def get_image_download_button(img_bytes, filename, button_text):
    """
    Generates a download button for a given image
    """
    img_bytes.seek(0)
    b64 = base64.b64encode(img_bytes.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}"><button style="background-color:#4CAF50;color:white;padding:8px 16px;border:none;border-radius:4px;cursor:pointer;">{button_text}</button></a>'
    return href

# Function to capture Netflix screenshot
def get_netflix_screenshot():
    try:
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Try multiple approaches to initialize Chrome driver
        driver = None
        try:
            # Try with ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            st.warning(f"ChromeDriverManager failed: {e}")
            try:
                # Try with direct Chrome path (common in cloud environments)
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                st.error(f"Failed to initialize Chrome driver: {e2}")
                # Show a placeholder image instead when running in cloud
                return create_placeholder_image()
        
        # Navigate to Netflix
        driver.get("https://www.netflix.com")
        
        # Wait for the page to load properly
        time.sleep(3)
        
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        
        # Add timestamp to screenshot
        return add_timestamp_to_image(screenshot)
    except Exception as e:
        st.error(f"Error taking screenshot: {e}")
        return create_placeholder_image()
    finally:
        # Close the browser if it was initialized
        if 'driver' in locals() and driver is not None:
            driver.quit()

# Function to create a placeholder image when selenium fails
def create_placeholder_image():
    # Create a simple image with a message
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Try to use a font or fallback to default
    try:
        font = ImageFont.truetype("Arial", 36)
    except:
        font = ImageFont.load_default()
    
    # Add explanatory text and timestamp
    timestamp = get_indian_datetime()
    message = "Netflix screenshot unavailable in cloud environment"
    draw.text((width/2-200, height/2-50), message, font=font, fill=(255, 255, 255))
    draw.text((width/2-200, height/2+50), f"Timestamp: {timestamp}", font=font, fill=(255, 255, 255))
    
    # Convert to bytes
    result_bytes = io.BytesIO()
    image.save(result_bytes, format='PNG')
    result_bytes.seek(0)
    
    return result_bytes

# Function to perform Netflix login and take screenshots
def login_netflix(email, password):
    screenshots = []
    try:
        # Configure Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Try multiple approaches to initialize Chrome driver - using the EXACT same approach as get_netflix_screenshot
        driver = None
        try:
            # Try with ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            st.warning(f"ChromeDriverManager failed in login: {e}")
            try:
                # Try with direct Chrome path (common in cloud environments)
                driver = webdriver.Chrome(options=chrome_options)
                st.info("Using direct Chrome instance for login")
            except Exception as e2:
                st.error(f"Failed to initialize Chrome driver for login: {e2}")
                # Show placeholder images instead when running in cloud
                return create_login_placeholder_images(email)
        
        # If we reach here, we have a working driver
        st.info("Chrome driver initialized successfully for login")
        
        # Navigate to Netflix login page
        driver.get("https://www.netflix.com/login")
        
        # Wait for login page to load
        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "userLoginId"))
            )
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            
            # Enter email
            email_field.clear()
            email_field.send_keys(email)
            
            # Enter password
            password_field.clear()
            password_field.send_keys(password)
            
            # Take a screenshot now at login page (regardless of password visibility)
            pre_login_screenshot = driver.get_screenshot_as_png()
            screenshots.append(("Login page with credentials", add_timestamp_to_image(pre_login_screenshot)))
            
            # Try multiple approaches to make password visible - but don't fail if this doesn't work
            password_toggled = False
        
            # APPROACH 1: Try to find and click on eye symbol using better selectors
            try:
                # More comprehensive list of selectors for the password toggle
                selectors = [
                    "[data-uia='password-visibility-toggle']",
                    "button.password-toggle",
                    "span.password-toggle",
                    "div.password-toggle",
                    "button[aria-label*='password']",
                    "button[aria-label*='Password']",
                    ".show-password-toggle",
                    "[aria-label='Show Password']",
                    # Additional selectors based on Netflix's HTML structure
                    ".form-control_labelStyles__oy4jpq5 + div button",
                    "div[data-uia='field-password+container'] button",
                    "//div[contains(@data-uia, 'password')]//button",  # XPath
                    "//input[@name='password']/following-sibling::button",  # XPath
                    "//input[@name='password']/..//button"  # XPath to get button near password
                ]
                
                for selector in selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath selector
                            toggle_element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            # CSS selector
                            toggle_element = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            
                        toggle_element.click()
                        time.sleep(1)
                        password_toggled = True
                        print(f"Password toggle successful with selector: {selector}")
                        break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Failed to click on password toggle using selectors: {e}")
            
            # APPROACH 2: If clicking failed, try to change input type using JavaScript
            if not password_toggled:
                try:
                    # Use JavaScript to change the input type from password to text
                    js_script = """
                    document.querySelector('input[type="password"]').type = 'text';
                    return true;
                    """
                    modified = driver.execute_script(js_script)
                    if modified:
                        password_toggled = True
                        print("Password field changed to text type using JavaScript")
                        time.sleep(1)
                except Exception as js_error:
                    print(f"JavaScript password type change failed: {js_error}")
                
            # Try to click login button with multiple attempts
            try:
                # Try multiple selectors for the login button
                login_button_selectors = [
                    "button[data-uia='login-submit-button']",
                    "button[type='submit']",
                    "//button[contains(text(), 'Sign In')]",  # XPath
                    "//button[@type='submit']",  # XPath
                    ".login-form button[type='submit']"
                ]
                
                login_success = False
                for selector in login_button_selectors:
                    try:
                        if selector.startswith("//"):
                            # XPath selector
                            login_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            # CSS selector
                            login_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            
                        login_button.click()
                        login_success = True
                        print(f"Login button click successful with selector: {selector}")
                        break
                    except Exception:
                        continue
                        
                if not login_success:
                    # Try JavaScript click as last resort
                    driver.execute_script("document.querySelector('button[type=\"submit\"]').click();")
                    print("Clicked login button with JavaScript")
                
                # Wait for login to complete and homepage to load
                time.sleep(10)
                
                # Take post-login screenshot
                post_login_screenshot = driver.get_screenshot_as_png()
                screenshots.append(("Post-login Netflix", add_timestamp_to_image(post_login_screenshot)))
                
                # Try to take a profile selection screenshot
                try:
                    # Check if there's a profile selection page
                    profile_buttons = driver.find_elements(By.CSS_SELECTOR, "a.profile-link")
                    if profile_buttons and len(profile_buttons) > 0:
                        # Click on the first profile
                        profile_buttons[0].click()
                        time.sleep(5)  # Wait for profile page to load
                        
                        # Take screenshot of profile page
                        profile_screenshot = driver.get_screenshot_as_png()
                        screenshots.append(("Netflix Profile Page", add_timestamp_to_image(profile_screenshot)))
                except Exception as profile_error:
                    print(f"Profile selection failed: {profile_error}")
                    
                return screenshots
            except Exception as e:
                st.error(f"Error during login process: {e}")
                # If we get an error after initializing the driver, take a screenshot of whatever we see
                try:
                    error_screenshot = driver.get_screenshot_as_png()
                    screenshots.append(("Login error state", add_timestamp_to_image(error_screenshot)))
                    return screenshots
                except:
                    return create_login_placeholder_images(email)
        except Exception as e:
            st.error(f"Error during login process: {e}")
            # If we get an error after initializing the driver, take a screenshot of whatever we see
            try:
                error_screenshot = driver.get_screenshot_as_png()
                screenshots.append(("Login error state", add_timestamp_to_image(error_screenshot)))
                return screenshots
            except:
                return create_login_placeholder_images(email)
    except Exception as e:
        st.error(f"Error setting up login process: {e}")
        return create_login_placeholder_images(email)
    finally:
        # Close the browser if it was initialized
        if 'driver' in locals() and driver is not None:
            try:
                driver.quit()
            except:
                pass  # Ignore errors when closing the driver

# Function to create placeholder login images when selenium fails
def create_login_placeholder_images(email):
    # Create placeholder images to simulate the login process
    images = []
    
    # Create first image (pre-login)
    width, height = 800, 600
    image1 = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image1)
    
    # Try to use a font or fallback to default
    try:
        font = ImageFont.truetype("Arial", 36)
        small_font = ImageFont.truetype("Arial", 24)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add explanatory text and timestamp
    timestamp = get_indian_datetime()
    draw.text((width/2-300, height/2-100), "Netflix login screenshot unavailable", font=font, fill=(255, 255, 255))
    draw.text((width/2-300, height/2), f"Email: {email[:3]}{'*' * (len(email) - 6)}{email[-3:]}", font=small_font, fill=(255, 255, 255))
    draw.text((width/2-300, height/2+50), f"Password: ********", font=small_font, fill=(255, 255, 255))
    draw.text((width/2-300, height/2+150), f"Timestamp: {timestamp}", font=small_font, fill=(255, 255, 255))
    
    # Convert to bytes
    result_bytes1 = io.BytesIO()
    image1.save(result_bytes1, format='PNG')
    result_bytes1.seek(0)
    images.append(("Pre-login with credentials", add_timestamp_to_image(result_bytes1.getvalue())))
    
    # Create second image (post-login)
    image2 = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(image2)
    draw.text((width/2-300, height/2-50), "Post-login Netflix screenshot unavailable", font=font, fill=(255, 255, 255))
    draw.text((width/2-300, height/2+50), f"Running in cloud environment", font=small_font, fill=(255, 255, 255))
    draw.text((width/2-300, height/2+100), f"Timestamp: {timestamp}", font=small_font, fill=(255, 255, 255))
    
    # Convert to bytes
    result_bytes2 = io.BytesIO()
    image2.save(result_bytes2, format='PNG')
    result_bytes2.seek(0)
    images.append(("Post-login Netflix", add_timestamp_to_image(result_bytes2.getvalue())))
    
    return images

# Streamlit UI
def main():
    st.set_page_config(
        page_title="Netflix Screenshot Tool",
        page_icon="🎬",
        layout="wide"
    )
    
    st.title("🎬 Netflix Screenshot Tool")
    st.write(f"Current Indian Time: {get_indian_datetime()}")
    
    # Create a sidebar for the options
    st.sidebar.title("Options")
    option = st.sidebar.radio(
        "Choose an option:",
        ["Homepage Screenshot", "Login and Capture"]
    )
    
    if option == "Homepage Screenshot":
        if st.button("Capture Netflix Homepage"):
            with st.spinner("Getting Netflix screenshot..."):
                screenshot = get_netflix_screenshot()
                
                if screenshot:
                    st.success("Screenshot captured successfully!")
                    st.image(screenshot, caption=f"Netflix homepage - {get_indian_datetime()}", use_column_width=True)
                    
                    # Add download button for the homepage screenshot
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    download_filename = f"netflix_homepage_{timestamp}.png"
                    download_button_html = get_image_download_button(screenshot, download_filename, "Download Screenshot")
                    st.markdown(download_button_html, unsafe_allow_html=True)
                else:
                    st.error("Failed to capture Netflix screenshot.")
    
    else:  # Login and Capture
        with st.form("netflix_login_form"):
            st.subheader("Netflix Login")
            
            email = st.text_input("Email", key="email")
            password = st.text_input("Password", type="password", key="password")
            
            submit_button = st.form_submit_button("Login and Capture Screenshots")
        
        if submit_button:
            if not email or not password:
                st.error("Please provide both email and password.")
            else:
                with st.spinner("Logging into Netflix with provided credentials..."):
                    # Create a placeholder for status messages
                    status_container = st.empty()
                    status_container.info("Initializing browser...")
                    
                    try:
                        screenshots = login_netflix(email, password)
                        status_container.empty()  # Clear the status message
                        
                        if screenshots:
                            st.success(f"Successfully captured {len(screenshots)} screenshots!")
                            
                            # Create timestamp for filenames
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            for i, (desc, img) in enumerate(screenshots):
                                with st.expander(f"{i+1}. {desc}", expanded=True):
                                    # Display the screenshot
                                    st.image(img, caption=desc, use_column_width=True)
                                    
                                    # Create download button for each screenshot
                                    sanitized_desc = desc.replace(" ", "_").lower()
                                    download_filename = f"netflix_{sanitized_desc}_{timestamp}.png"
                                    download_button_html = get_image_download_button(img, download_filename, f"Download {desc}")
                                    st.markdown(download_button_html, unsafe_allow_html=True)
                        else:
                            st.error("Failed to capture Netflix login screenshots.")
                    except Exception as e:
                        status_container.empty()
                        st.error(f"Error during screenshot capture process: {str(e)}")
        
        # Add option to download all screenshots as a batch
        if 'screenshots' in locals() and screenshots:
            st.write("---")
            st.subheader("Batch Download")
            st.write("Download all screenshots:")
            
            # Create a batch download section with individual buttons
            cols = st.columns(min(3, len(screenshots)))  # Create up to 3 columns
            for i, (desc, img) in enumerate(screenshots):
                sanitized_desc = desc.replace(" ", "_").lower()
                download_filename = f"netflix_{sanitized_desc}_{timestamp}.png"
                download_button_html = get_image_download_button(img, download_filename, desc)
                cols[i % 3].markdown(download_button_html, unsafe_allow_html=True)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("This tool captures Netflix screenshots with timestamps.")

if __name__ == "__main__":
    main()
