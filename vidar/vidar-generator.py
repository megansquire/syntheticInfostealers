import csv
import os
import random
import hashlib
import json
import traceback
from datetime import datetime, timedelta
import string
import base64
from PIL import Image, ImageDraw
import io

class VidarLogGenerator:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.personas = self.load_vidar_personas()
        self.load_configs()
        self.output_base_dir = self.config['main']['output_base_dir']
        
    def load_configs(self):
        """Load all configuration files"""
        self.config = {}
        config_files = [
            'main', 'browser_versions', 'sites', 'downloads', 'hardware',
            'processes', 'software', 'search_queries', 'cookie_names',
            'country', 'computer_names'
        ]
        
        for config_name in config_files:
            with open(f'vidar_configs/{config_name}.json', 'r') as f:
                self.config[config_name] = json.load(f)
    
    def load_vidar_personas(self):
        """Load personas infected with Vidar"""
        vidar_personas = []
        
        with open(self.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Infection') == 'Vidar':
                    vidar_personas.append(row)
        
        print(f"Found {len(vidar_personas)} personas infected with Vidar")
        return vidar_personas
    
    def get_persona_seed(self, persona_id, suffix=''):
        """Generate consistent seed for persona data"""
        return int(hashlib.md5(f"{persona_id}{suffix}".encode()).hexdigest()[:8], 16)
    
    def generate_autofill(self, persona, browser_profile):
        """Generate autofill data for a browser profile"""
        random.seed(self.get_persona_seed(persona['PersonaID'], f'autofill_{browser_profile}'))
        
        entries = []
        
        # Personal info
        first_name = persona.get('FirstName', 'John')
        last_name = persona.get('LastName', 'Doe')
        email = persona.get('EmailPersonal', 'user@example.fake')
        phone = self.generate_phone_number(persona.get('Country', 'US'))
        
        # Address info
        address = self.generate_address(persona)
        
        # Common form fields
        form_fields = {
            'name': f"{first_name} {last_name}",
            'billing_state': address['state'],
            'cardExpiry': f"{random.randint(1,12):02d} / {random.randint(25,29)}",
            'cardHolder': f"Mr {first_name[0]} {last_name}",
            'cardexp': f"{random.randint(1,12):02d}/{random.randint(25,29)}",
            'email': email,
            'phone': phone,
            'address': address['street'],
            'city': address['city'],
            'zip': address['zip'],
            'username': email.split('@')[0] if '@' in email else first_name.lower()
        }
        
        # Generate 20-50 entries mixing form fields and search queries
        num_entries = random.randint(20, 50)
        
        # Add form fields
        for _ in range(int(num_entries * 0.6)):
            field = random.choice(list(form_fields.keys()))
            value = form_fields[field]
            entries.append(f"{field} {value}")
        
        # Add search queries (marked with 'q')
        search_queries = self.generate_search_queries(persona, int(num_entries * 0.4))
        for query in search_queries:
            entries.append(f"q {query}")
        
        random.shuffle(entries)
        return '\n'.join(entries) + '\n'
    
    def generate_cookies(self, persona, browser_profile):
        """Generate cookies for a browser profile"""
        random.seed(self.get_persona_seed(persona['PersonaID'], f'cookies_{browser_profile}'))
        
        cookies = []
        sites = self.get_sites_for_persona(persona)
        cookie_domains = []
        
        # Generate 40-80 cookies
        num_cookies = random.randint(40, 80)
        
        for _ in range(num_cookies):
            domain = random.choice(sites)
            
            # Vidar format includes both www. and . prefixed domains
            if random.random() > 0.5 and not domain.startswith('www.'):
                full_domain = f"www.{domain}"
            else:
                full_domain = domain
            
            cookie_domains.append(domain)
            
            # Cookie format: domain \t includeSubdomains \t path \t secure \t expiry \t name \t value
            include_subdomains = 'TRUE' if random.random() > 0.3 else 'FALSE'
            path = '/'
            secure = 'TRUE' if random.random() > 0.3 else 'FALSE'
            
            # Expiry timestamp
            expiry = int((datetime.now() + timedelta(days=random.randint(30, 730))).timestamp())
            
            # Cookie names based on site
            cookie_names = self.config['cookie_names']
            if 'google' in domain:
                names = cookie_names['google']
            elif 'facebook' in domain:
                names = cookie_names['facebook']
            elif 'coursehero' in domain:
                names = cookie_names['coursehero']
            else:
                names = cookie_names['default']
            
            name = random.choice(names)
            value = self.generate_cookie_value()
            
            # Special handling for some domains
            if domain.startswith('.'):
                cookie_line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}"
            else:
                dot_domain = f".{domain}" if not domain.startswith('www.') else domain.replace('www.', '.')
                cookie_line = f"{full_domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}"
            
            cookies.append(cookie_line)
        
        return '\n'.join(cookies) + '\n', cookie_domains
    
    def generate_cookie_value(self):
        """Generate a realistic cookie value"""
        value_types = [
            lambda: ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(20, 40))),
            lambda: hashlib.md5(str(random.random()).encode()).hexdigest(),
            lambda: f"{random.randint(100000, 999999)}%3A0.0.0.0.0%3B{random.randint(100000, 999999)}%3A0.0.0.0.0"
        ]
        return random.choice(value_types)()
    
    def generate_downloads(self, persona, browser_profile):
        """Generate download history"""
        random.seed(self.get_persona_seed(persona['PersonaID'], f'downloads_{browser_profile}'))
        
        downloads = []
        username = persona.get('FirstName', 'User')
        archetype = persona.get('PersonaArchetype', '')
        
        # Number of downloads based on persona
        if persona.get('DownloadHabits') == 'Frequent':
            num_downloads = random.randint(10, 20)
        else:
            num_downloads = random.randint(3, 10)
        
        # Get downloads from config
        downloads_config = self.config['downloads']
        common_files = downloads_config['common'].copy()
        
        # Add archetype-specific downloads
        if 'Gaming' in archetype:
            common_files.extend(downloads_config.get('gaming', []))
        
        if 'Student' in archetype:
            common_files.extend(downloads_config.get('student', []))
        
        if 'Corporate' in archetype or 'Small_Business' in archetype:
            common_files.extend(downloads_config.get('corporate', []))
        
        # Add some image downloads
        image_searches = [
            'cat meme funny', 'desktop wallpaper 4k', 'recipe chocolate cake',
            'british old guy selfie', 'vacation photos beach', 'car wallpaper'
        ]
        
        for _ in range(num_downloads):
            if random.random() > 0.7 and image_searches:
                # Image download
                search = random.choice(image_searches)
                filename = f"{random.randint(1000000000, 9999999999)}_{random.randint(10000000, 99999999)}{random.choice(['a', 'b', 'c', 'd'])}{random.randint(1, 9)}_z.jpg"
                url = f"https://www.google.com/search?q={search.replace(' ', '+')}&client=firefox-b-d&sca_esv={hashlib.md5(search.encode()).hexdigest()[:16]}"
                downloads.append(f"C:\\Users\\{username}\\Downloads\\{filename}\n{url}")
            else:
                # Regular file download
                file_info = random.choice(common_files)
                downloads.append(f"C:\\Users\\{username}\\Downloads\\{file_info[0]}\n{file_info[1]}")
        
        # Join with double newline as per format
        return '\n\n'.join(downloads) + '\n'
    
    def generate_passwords(self, persona):
        """Generate passwords.txt in Vidar format"""
        random.seed(self.get_persona_seed(persona['PersonaID'], 'passwords'))
        
        entries = []
        
        # Get user credentials
        email = persona.get('EmailPersonal', 'user@example.fake')
        work_email = persona.get('EmailWork', '')
        first_name = persona.get('FirstName', 'User')
        last_name = persona.get('LastName', 'Smith')
        
        # Generate passwords based on habits
        if persona.get('PasswordHabits') == 'Reuses_Passwords':
            main_password = f"{first_name}{random.randint(2020, 2024)}!"
            passwords = [main_password] * 10
        elif persona.get('PasswordHabits') == 'Good_Hygiene':
            passwords = []
            for _ in range(20):
                passwords.append(''.join(random.choices(
                    string.ascii_letters + string.digits + '!@#$%^&*',
                    k=random.randint(12, 20)
                )))
        else:
            passwords = [
                f"{first_name}{random.randint(2020, 2024)}!",
                f"WANKstain{random.randint(10, 99)}!",
                f"{last_name.lower()}{random.randint(100, 999)}",
                'Welcome123!',
                f"{first_name.lower()}123"
            ]
        
        # Get browser profiles
        browser_profiles = self.get_browser_profiles(persona)
        
        # Generate login entries
        sites = self.get_sites_for_persona(persona)
        num_passwords = random.randint(15, 40)
        
        for _ in range(num_passwords):
            site = random.choice(sites)
            browser, profile = random.choice(browser_profiles)
            
            # Format browser string for Vidar
            if browser == 'Mozilla Firefox':
                browser_str = f"Mozilla Firefox [{profile}]"
            elif browser == 'Google Chrome':
                browser_str = f"Google Chrome [{profile}]"
            elif browser == 'Microsoft Edge':
                browser_str = f"Microsoft Edge [{profile}]"
            else:
                browser_str = f"{browser} [{profile}]"
            
            # Generate login
            if random.random() > 0.3 and email:
                login = email
            elif work_email and ('linkedin' in site or 'slack' in site):
                login = work_email
            else:
                login = f"{first_name.lower()}{random.randint(100, 999)}"
                if '@' not in login and random.random() > 0.5:
                    login += '@outlook.com'
            
            # Pick password
            if persona.get('PasswordHabits') == 'Reuses_Passwords':
                password = passwords[0]
            else:
                password = random.choice(passwords)
            
            # Vidar format with line breaks
            entry = f"""Soft: {browser_str}
Host: https://{site}
Login: {login}
Password: {password}"""
            
            entries.append(entry)
        
        return '\n\n\n'.join(entries) + '\n'
    
    def generate_information_txt(self, persona):
        """Generate information.txt in Vidar format"""
        random.seed(self.get_persona_seed(persona['PersonaID'], 'system'))
        
        # Get persona details
        country = persona.get('Country', 'US')
        city = persona.get('City', 'Unknown')
        ip = self.generate_ip_for_country(country)
        
        # Generate system info
        device_type = persona.get('DeviceType', 'Personal_Laptop')
        income_level = persona.get('IncomeLevel', 'Medium')
        cpu = self.generate_cpu_info(device_type, income_level)
        gpu = self.generate_gpu_info(device_type)
        ram_mb = self.generate_ram_amount(device_type, income_level)
        
        # OS info - determine version based on examples
        os_version = persona.get('OS', 'Windows 10')
        if '11' in os_version:
            os_name = random.choice(['Windows 11', 'Windows 11 Home'])
            version = random.choice(['10.1', '11'])
        else:
            os_name = 'Windows 10 Home'
            version = '10.1'
        
        username = persona.get('FirstName', 'User')
        
        # Special cases based on examples
        if username == 'B':
            username = 'B'
        elif username == 'Admin':
            username = 'Admin'
        elif username == '4afsm':
            username = '4afsm'
        
        pc_name = self.generate_computer_name(device_type)
        
        # Dates - use format from examples
        current_date = datetime.now()
        install_date = current_date - timedelta(days=random.randint(30, 730))
        
        # Generate GUID and HWID based on examples
        guid = self.generate_guid()
        hwid = self.generate_vidar_hwid()
        machine_id = self.generate_machine_id()
        
        # Timezone
        timezone_offset = self.get_timezone_offset(persona.get('Timezone', 'UTC'))
        
        # Resolution
        resolution = self.generate_screen_resolution(device_type)
        
        # Path - use patterns from config
        paths = self.config['main']['execution_paths']
        exec_path = random.choice(paths).format(username=username, random=''.join(random.choices(string.ascii_letters, k=8)))
        
        # Select header variant
        header = random.choice(self.config['main']['headers'])
        
        # Generate process list
        processes = self.generate_process_list(persona)
        
        # Generate software list
        software = self.generate_software_list(persona)
        
        # Format date/time based on examples (some use single digits, some double)
        if random.random() > 0.5:
            date_str = current_date.strftime('%-d/%-m/%Y %-H:%-M:%-S')
            install_date_str = install_date.strftime('%-d/%-m/%Y %-H:%-M:%-S')
        else:
            date_str = current_date.strftime('%d/%m/%Y %H:%M:%S')
            install_date_str = install_date.strftime('%d/%m/%Y %H:%M:%S')
        
        # Languages
        languages = self.config['country']['languages'].get(country, 'English (United States)')
        
        # Format the information.txt
        content = f"""{header}Ip: {ip}
Country: {country}
Version: {version}

Date: {date_str}
MachineID: {machine_id}
GUID: {{{guid}}}
HWID: {hwid}-{guid}

Path: {exec_path}
Work Dir: In memory

Windows: {os_name}
Install Date: {install_date_str}
AV: {persona.get('AntivirusType', 'Windows Defender')}
Computer Name: {pc_name}
User Name: {username}
Display Resolution: {resolution}
Keyboard Languages: {languages}
Local Time: {date_str}
TimeZone: {timezone_offset}

[Hardware]
Processor: {cpu}
Cores: {self.get_cpu_cores(device_type)}
Threads: {self.get_cpu_threads(device_type)}
RAM: {ram_mb} MB
VideoCard: {gpu}

[Processes]
{processes}

[Software]
{software}"""
        
        return content
    
    def generate_process_list(self, persona):
        """Generate process list for Vidar"""
        processes_config = self.config['processes']
        processes = processes_config['base'].copy()
        
        # Add many svchost instances
        svchost_count = random.randint(*processes_config['svchost_count'])
        for _ in range(svchost_count):
            processes.append("svchost.exe")
        
        # Add browser processes
        primary_browser = persona.get('PrimaryBrowser', '')
        secondary_browser = persona.get('SecondaryBrowser', '')
        
        for browser in [primary_browser, secondary_browser]:
            if browser and browser in processes_config['browser']:
                browser_config = processes_config['browser'][browser]
                count = random.randint(*browser_config['count'])
                for _ in range(count):
                    for process in browser_config['processes']:
                        processes.append(process)
        
        # NVIDIA processes
        if persona.get('DeviceType') == 'Gaming_Rig' or random.random() > 0.5:
            processes.extend(processes_config['nvidia'])
        
        # Archetype-specific processes
        archetype = persona.get('PersonaArchetype', '')
        
        if 'Gaming' in archetype:
            processes.extend(processes_config['gaming'])
            # Multiple Steam web helper instances
            for _ in range(random.randint(4, 7)):
                processes.append("steamwebhelper.exe")
        
        if 'Corporate' in archetype or 'Small_Business' in archetype:
            processes.extend(processes_config['corporate'])
        
        # Antivirus processes
        av_type = persona.get('AntivirusType', '')
        if av_type in processes_config['antivirus']:
            processes.extend(processes_config['antivirus'][av_type])
        
        # Add the malware itself
        malware_process = random.choice(self.config['main']['malware_processes'])
        processes.append(malware_process)
        
        # Add ending processes
        processes.extend(processes_config['ending'])
        
        return '\n'.join(processes)
    
    def generate_software_list(self, persona):
        """Generate software list for Vidar"""
        software_config = self.config['software']
        software = []
        
        # Base software with version placeholders
        edge_version = random.choice(self.config['browser_versions']['Edge'])
        update_minor = random.randint(180, 195)
        update_patch = random.randint(30, 50)
        webview_version = random.choice(self.config['browser_versions']['Edge'])
        
        for base_software in software_config['base']:
            software.append(base_software.format(
                edge_version=edge_version,
                update_minor=update_minor,
                update_patch=update_patch,
                webview_version=webview_version
            ))
        
        # Visual C++ Redistributables
        software.extend(software_config['vcredist'])
        
        # Browsers
        if 'Chrome' in persona.get('PrimaryBrowser', ''):
            version = random.choice(self.config['browser_versions']['Chrome'])
            software.append(software_config['browsers']['Chrome'].format(version=version))
        
        if 'Firefox' in persona.get('PrimaryBrowser', '') or 'Firefox' in persona.get('SecondaryBrowser', ''):
            version = random.choice(self.config['browser_versions']['Firefox'])
            software.append(software_config['browsers']['Firefox'].format(version=version))
        
        # Archetype-specific software
        archetype = persona.get('PersonaArchetype', '')
        
        if 'Gaming' in archetype:
            software.extend(software_config['gaming']['software'])
            # Add some games
            games = software_config['gaming']['games']
            software.extend(random.sample(games, random.randint(1, 3)))
        
        if 'Student' in archetype:
            software.extend(software_config['student'])
        
        if 'Corporate' in archetype or 'Small_Business' in archetype:
            software.extend(software_config['corporate'])
        
        # Utilities
        if persona.get('TechSavviness') in ['High', 'Medium']:
            software.extend(random.sample(software_config['utilities'], random.randint(2, 4)))
        
        # Communication tools
        if persona.get('SocialMediaUser') == 'Heavy':
            software.extend(random.sample(software_config['communication'], random.randint(1, 2)))
        
        # Antivirus
        av_type = persona.get('AntivirusType', '')
        if av_type in software_config['antivirus']:
            av_software = software_config['antivirus'][av_type]
            if isinstance(av_software, list):
                software.extend(av_software)
            else:
                software.append(av_software)
        
        # Developer tools
        if persona.get('TechSavviness') == 'High':
            software.extend(random.sample(software_config['developer'], random.randint(2, 4)))
        
        return '\n'.join(software)
    
    def generate_screenshot(self, persona):
        """Generate a screenshot showing desktop"""
        random.seed(self.get_persona_seed(persona['PersonaID'], 'screenshot'))
        
        # Get resolution
        resolution_str = self.generate_screen_resolution(persona.get('DeviceType', 'Personal_Laptop'))
        width, height = map(int, resolution_str.split('x'))
        
        # Create image
        wallpaper_colors = self.config['main']['wallpaper_colors']
        img = Image.new('RGB', (width, height), color=tuple(random.choice(wallpaper_colors)))
        draw = ImageDraw.Draw(img)
        
        # Add taskbar at bottom
        taskbar_height = 40
        draw.rectangle([(0, height - taskbar_height), (width, height)], fill=(48, 48, 48))
        
        # Add start button
        draw.rectangle([(0, height - taskbar_height), (48, height)], fill=(0, 120, 215))
        
        # Add some window outlines to simulate open applications
        archetype = persona.get('PersonaArchetype', '')
        
        # Browser window
        if random.random() > 0.3:
            window_x = random.randint(100, width - 800)
            window_y = random.randint(50, height - 600)
            draw.rectangle([(window_x, window_y), (window_x + 800, window_y + 600)], 
                          outline=(200, 200, 200), width=1)
            # Title bar
            draw.rectangle([(window_x, window_y), (window_x + 800, window_y + 30)], 
                          fill=(240, 240, 240))
        
        # Gaming overlay if gamer
        if 'Gaming' in archetype and random.random() > 0.5:
            # Discord overlay in corner
            draw.rectangle([(width - 300, 50), (width - 50, 200)], 
                          fill=(54, 57, 63), outline=(200, 200, 200))
        
        # File explorer window if downloading
        if persona.get('DownloadHabits') == 'Frequent':
            window_x = random.randint(200, width - 600)
            window_y = random.randint(100, height - 400)
            draw.rectangle([(window_x, window_y), (window_x + 600, window_y + 400)], 
                          outline=(200, 200, 200), width=1, fill=(255, 255, 255))
        
        # Convert to JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        return output.getvalue()
    
    def get_browser_profiles(self, persona):
        """Get browser profiles for persona"""
        profiles = []
        
        # Primary browser
        primary = persona.get('PrimaryBrowser', 'Chrome')
        if primary and primary != 'None':
            if primary == 'Chrome':
                profiles.append(('Google Chrome', 'Default'))
                # Some users have guest profile
                if random.random() > 0.8:
                    profiles.append(('Google Chrome', 'Guest Profile'))
            elif primary == 'Edge':
                profiles.append(('Microsoft Edge', 'Default'))
            elif primary == 'Firefox':
                # Firefox uses random profile names
                profile_name = self.generate_firefox_profile_name()
                profiles.append(('Mozilla Firefox', profile_name))
            elif primary == 'Brave':
                profiles.append(('Brave Browser', 'Default'))
        
        # Secondary browser
        secondary = persona.get('SecondaryBrowser', 'None')
        if secondary and secondary != 'None' and secondary != primary:
            if secondary == 'Chrome' and not any(p[0] == 'Google Chrome' for p in profiles):
                profiles.append(('Google Chrome', 'Default'))
            elif secondary == 'Edge' and not any(p[0] == 'Microsoft Edge' for p in profiles):
                profiles.append(('Microsoft Edge', 'Default'))
            elif secondary == 'Firefox' and not any(p[0] == 'Mozilla Firefox' for p in profiles):
                profile_name = self.generate_firefox_profile_name()
                profiles.append(('Mozilla Firefox', profile_name))
        
        # Some personas have IE cookies
        if random.random() > 0.7:
            profiles.append(('Internet Explorer', 'Default'))
        
        return profiles if profiles else [('Google Chrome', 'Default')]
    
    def generate_firefox_profile_name(self):
        """Generate Firefox profile name format"""
        chars = string.ascii_lowercase + string.digits
        prefix = ''.join(random.choices(chars, k=8))
        suffixes = ['default-release', 'default', 'default-release-1', 'default-esr']
        suffix = random.choice(suffixes)
        
        # Sometimes add timestamp
        if 'release-1' in suffix and random.random() > 0.5:
            timestamp = int((datetime.now() - timedelta(days=random.randint(30, 365))).timestamp() * 1000)
            return f"{prefix}.{suffix}-{timestamp}"
        
        return f"{prefix}.{suffix}"
    
    def generate_vidar_log(self, persona):
        """Generate complete Vidar log for a persona"""
        persona_id = persona['PersonaID']
        log_dir = os.path.join(self.output_base_dir, f"Vidar_{persona_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        print(f"Generating Vidar log for {persona_id}: {persona.get('FirstName', 'Unknown')} {persona.get('LastName', 'Unknown')}")
        
        # Create directory structure
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(os.path.join(log_dir, 'Autofill'), exist_ok=True)
        os.makedirs(os.path.join(log_dir, 'Cookies'), exist_ok=True)
        os.makedirs(os.path.join(log_dir, 'Downloads'), exist_ok=True)
        
        # Get browser profiles
        browser_profiles = self.get_browser_profiles(persona)
        
        # Track all cookie domains
        all_cookie_domains = []
        
        # Generate browser-specific files
        for browser, profile in browser_profiles:
            # Skip IE for autofill and downloads
            if browser == 'Internet Explorer':
                continue
                
            # Format filenames
            if browser == 'Google Chrome':
                autofill_name = f"Google Chrome_{profile}.txt"
                cookie_name = f"Google Chrome_{profile}.txt"
                download_name = f"Google Chrome_{profile}.txt"
            elif browser == 'Microsoft Edge':
                autofill_name = f"Microsoft Edge_{profile}.txt"
                cookie_name = f"Microsoft Edge_{profile}.txt" if random.random() > 0.5 else "Edge_Cookies.txt"
                download_name = f"Microsoft Edge_{profile}.txt"
            elif browser == 'Mozilla Firefox':
                autofill_name = f"Mozilla Firefox_{profile}.txt"
                cookie_name = f"Mozilla Firefox_{profile}.txt"
                download_name = None  # Firefox downloads not always included
            else:
                autofill_name = f"{browser}_{profile}.txt"
                cookie_name = f"{browser}_{profile}.txt"
                download_name = f"{browser}_{profile}.txt"
            
            # Generate autofill
            autofill_path = os.path.join(log_dir, 'Autofill', autofill_name)
            with open(autofill_path, 'w', encoding='utf-8') as f:
                f.write(self.generate_autofill(persona, f"{browser}_{profile}"))
            
            # Generate cookies
            cookie_content, cookie_domains = self.generate_cookies(persona, f"{browser}_{profile}")
            
            # Special case for Firefox cookie naming
            if browser == 'Mozilla Firefox' and random.random() > 0.5:
                cookie_name = f"cookies_Mozilla Firefox_{profile.split('.')[0]}"
            
            cookie_path = os.path.join(log_dir, 'Cookies', cookie_name)
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write(cookie_content)
            all_cookie_domains.extend(cookie_domains)
            
            # Generate downloads (not for Firefox usually)
            if download_name and (browser != 'Mozilla Firefox' or random.random() > 0.7):
                download_path = os.path.join(log_dir, 'Downloads', download_name)
                with open(download_path, 'w', encoding='utf-8') as f:
                    f.write(self.generate_downloads(persona, f"{browser}_{profile}"))
        
        # IE cookies if applicable
        if any(p[0] == 'Internet Explorer' for p in browser_profiles):
            cookie_path = os.path.join(log_dir, 'Cookies', 'IE_Cookies.txt')
            cookie_content, cookie_domains = self.generate_cookies(persona, 'IE_Default')
            with open(cookie_path, 'w', encoding='utf-8') as f:
                f.write(cookie_content)
            all_cookie_domains.extend(cookie_domains)
        
        # Generate cookie_list.txt
        unique_domains = sorted(set(all_cookie_domains))
        with open(os.path.join(log_dir, 'cookie_list.txt'), 'w', encoding='utf-8') as f:
            # Include both base domains and www variants
            final_domains = []
            for domain in unique_domains:
                final_domains.append(domain)
                if not domain.startswith('www.') and random.random() > 0.5:
                    final_domains.append(f"www.{domain}")
            
            # Remove duplicates and sort
            final_domains = sorted(set(final_domains))
            f.write('\n'.join(final_domains) + '\n')
        
        # Generate information.txt
        with open(os.path.join(log_dir, 'information.txt'), 'w', encoding='utf-8') as f:
            f.write(self.generate_information_txt(persona))
        
        # Generate passwords.txt
        with open(os.path.join(log_dir, 'passwords.txt'), 'w', encoding='utf-8') as f:
            f.write(self.generate_passwords(persona))
        
        # Generate screenshot.jpg
        screenshot_data = self.generate_screenshot(persona)
        with open(os.path.join(log_dir, 'screenshot.jpg'), 'wb') as f:
            f.write(screenshot_data)
        
        return log_dir
    
    # Helper methods
    def generate_cpu_info(self, device_type, income_level):
        """Generate CPU info based on device and income"""
        hardware_config = self.config['hardware']['cpu']
        
        if device_type == 'Gaming_Rig':
            cpus = hardware_config['Gaming_Rig']
        elif device_type == 'Business_Laptop':
            cpus = hardware_config['Business_Laptop']
        else:
            cpus = hardware_config['default']
        
        return random.choice(cpus)
    
    def generate_gpu_info(self, device_type):
        """Generate GPU info"""
        hardware_config = self.config['hardware']['gpu']
        
        if device_type == 'Gaming_Rig':
            gpus = hardware_config['Gaming_Rig']
        elif 'Laptop' in device_type:
            gpus = hardware_config['laptop']
        else:
            gpus = hardware_config['default']
        
        return random.choice(gpus)
    
    def generate_ram_amount(self, device_type, income_level):
        """Generate RAM amount in MB"""
        hardware_config = self.config['hardware']['ram_mb']
        
        if device_type == 'Gaming_Rig':
            return random.choice(hardware_config['Gaming_Rig'])
        elif income_level == 'High':
            return random.choice(hardware_config['high_income'])
        else:
            return random.choice(hardware_config['default'])
    
    def generate_screen_resolution(self, device_type):
        """Generate screen resolution"""
        hardware_config = self.config['hardware']['resolution']
        
        if device_type == 'Gaming_Rig':
            return random.choice(hardware_config['Gaming_Rig'])
        else:
            return random.choice(hardware_config['default'])
    
    def generate_computer_name(self, device_type):
        """Generate computer name"""
        computer_names = self.config['computer_names']
        
        if device_type in computer_names:
            prefixes = computer_names[device_type]
        else:
            prefixes = computer_names['default']
        
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=random.randint(6, 8)))
        
        return f"{prefix}-{suffix}"
    
    def generate_guid(self):
        """Generate Windows GUID format"""
        # Based on examples, sometimes short, sometimes full
        if random.random() > 0.3:
            parts = [
                ''.join(random.choices('0123456789abcdef', k=8)),
                ''.join(random.choices('0123456789abcdef', k=4)),
                ''.join(random.choices('0123456789abcdef', k=4)),
                ''.join(random.choices('0123456789abcdef', k=4)),
                ''.join(random.choices('0123456789abcdef', k=12))
            ]
            return '-'.join(parts)
        else:
            # Short format from examples
            return ''.join(random.choices('0123456789abcdef', k=8)) + '-' + ''.join(random.choices('0123456789abcdef', k=4))
    
    def generate_machine_id(self):
        """Generate machine ID"""
        return str(self.generate_guid())
    
    def generate_vidar_hwid(self):
        """Generate HWID in Vidar format"""
        # Based on examples, format varies
        formats = [
            lambda: f"{''.join(random.choices('0123456789ABCDEF', k=17))}{random.randint(1, 9)}",
            lambda: f"{''.join(random.choices('0123456789ABCDEF', k=16))}{random.randint(1, 9)}"
        ]
        return random.choice(formats)()
    
    def get_timezone_offset(self, timezone_str):
        """Get timezone offset"""
        timezone_offsets = self.config['country']['timezones']
        
        for tz_name, offset in timezone_offsets.items():
            if tz_name in timezone_str:
                return offset
        
        return '0'
    
    def get_language_for_country(self, country):
        """Get language for country"""
        return self.config['country']['languages'].get(country, 'English (United States)')
    
    def generate_ip_for_country(self, country):
        """Generate IP for country"""
        ip_patterns = self.config['country']['ip_patterns']
        
        if country in ip_patterns:
            pattern = ip_patterns[country]
            
            # Some countries have static IPs in examples
            if 'static' in pattern:
                return pattern['static']
            
            # Generate based on pattern
            prefixes = pattern.get('prefixes', [])
            ranges = pattern.get('ranges', [])
            
            if prefixes:
                prefix = random.choice(prefixes)
                parts = [str(prefix)]
                for range_vals in ranges:
                    parts.append(str(random.randint(range_vals[0], range_vals[1])))
                return '.'.join(parts)
        
        # Default pattern
        default = ip_patterns['default']
        parts = []
        for range_vals in default['ranges']:
            parts.append(str(random.randint(range_vals[0], range_vals[1])))
        return '.'.join(parts)
    
    def get_cpu_cores(self, device_type):
        """Get CPU core count"""
        hardware_config = self.config['hardware']['cpu_cores']
        
        if device_type == 'Gaming_Rig':
            return random.choice(hardware_config['Gaming_Rig'])
        else:
            return hardware_config['default']
    
    def get_cpu_threads(self, device_type):
        """Get CPU thread count"""
        cores = self.get_cpu_cores(device_type)
        # Usually 2x cores for modern CPUs
        return cores * 2 if device_type == 'Gaming_Rig' else cores
    
    def get_sites_for_persona(self, persona):
        """Get relevant sites based on persona"""
        sites_config = self.config['sites']
        sites = sites_config['common'].copy()
        
        archetype = persona.get('PersonaArchetype', '')
        
        if 'Gaming' in archetype:
            sites.extend(sites_config['gaming'])
        
        if 'Student' in archetype:
            sites.extend(sites_config['student'])
        
        if 'Remote_Worker' in archetype or 'Corporate' in archetype:
            sites.extend(sites_config['corporate'])
        
        if persona.get('CryptoUser') != 'None':
            sites.extend(sites_config['crypto'])
        
        if persona.get('SocialMediaUser') == 'Heavy':
            sites.extend(sites_config['social_heavy'])
        
        return sites
    
    def generate_phone_number(self, country):
        """Generate phone number for country"""
        if country == 'US':
            return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"
        elif country == 'GB':
            return f"07{random.randint(700,999)} {random.randint(100000,999999)}"
        else:
            return f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(100,999)} {random.randint(1000,9999)}"
    
    def generate_address(self, persona):
        """Generate address for persona"""
        streets = ['Main St', 'Oak Ave', 'Elm St', 'Park Rd', 'First Ave', 'High St']
        return {
            'street': f"{random.randint(100,9999)} {random.choice(streets)}",
            'city': persona.get('City', 'Unknown'),
            'state': persona.get('State_Region', 'Unknown'),
            'zip': str(random.randint(10000,99999))
        }
    
    def generate_search_queries(self, persona, count):
        """Generate search queries based on persona"""
        search_config = self.config['search_queries']
        archetype = persona.get('PersonaArchetype', '')
        
        queries = search_config['base'].copy()
        
        if 'Gaming' in archetype:
            queries.extend(search_config['gaming'])
        
        if 'Student' in archetype:
            queries.extend(search_config['student'])
        
        if 'Corporate' in archetype or 'Small_Business' in archetype:
            queries.extend(search_config['corporate'])
        
        # Add image searches
        queries.extend(search_config['image'])
        
        random.shuffle(queries)
        return queries[:count]
    
    def generate_all_vidar_logs(self):
        """Generate Vidar logs for all selected personas"""
        generated_logs = []
        
        print(f"Starting Vidar stealer log generation...")
        print(f"Processing {len(self.personas)} Vidar-infected personas")
        print("-" * 50)
        
        for persona in self.personas:
            try:
                log_dir = self.generate_vidar_log(persona)
                generated_logs.append(log_dir)
            except Exception as e:
                print(f"Error generating log for {persona['PersonaID']}: {str(e)}")
                print(f"   Full traceback:")
                traceback.print_exc()
        
        print("-" * 50)
        print(f"Successfully generated {len(generated_logs)} Vidar stealer logs")
        return generated_logs


# Main execution
if __name__ == "__main__":
    # Initialize generator
    generator = VidarLogGenerator('personas.csv')
    
    # Generate all logs
    logs = generator.generate_all_vidar_logs()
    
    print(f"\nLogs saved to: {generator.output_base_dir}/")
