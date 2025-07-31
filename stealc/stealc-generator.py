#!/usr/bin/env python3
"""
Synthetic StealC Stealer Log Generator for DEFCON Red Team Village Workshop
Generates realistic but obviously fake stealer logs for educational purposes.

This generator reads personas from a CSV file and generates logs for personas
where the 'Infection' column contains 'StealC'. This ensures each persona is
infected by the correct stealer as specified in the CSV file.
"""

import csv
import hashlib
import json
import logging
import os
import random
import string
import traceback
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Persona:
    """Represents a user persona from the CSV."""
    persona_id: str
    first_name: str
    last_name: str
    email_personal: str
    email_work: str
    country: str
    city: str
    state_region: str
    timezone: str
    os: str
    device_type: str
    income_level: str
    primary_browser: str
    secondary_browser: str
    password_habits: str
    persona_archetype: str
    financial_value: str
    crypto_user: str
    social_media_user: str
    online_shopper: str
    business_access: str

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Persona':
        """Create a Persona instance from a CSV row."""
        return cls(
            persona_id=row['PersonaID'],
            first_name=row.get('FirstName', 'John'),
            last_name=row.get('LastName', 'Doe'),
            email_personal=row.get('EmailPersonal', 'user@example.fake'),
            email_work=row.get('EmailWork', ''),
            country=row.get('Country', 'US'),
            city=row.get('City', 'Unknown'),
            state_region=row.get('State_Region', 'Unknown'),
            timezone=row.get('Timezone', 'UTC'),
            os=row['OS'],
            device_type=row.get('DeviceType', 'Personal_Laptop'),
            income_level=row.get('IncomeLevel', 'Medium'),
            primary_browser=row.get('PrimaryBrowser', 'Chrome'),
            secondary_browser=row.get('SecondaryBrowser', 'None'),
            password_habits=row.get('PasswordHabits', 'Mixed'),
            persona_archetype=row.get('PersonaArchetype', 'General'),
            financial_value=row.get('FinancialValue', 'Medium'),
            crypto_user=row.get('CryptoUser', 'None'),
            social_media_user=row.get('SocialMediaUser', 'Light'),
            online_shopper=row.get('OnlineShopper', 'Light'),
            business_access=row.get('BusinessAccess', 'No')
        )


class ConfigurationManager:
    """Manages all configuration data from external files."""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all JSON configuration files from the config directory."""
        stealc_config_dir = self.config_dir / 'stealc'
        if not stealc_config_dir.exists():
            raise FileNotFoundError(f"StealC configuration directory '{stealc_config_dir}' not found.")
        
        for config_file in stealc_config_dir.glob('*.json'):
            config_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configs[config_name] = json.load(f)
                logger.info(f"Loaded stealc/{config_name}.json")
            except Exception as e:
                logger.error(f"Error loading {config_file}: {e}")
                raise
    
    def get(self, config_name: str, *keys, default=None):
        """Get a configuration value by name and nested keys."""
        try:
            value = self.configs.get(config_name)
            if value is None:
                logger.warning(f"Configuration '{config_name}' not found")
                return default
            
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    logger.warning(f"Cannot access key '{key}' in non-dict value")
                    return default
                    
                if value is None:
                    return default
                    
            return value
        except Exception as e:
            logger.error(f"Error accessing config {config_name}.{'.'.join(map(str, keys))}: {e}")
            return default


class BaseGenerator(ABC):
    """Abstract base class for content generators."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    @staticmethod
    def get_persona_seed(persona_id: str, suffix: str = "") -> int:
        """Generate consistent seed for persona-specific data."""
        seed_string = f"{persona_id}_{suffix}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    @abstractmethod
    def generate(self, persona: Persona) -> Any:
        """Generate content for the given persona."""
        pass


class TemplateRenderer:
    """Handles template rendering with variable substitution."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    def render(self, template_name: str, **kwargs) -> str:
        """Render a template with the given variables."""
        template = self.config.get('templates', template_name, default="")
        if not template:
            logger.warning(f"Template '{template_name}' not found")
            return ""
        
        # Simple variable substitution
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return template


class HardwareGenerator(BaseGenerator):
    """Generates hardware information for personas."""
    
    def generate(self, persona: Persona) -> Dict[str, str]:
        """Generate realistic hardware based on persona."""
        random.seed(self.get_persona_seed(persona.persona_id, 'hardware'))
        
        # Get hardware config for device type and income level
        hardware_config = self.config.get('hardware', persona.device_type, persona.income_level)
        if not hardware_config:
            # Fallback to default
            hardware_config = self.config.get('hardware', 'Personal_Laptop', 'Medium')
        
        return {
            'cpu': random.choice(hardware_config['cpu']),
            'gpu': random.choice(hardware_config['gpu']),
            'ram_mb': random.choice(hardware_config['ram_mb']),
            'resolution': random.choice(hardware_config['resolution']),
            'cores': random.choice(hardware_config['cores']),
            'threads': random.choice(hardware_config['threads'])
        }
    
    def generate_computer_name(self, device_type: str) -> str:
        """Generate computer name based on device type."""
        prefixes = self.config.get('hardware', 'computer_name_prefixes', device_type, 
                                  default=['DESKTOP'])
        prefix = random.choice(prefixes)
        
        # Sometimes add a suffix
        if random.random() > 0.5:
            suffixes = self.config.get('hardware', 'computer_name_suffixes', default=[])
            if suffixes:
                suffix = random.choice(suffixes)
                if '{number}' in suffix:
                    suffix = suffix.replace('{number}', str(random.randint(100, 999)))
                return f"{prefix}{suffix}"
        
        return prefix
    
    def generate_hwid(self) -> str:
        """Generate hardware ID."""
        chars = self.config.get('charsets', 'hwid', default='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        length = self.config.get('main', 'generator_settings', 'hwid_length', default=21)
        return ''.join(random.choices(chars, k=length))
    
    def is_laptop(self, device_type: str) -> bool:
        """Determine if device is a laptop."""
        laptop_types = self.config.get('hardware', 'laptop_device_types', 
                                      default=['Personal_Laptop', 'Business_Laptop'])
        return device_type in laptop_types


class NetworkGenerator:
    """Generates network-related information."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    def generate_ip_for_country(self, country: str) -> str:
        """Generate IP address based on country."""
        ip_generators = self.config.get('network', 'country_ip_generators')
        
        if country in ip_generators:
            generator = ip_generators[country]
            # Parse the generator string
            return self._execute_ip_generator(generator)
        
        # Default fallback
        return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    
    def _execute_ip_generator(self, generator: str) -> str:
        """Execute IP generator string."""
        # Replace random.choice and random.randint patterns
        import re
        
        # Handle random.choice([...])
        choice_pattern = r'random\.choice\(\[([\d,\s]+)\]\)'
        def replace_choice(match):
            values = [int(x.strip()) for x in match.group(1).split(',')]
            return str(random.choice(values))
        generator = re.sub(choice_pattern, replace_choice, generator)
        
        # Handle random.randint(min,max)
        randint_pattern = r'random\.randint\((\d+),(\d+)\)'
        def replace_randint(match):
            return str(random.randint(int(match.group(1)), int(match.group(2))))
        generator = re.sub(randint_pattern, replace_randint, generator)
        
        # Evaluate the expression safely (only contains numbers and dots now)
        return generator
    
    def get_timezone_offset(self, timezone_str: str) -> str:
        """Extract UTC offset from timezone string."""
        timezone_offsets = self.config.get('network', 'timezone_offsets', default={})
        
        # Try to extract from the string
        if 'UTC' in timezone_str or 'GMT' in timezone_str:
            import re
            match = re.search(r'[+-]\d+', timezone_str)
            if match:
                return match.group()
        
        # Check for known timezone names
        for tz_name, offset in timezone_offsets.items():
            if tz_name in timezone_str:
                return offset
        
        # Default
        return random.choice(['-8', '-7', '-6', '-5', '-4', '0', '1', '2', '3', '5'])
    
    def get_language_code(self, country: str) -> str:
        """Get language code for country."""
        language_codes = self.config.get('network', 'country_language_codes', default={})
        return language_codes.get(country, 'en-US')
    
    def get_language_name(self, country: str) -> str:
        """Get language name for country."""
        language_names = self.config.get('network', 'country_language_names', default={})
        return language_names.get(country, 'English (United States)')


class MarketingGenerator:
    """Generates marketing-related content."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    def generate_copyright_header(self) -> str:
        """Generate copyright.txt content."""
        random.seed(random.random())  # Different each time
        
        channels = self.config.get('marketing', 'channels', default=[])
        shops = self.config.get('marketing', 'shops', default=[])
        supports = self.config.get('marketing', 'supports', default=[])
        
        if not channels or not shops or not supports:
            return "STEALC STEALER\n"
        
        channel = random.choice(channels)
        shop = random.choice(shops)
        support = random.choice(supports)
        
        template = self.config.get('templates', 'copyright_header', default="")
        if template:
            return template.format(channel=channel, shop=shop, support=support)
        
        return f"""CL0UD INFO - {channel} | SH0P - {shop} | SUPP - {support}

----------------------------------------------------------------
CL0UD INFO - {channel} | SH0P - {shop} | SUPPORT - {support}

----------------------------------------------------------------

"""
    
    def generate_marketing_file(self) -> Tuple[str, str]:
        """Generate the random-named marketing file with ASCII art."""
        random.seed(random.random())
        
        # Generate random filename
        chars = self.config.get('charsets', 'filename', default='abcdefghijklmnopqrstuvwxyz')
        length_range = self.config.get('ranges', 'marketing_filename_length', 
                                      default={'min': 5, 'max': 12})
        filename_length = random.randint(length_range['min'], length_range['max'])
        filename = ''.join(random.choices(chars, k=filename_length)) + '.txt'
        
        # Sometimes just a simple ad
        if random.random() > 0.7:
            channels = self.config.get('marketing', 'channels', default=[])
            shops = self.config.get('marketing', 'shops', default=[])
            supports = self.config.get('marketing', 'supports', default=[])
            
            if channels and shops and supports:
                channel = random.choice(channels)
                shop = random.choice(shops)
                support = random.choice(supports)
                content = f"https://t.me/{channel[1:]} - channel | https://t.me/{support[1:]} - support | https://t.me/{shop[1:]} - shop\n"
            else:
                content = "STEALC STEALER\n"
        else:
            # Generate ASCII art
            content = self.generate_ascii_art()
        
        return filename, content
    
    def generate_ascii_art(self) -> str:
        """Generate StealC ASCII art advertisement."""
        channels = self.config.get('marketing', 'channels', default=[])
        shops = self.config.get('marketing', 'shops', default=[])
        supports = self.config.get('marketing', 'supports', default=[])
        
        template = self.config.get('templates', 'ascii_art', default="")
        if template and channels and shops and supports:
            channel = random.choice(channels)
            shop = random.choice(shops)
            support = random.choice(supports)
            return template.format(channel=channel, shop=shop, support=support)
        
        return "STEALC STEALER - POWERFUL NATIVE STEALER\n"


class SystemInfoGenerator(BaseGenerator):
    """Generates system_info.txt content."""
    
    def __init__(self, config: ConfigurationManager):
        super().__init__(config)
        self.hardware_generator = HardwareGenerator(config)
        self.network_generator = NetworkGenerator(config)
        self.template_renderer = TemplateRenderer(config)
    
    def generate(self, persona: Persona) -> str:
        """Generate system_info.txt content."""
        random.seed(self.get_persona_seed(persona.persona_id, 'system'))
        
        # Generate hardware
        hardware = self.hardware_generator.generate(persona)
        
        # Network info
        ip = self.network_generator.generate_ip_for_country(persona.country)
        timezone_offset = self.network_generator.get_timezone_offset(persona.timezone)
        language_code = self.network_generator.get_language_code(persona.country)
        language_name = self.network_generator.get_language_name(persona.country)
        
        # System info
        pc_name = self.hardware_generator.generate_computer_name(persona.device_type)
        is_laptop = 'TRUE' if self.hardware_generator.is_laptop(persona.device_type) else 'FALSE'
        hwid = self.hardware_generator.generate_hwid()
        
        # Execution path
        exec_path = self._generate_execution_path(persona)
        
        # Current time
        local_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        
        # GPU list
        gpu_list = self._generate_gpu_list(persona, hardware['gpu'])
        
        # Generate sections
        user_agents = self._generate_user_agents_section(persona)
        installed_apps = self._generate_installed_apps_section(persona)
        process_list = self._generate_process_list_section(persona)
        
        # Use template
        return self.template_renderer.render(
            'system_info',
            ip=ip,
            country=persona.country,
            hwid=hwid,
            os_version=persona.os,
            username=persona.first_name,
            pc_name=pc_name,
            local_time=local_time,
            timezone_offset=timezone_offset,
            language_code=language_code,
            language_name=language_name,
            is_laptop=is_laptop,
            exec_path=exec_path,
            cpu=hardware['cpu'],
            cores=hardware['cores'],
            threads=hardware['threads'],
            ram_mb=hardware['ram_mb'],
            resolution=hardware['resolution'],
            gpu_list=gpu_list,
            user_agents=user_agents,
            installed_apps=installed_apps,
            process_list=process_list
        )
    
    def _generate_execution_path(self, persona: Persona) -> str:
        """Generate execution path."""
        paths = self.config.get('main', 'execution_paths', default=[])
        if paths:
            path = random.choice(paths)
            return path.replace('{username}', persona.first_name)
        return f"C:\\Users\\{persona.first_name}\\AppData\\Local\\Temp\\Setup.exe"
    
    def _generate_gpu_list(self, persona: Persona, primary_gpu: str) -> str:
        """Generate GPU list in StealC format."""
        gpus = [f"\t\t-{primary_gpu}"]
        
        # Gaming rigs might have integrated + dedicated
        if persona.device_type == 'Gaming_Rig' and random.random() > 0.5:
            integrated_gpus = self.config.get('hardware', 'integrated_gpus', default=[])
            if integrated_gpus:
                gpus.append(f"\t\t-{random.choice(integrated_gpus)}")
        
        # Laptops sometimes list GPU multiple times
        elif 'Laptop' in persona.device_type:
            repeat_range = self.config.get('ranges', 'laptop_gpu_repeats', 
                                         default={'min': 1, 'max': 3})
            num_repeats = random.randint(repeat_range['min'], repeat_range['max'])
            for _ in range(num_repeats - 1):
                gpus.append(f"\t\t-{primary_gpu}")
        
        return '\n'.join(gpus)
    
    def _generate_user_agents_section(self, persona: Persona) -> str:
        """Generate User Agents section."""
        user_agents = []
        
        browser_versions = self.config.get('browsers', 'versions', default={})
        ua_templates = self.config.get('templates', 'user_agents', default={})
        
        # Add user agents for installed browsers
        browsers = []
        if persona.primary_browser and persona.primary_browser != 'None':
            browsers.append(persona.primary_browser)
        if persona.secondary_browser and persona.secondary_browser != 'None':
            browsers.append(persona.secondary_browser)
        
        for browser in browsers:
            if browser in browser_versions and browser in ua_templates:
                version = random.choice(browser_versions[browser])
                ua_template = ua_templates[browser]
                ua = ua_template.format(version=version)
                user_agents.append(f"\t{ua}")
        
        return '\n'.join(user_agents)
    
    def _generate_installed_apps_section(self, persona: Persona) -> str:
        """Generate Installed Apps section."""
        all_users_apps = []
        current_user_apps = []
        
        # Base Windows apps
        all_users_apps.extend(self.config.get('software', 'windows_base', default=[]))
        
        # Browser apps
        browser_apps = self.config.get('software', 'browsers', default={})
        if persona.primary_browser in browser_apps:
            all_users_apps.append(browser_apps[persona.primary_browser])
        if persona.secondary_browser in browser_apps:
            all_users_apps.append(browser_apps[persona.secondary_browser])
        
        # Device-specific apps
        device_apps = self.config.get('software', 'device_type', persona.device_type, default=[])
        all_users_apps.extend(device_apps)
        
        # Archetype-specific apps
        archetype_apps = self.config.get('software', 'archetype', persona.persona_archetype, default=[])
        all_users_apps.extend(archetype_apps)
        
        # Current user apps
        current_user_apps.extend(self.config.get('software', 'current_user_base', default=[]))
        
        # Conditional current user apps
        if 'Student' in persona.persona_archetype or persona.social_media_user == 'Heavy':
            current_user_apps.extend(self.config.get('software', 'current_user_social', default=[]))
        
        if 'Gaming' in persona.persona_archetype or 'Student' in persona.persona_archetype:
            current_user_apps.extend(self.config.get('software', 'current_user_creative', default=[]))
        
        # Limit and format
        max_all_users = self.config.get('ranges', 'installed_apps_all_users', 
                                       default={'min': 20, 'max': 40})
        all_users_apps = all_users_apps[:random.randint(max_all_users['min'], max_all_users['max'])]
        
        result = "All Users:\n"
        for app in all_users_apps:
            result += f"\t{app}\n"
        
        result += "Current User:\n"
        for app in current_user_apps:
            result += f"\t{app}\n"
        
        return result.rstrip()
    
    def _generate_process_list_section(self, persona: Persona) -> str:
        """Generate process list section."""
        processes = []
        
        # System processes
        processes.extend(self.config.get('processes', 'system', default=[]))
        
        # Multiple svchost instances
        svchost_range = self.config.get('ranges', 'svchost_count', 
                                       default={'min': 30, 'max': 50})
        for _ in range(random.randint(svchost_range['min'], svchost_range['max'])):
            processes.append("svchost.exe")
        
        # Browser processes
        browser_processes = self.config.get('processes', 'browsers', default={})
        
        if 'Chrome' in persona.primary_browser or 'Chrome' in persona.secondary_browser:
            if 'Chrome' in browser_processes:
                count_range = browser_processes['Chrome']
                for _ in range(random.randint(count_range['min'], count_range['max'])):
                    processes.append("chrome.exe")
        
        if 'Edge' in persona.primary_browser or 'Edge' in persona.secondary_browser:
            if 'Edge' in browser_processes:
                count_range = browser_processes['Edge']
                for _ in range(random.randint(count_range['min'], count_range['max'])):
                    processes.append("msedge.exe")
                # Edge WebView processes
                webview_range = browser_processes.get('EdgeWebView', {'min': 3, 'max': 6})
                for _ in range(random.randint(webview_range['min'], webview_range['max'])):
                    processes.append("msedgewebview2.exe")
        
        if 'Firefox' in persona.primary_browser or 'Firefox' in persona.secondary_browser:
            processes.append("firefox.exe")
        
        # Archetype-specific processes
        archetype_processes = self.config.get('processes', 'archetype', 
                                            persona.persona_archetype, default=[])
        processes.extend(archetype_processes)
        
        # Social media processes
        if persona.social_media_user == 'Heavy':
            social_processes = self.config.get('processes', 'social_media', default=[])
            processes.extend(random.sample(social_processes, 
                           min(len(social_processes), random.randint(1, 3))))
        
        # Add the malware itself
        processes.append("explorer.exe")  # Second instance
        
        # Shuffle non-system processes
        system_count = len(self.config.get('processes', 'system', default=[]))
        if len(processes) > system_count:
            system_procs = processes[:system_count]
            other_procs = processes[system_count:]
            random.shuffle(other_procs)
            processes = system_procs + other_procs
        
        # Format with tabs
        return '\n'.join([f"\t{proc}" for proc in processes])


class BrowserDataGenerator:
    """Generates browser-related data."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
        self.template_renderer = TemplateRenderer(config)
    
    @staticmethod
    def get_persona_seed(persona_id: str, suffix: str = "") -> int:
        """Generate consistent seed for persona-specific data."""
        seed_string = f"{persona_id}_{suffix}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    def get_browser_profiles(self, persona: Persona) -> List[Tuple[str, str]]:
        """Get browser profiles for persona."""
        profiles = []
        
        # Primary browser
        if persona.primary_browser and persona.primary_browser != 'None':
            browser_name = self._get_browser_full_name(persona.primary_browser)
            profiles.append((browser_name, 'Default'))
            
            # Heavy users might have multiple profiles
            if (persona.social_media_user == 'Heavy' or persona.business_access == 'Yes') and \
               persona.primary_browser == 'Chrome' and random.random() > 0.5:
                profile_range = self.config.get('ranges', 'chrome_profiles', 
                                              default={'min': 1, 'max': 5})
                profile_num = random.randint(profile_range['min'], profile_range['max'])
                profiles.append((browser_name, f'Profile {profile_num}'))
        
        # Secondary browser
        if persona.secondary_browser and persona.secondary_browser != 'None':
            browser_name = self._get_browser_full_name(persona.secondary_browser)
            if persona.secondary_browser == 'Firefox':
                # Firefox uses random profile names
                profile_name = self._generate_firefox_profile_name()
                profiles.append((browser_name, profile_name))
            else:
                profiles.append((browser_name, 'Default'))
        
        return profiles if profiles else [('Google Chrome', 'Default')]
    
    def _get_browser_full_name(self, browser: str) -> str:
        """Get full browser name for directory."""
        browser_names = self.config.get('browsers', 'full_names', default={})
        return browser_names.get(browser, browser)
    
    def _generate_firefox_profile_name(self) -> str:
        """Generate Firefox profile name format."""
        chars = self.config.get('charsets', 'firefox_profile', 
                               default='abcdefghijklmnopqrstuvwxyz0123456789')
        prefix_length = self.config.get('main', 'generator_settings', 
                                       'firefox_profile_prefix_length', default=8)
        prefix = ''.join(random.choices(chars, k=prefix_length))
        
        suffixes = self.config.get('browsers', 'firefox_profile_suffixes', 
                                  default=['default-release'])
        return f"{prefix}.{random.choice(suffixes)}"
    
    def generate_autofill(self, persona: Persona, browser_profile: str) -> str:
        """Generate autofill data for a browser profile."""
        random.seed(self.get_persona_seed(persona.persona_id, f'autofill_{browser_profile}'))
        
        entries = []
        
        # Get form fields
        form_fields = self._generate_form_fields(persona)
        
        # Number of entries
        entry_range = self.config.get('ranges', 'autofill_entries', 
                                    default={'min': 30, 'max': 80})
        num_entries = random.randint(entry_range['min'], entry_range['max'])
        
        # Mix of form fields (70%)
        field_names = list(form_fields.keys())
        for _ in range(int(num_entries * 0.7)):
            field = random.choice(field_names)
            value = form_fields[field]
            entries.append(f"{field} {value}")
        
        # Search queries (30%)
        search_queries = self._generate_search_queries(persona, int(num_entries * 0.3))
        for query in search_queries:
            entries.append(f"q {query}")
        
        random.shuffle(entries)
        return '\n'.join(entries) + '\n'
    
    def generate_cookies(self, persona: Persona, browser_profile: str) -> Tuple[str, List[str]]:
        """Generate cookies for a browser profile."""
        random.seed(self.get_persona_seed(persona.persona_id, f'cookies_{browser_profile}'))
        
        cookies = []
        sites = self._get_sites_for_persona(persona)
        cookie_domains = []
        
        # Number of cookies
        cookie_range = self.config.get('ranges', 'cookie_count', 
                                     default={'min': 50, 'max': 100})
        num_cookies = random.randint(cookie_range['min'], cookie_range['max'])
        
        for _ in range(num_cookies):
            site = random.choice(sites)
            domain = f".{site}" if not site.startswith('.') else site
            cookie_domains.append(domain)
            
            # Cookie parameters
            include_subdomains = 'TRUE' if random.random() > 0.2 else 'FALSE'
            path = '/'
            secure = 'TRUE' if 'https' in site or random.random() > 0.3 else 'FALSE'
            
            # Expiry
            expiry_range = self.config.get('ranges', 'cookie_expiry_days', 
                                         default={'min': 30, 'max': 730})
            expiry_days = random.randint(expiry_range['min'], expiry_range['max'])
            expiry = int((datetime.now() + timedelta(days=expiry_days)).timestamp())
            
            # Cookie name and value
            cookie_name, cookie_value = self._generate_cookie_data(site)
            
            # Special cases
            if site == 'accounts.google.com':
                domain = site  # No leading dot
                include_subdomains = 'FALSE'
            
            cookie_line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{cookie_name}\t{cookie_value}"
            cookies.append(cookie_line)
        
        return '\n'.join(cookies) + '\n', cookie_domains
    
    def generate_history(self, persona: Persona, browser_profile: str) -> str:
        """Generate browsing history."""
        random.seed(self.get_persona_seed(persona.persona_id, f'history_{browser_profile}'))
        
        sites = self._get_sites_for_persona(persona)
        history_entries = []
        
        # Number of entries
        history_range = self.config.get('ranges', 'history_entries', 
                                      default={'min': 50, 'max': 150})
        num_entries = random.randint(history_range['min'], history_range['max'])
        
        url_patterns = self.config.get('browsers', 'url_patterns', default={})
        
        for _ in range(num_entries):
            site = random.choice(sites)
            
            # Generate URL based on site
            if site in url_patterns:
                url = self._generate_url_from_pattern(site, url_patterns[site], persona)
            else:
                url = f"https://{site}/"
                if random.random() > 0.7:
                    # Add path
                    paths = self.config.get('browsers', 'common_paths', 
                                          default=['login', 'account', 'profile'])
                    url += random.choice(paths)
            
            history_entries.append(url)
        
        return '\n'.join(history_entries) + '\n'
    
    def generate_passwords(self, persona: Persona) -> str:
        """Generate passwords.txt in StealC format."""
        random.seed(self.get_persona_seed(persona.persona_id, 'passwords'))
        
        entries = []
        
        # Get browser profiles
        browser_profiles = self.get_browser_profiles(persona)
        
        # Generate passwords
        passwords = self._generate_passwords_for_persona(persona)
        
        # Generate login entries
        sites = self._get_sites_for_persona(persona)
        password_range = self.config.get('ranges', 'password_entries', 
                                       default={'min': 20, 'max': 50})
        num_passwords = random.randint(password_range['min'], password_range['max'])
        
        for _ in range(num_passwords):
            site = random.choice(sites)
            browser, profile = random.choice(browser_profiles)
            
            # Generate login
            login = self._generate_login_for_site(persona, site)
            
            # Pick password
            if persona.password_habits == 'Reuses_Passwords':
                password = passwords[0]  # Always use first
            else:
                password = random.choice(passwords)
            
            # Use template
            entry = self.template_renderer.render(
                'password_entry',
                browser=browser,
                profile=profile,
                site=site,
                path='login' if random.random() > 0.5 else '',
                login=login,
                password=password
            )
            entries.append(entry)
        
        return '\n'.join(entries)
    
    def _generate_form_fields(self, persona: Persona) -> Dict[str, str]:
        """Generate form field data."""
        phone = self._generate_phone_number(persona.country)
        address = self._generate_address(persona)
        
        fields = {
            'name': f"{persona.first_name} {persona.last_name}",
            'fname': persona.first_name,
            'lname': persona.last_name,
            'email': persona.email_personal,
            'phone': phone,
            'tel': phone,
            'address': address['street'],
            'address1': address['street'],
            'city': address['city'],
            'state': address['state'],
            'zip': address['zip'],
            'zipcode': address['zip'],
            'country': persona.country,
            'cardnumber': self._generate_credit_card_number(),
            'cardname': f"{persona.first_name} {persona.last_name}",
            'cardexp': f"{random.randint(1,12):02d}/{random.randint(25,29)}",
            'cardExpiry': f"{random.randint(1,12):02d} / {random.randint(25,29)}",
            'cvv': str(random.randint(100, 999)),
            'billing_state': address['state'],
            'shipping_address': address['street'],
            'username': persona.email_personal.split('@')[0] if '@' in persona.email_personal else persona.first_name.lower()
        }
        
        return fields
    
    def _generate_phone_number(self, country: str) -> str:
        """Generate phone number for country."""
        formats = self.config.get('network', 'phone_formats', default={})
        if country in formats:
            return self._format_phone(formats[country])
        return f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(100,999)} {random.randint(1000,9999)}"
    
    def _format_phone(self, format_str: str) -> str:
        """Format phone number from template."""
        # Replace {min-max} patterns
        import re
        pattern = r'\{(\d+)-(\d+)\}'
        def replace_range(match):
            min_val = int(match.group(1))
            max_val = int(match.group(2))
            return str(random.randint(min_val, max_val))
        return re.sub(pattern, replace_range, format_str)
    
    def _generate_address(self, persona: Persona) -> Dict[str, str]:
        """Generate address for persona."""
        streets = self.config.get('network', 'street_names', default=['Main St'])
        street_range = self.config.get('ranges', 'street_number', 
                                     default={'min': 100, 'max': 9999})
        
        return {
            'street': f"{random.randint(street_range['min'], street_range['max'])} {random.choice(streets)}",
            'city': persona.city,
            'state': persona.state_region,
            'zip': str(random.randint(10000, 99999))
        }
    
    def _generate_credit_card_number(self) -> str:
        """Generate fake credit card number."""
        prefixes = self.config.get('main', 'credit_card_prefixes', 
                                 default={'visa': '4', 'mastercard': '5', 'amex': '37', 'discover': '6011'})
        prefix = random.choice(list(prefixes.values()))
        
        if prefix == '37':  # Amex is 15 digits
            remaining = 15 - len(prefix)
        else:  # Others are 16 digits
            remaining = 16 - len(prefix)
        
        return prefix + ''.join([str(random.randint(0,9)) for _ in range(remaining)])
    
    def _generate_search_queries(self, persona: Persona, count: int) -> List[str]:
        """Generate search queries based on persona."""
        # Base queries
        queries = self.config.get('browsers', 'search_queries', 'base', default=[]).copy()
        
        # Archetype-specific queries
        archetype_queries = self.config.get('browsers', 'search_queries', 
                                          persona.persona_archetype, default=[])
        queries.extend(archetype_queries)
        
        # Crypto queries
        if persona.crypto_user != 'None':
            crypto_queries = self.config.get('browsers', 'search_queries', 'crypto', default=[])
            queries.extend(crypto_queries)
        
        random.shuffle(queries)
        return queries[:count]
    
    def _get_sites_for_persona(self, persona: Persona) -> List[str]:
        """Get relevant sites based on persona."""
        # Common sites
        sites = self.config.get('websites', 'common_sites', default=[]).copy()
        
        # Archetype sites
        archetype_sites = self.config.get('websites', 'archetype_sites', 
                                        persona.persona_archetype, default=[])
        sites.extend(archetype_sites)
        
        # Crypto sites
        if persona.crypto_user != 'None':
            crypto_sites = self.config.get('websites', 'crypto_sites', default=[])
            sites.extend(crypto_sites)
        
        # Banking sites
        if persona.financial_value == 'High':
            banking_sites = self.config.get('websites', 'banking_sites', default=[])
            sites.extend(banking_sites)
        
        return sites
    
    def _generate_cookie_data(self, site: str) -> Tuple[str, str]:
        """Generate cookie name and value for site."""
        # Site-specific cookies
        site_cookies = self.config.get('browsers', 'site_specific_cookies', default={})
        
        for pattern, cookie_config in site_cookies.items():
            if pattern in site:
                names = cookie_config.get('names', ['session'])
                name = random.choice(names)
                
                # Generate value based on type
                if 'value_type' in cookie_config:
                    value_type = cookie_config['value_type']
                    if value_type == 'numeric':
                        value_range = cookie_config.get('range', {'min': 100000000, 'max': 999999999})
                        value = str(random.randint(value_range['min'], value_range['max']))
                    elif value_type == 'special':
                        patterns = cookie_config.get('patterns', [])
                        if patterns:
                            pattern = random.choice(patterns)
                            value = pattern.replace('{number}', str(random.randint(100, 999)))
                        else:
                            value = self._generate_cookie_value()
                    else:
                        value = self._generate_cookie_value()
                else:
                    value = self._generate_cookie_value()
                
                return name, value
        
        # Default cookies
        default_names = self.config.get('browsers', 'default_cookie_names', 
                                      default=['session_id', 'auth_token'])
        return random.choice(default_names), self._generate_cookie_value()
    
    def _generate_cookie_value(self) -> str:
        """Generate a realistic cookie value."""
        value_types = self.config.get('browsers', 'cookie_value_types', default=[])
        
        if not value_types or random.random() < 0.25:
            # Default pattern
            chars = string.ascii_letters + string.digits
            length = random.randint(20, 60)
            return ''.join(random.choices(chars, k=length))
        
        value_type = random.choice(value_types)
        
        if value_type == 'alphanumeric':
            chars = string.ascii_letters + string.digits
            length = random.randint(20, 60)
            return ''.join(random.choices(chars, k=length))
        elif value_type == 'alphanumeric_special':
            chars = string.ascii_letters + string.digits + '-_'
            length = random.randint(30, 80)
            return ''.join(random.choices(chars, k=length))
        elif value_type == 'md5':
            return hashlib.md5(str(random.random()).encode()).hexdigest()
        elif value_type == 'base64':
            data = str(random.random()).encode()
            return base64.b64encode(data).decode().strip('=')
        else:
            # Fallback
            return ''.join(random.choices(string.ascii_letters + string.digits, k=40))
    
    def _generate_url_from_pattern(self, site: str, patterns: List[str], persona: Persona) -> str:
        """Generate URL from pattern list."""
        pattern = random.choice(patterns)
        
        # Replace placeholders
        url = pattern.replace('{site}', site)
        
        if '{video_id}' in url:
            chars = string.ascii_letters + string.digits + '-_'
            video_id = ''.join(random.choices(chars, k=11))
            url = url.replace('{video_id}', video_id)
        
        if '{list_id}' in url:
            list_id = self._generate_youtube_list_id()
            url = url.replace('{list_id}', list_id)
        
        if '{username}' in url:
            usernames = self.config.get('browsers', 'social_usernames', default=['user123'])
            url = url.replace('{username}', random.choice(usernames))
        
        if '{search_query}' in url:
            queries = self._generate_search_queries(persona, 5)
            if queries:
                query = random.choice(queries).replace(' ', '+')
                url = url.replace('{search_query}', query)
        
        if '{subreddit}' in url:
            subreddits = self.config.get('browsers', 'subreddits', default=['AskReddit'])
            url = url.replace('{subreddit}', random.choice(subreddits))
        
        return url
    
    def _generate_youtube_list_id(self) -> str:
        """Generate YouTube playlist ID."""
        chars = string.ascii_letters + string.digits
        date = datetime.now().strftime('%d%m%Y')
        random_part = ''.join(random.choices(chars, k=12))
        return f"PQ{date}{random_part}"
    
    def _generate_passwords_for_persona(self, persona: Persona) -> List[str]:
        """Generate password list for persona."""
        password_patterns = self.config.get('passwords', persona.password_habits, default=[])
        
        if not password_patterns:
            # Default patterns
            password_patterns = ["{first_name}{year}!"]
        
        passwords = []
        
        if persona.password_habits == 'Reuses_Passwords':
            # Generate one main password
            pattern = password_patterns[0]
            password = self._format_password_pattern(pattern, persona)
            passwords = [password] * 10
        else:
            # Generate variety
            for pattern in password_patterns:
                password = self._format_password_pattern(pattern, persona)
                passwords.append(password)
            
            # Add some random strong passwords
            if persona.password_habits == 'Good_Hygiene':
                for _ in range(10):
                    chars = string.ascii_letters + string.digits + '!@#$%^&*'
                    length = random.randint(12, 20)
                    passwords.append(''.join(random.choices(chars, k=length)))
        
        return passwords
    
    def _format_password_pattern(self, pattern: str, persona: Persona) -> str:
        """Format password from pattern."""
        password = pattern
        password = password.replace('{first_name}', persona.first_name)
        password = password.replace('{last_name}', persona.last_name)
        password = password.replace('{year}', str(random.randint(2020, 2024)))
        password = password.replace('{number}', str(random.randint(100, 999)))
        
        if '{FirstLower}' in password:
            password = password.replace('{FirstLower}', persona.first_name.lower())
        if '{LastLower}' in password:
            password = password.replace('{LastLower}', persona.last_name.lower())
        
        return password
    
    def _generate_login_for_site(self, persona: Persona, site: str) -> str:
        """Generate login username for site."""
        # Use email for most sites
        if random.random() > 0.3 and persona.email_personal:
            return persona.email_personal
        
        # Use work email for professional sites
        if persona.email_work and any(prof in site for prof in ['linkedin', 'slack']):
            return persona.email_work
        
        # Generate username
        return f"{persona.first_name.lower()}{random.randint(100, 999)}"


class ApplicationDataGenerator:
    """Generates application-specific data."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    @staticmethod
    def get_persona_seed(persona_id: str, suffix: str = "") -> int:
        """Generate consistent seed for persona-specific data."""
        seed_string = f"{persona_id}_{suffix}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    def generate_discord_tokens(self, persona: Persona) -> Optional[str]:
        """Generate Discord tokens if applicable."""
        random.seed(self.get_persona_seed(persona.persona_id, 'discord'))
        
        # Discord probability by archetype
        discord_probability = self.config.get('applications', 'discord_probability', default={})
        
        include_discord = False
        if persona.persona_archetype in discord_probability:
            include_discord = random.random() < discord_probability[persona.persona_archetype]
        elif persona.social_media_user == 'Heavy':
            include_discord = random.random() < 0.5
        else:
            include_discord = random.random() < 0.2
        
        if not include_discord:
            return None
        
        tokens = []
        token_range = self.config.get('ranges', 'discord_tokens', default={'min': 1, 'max': 2})
        num_tokens = random.randint(token_range['min'], token_range['max'])
        
        for _ in range(num_tokens):
            # Modern Discord token format
            user_id = random.randint(100000000000000000, 999999999999999999)
            user_id_b64 = base64.b64encode(str(user_id).encode()).decode().strip('=')
            
            timestamp_chars = string.ascii_letters + string.digits + '-_'
            timestamp = ''.join(random.choices(timestamp_chars, k=6))
            
            hmac_length = self.config.get('main', 'generator_settings', 'discord_hmac_length', default=27)
            hmac = ''.join(random.choices(timestamp_chars, k=hmac_length))
            
            token = f"{user_id_b64}.{timestamp}.{hmac}"
            tokens.append(token)
        
        return '\n'.join(tokens) + '\n'
    
    def generate_steam_data(self, persona: Persona) -> Optional[Dict[str, Any]]:
        """Generate Steam configuration and tokens."""
        if 'Gaming' not in persona.persona_archetype:
            steam_probability = self.config.get('applications', 'steam_probability', 'default', default=0.3)
        else:
            steam_probability = self.config.get('applications', 'steam_probability', 'gaming', default=0.7)
        
        if random.random() > steam_probability:
            return None
        
        random.seed(self.get_persona_seed(persona.persona_id, 'steam'))
        
        result = {
            'config_files': self._generate_steam_config(persona),
            'token': self._generate_steam_token(persona)
        }
        
        return result
    
    def _generate_steam_config(self, persona: Persona) -> Dict[str, Any]:
        """Generate Steam configuration files."""
        steam_id_range = self.config.get('ranges', 'steam_id', default={'min': 76561190000000000, 'max': 76561199999999999})
        steam_id = random.randint(steam_id_range['min'], steam_id_range['max'])
        username = f"{persona.first_name.lower()}{random.randint(100, 999)}"
        
        # Generate loginusers.vdf
        loginusers_template = self.config.get('templates', 'steam_loginusers', default="")
        if loginusers_template:
            loginusers = loginusers_template.format(
                steam_id=steam_id,
                username=username,
                persona_name=persona.first_name,
                timestamp=int(datetime.now().timestamp())
            )
        else:
            loginusers = f'"users"\n{{\n    "{steam_id}"\n    {{\n        "AccountName"        "{username}"\n    }}\n}}\n'
        
        # Generate config.vdf
        config_template = self.config.get('templates', 'steam_config', default="")
        if config_template:
            config = config_template
        else:
            config = '"InstallConfigStore"\n{\n    "Software"\n    {\n        "Valve"\n        {\n            "Steam"\n            {\n            }\n        }\n    }\n}\n'
        
        # Generate ssfn files
        ssfn_files = []
        ssfn_range = self.config.get('ranges', 'steam_ssfn_count', default={'min': 1, 'max': 2})
        for _ in range(random.randint(ssfn_range['min'], ssfn_range['max'])):
            ssfn_id_length = self.config.get('main', 'generator_settings', 'steam_ssfn_id_length', default=15)
            ssfn_name = f"ssfn{random.randint(10**(ssfn_id_length-1), 10**ssfn_id_length-1)}"
            ssfn_size_range = self.config.get('ranges', 'steam_ssfn_size', default={'min': 100, 'max': 200})
            ssfn_content = b'\x00' * random.randint(ssfn_size_range['min'], ssfn_size_range['max'])
            ssfn_files.append((ssfn_name, ssfn_content))
        
        # Dialog resolutions
        dialog_resolutions = self.config.get('applications', 'steam_dialog_resolutions', default=[])
        
        return {
            'loginusers.vdf': loginusers,
            'config.vdf': config,
            'ssfn_files': ssfn_files,
            'dialog_resolutions': dialog_resolutions,
            'libraryfolders.vdf': '"LibraryFolders"\n{\n\t"0"\t"C:\\\\Program Files (x86)\\\\Steam"\n}\n'
        }
    
    def _generate_steam_token(self, persona: Persona) -> str:
        """Generate Steam OAuth token."""
        # JWT header
        header = base64.b64encode(b'{"typ":"JWT","alg":"EdDSA"}').decode().strip('=')
        
        # Payload
        steam_id_range = self.config.get('ranges', 'steam_id', default={'min': 76561190000000000, 'max': 76561199999999999})
        steam_id = random.randint(steam_id_range['min'], steam_id_range['max'])
        issued_at = int(datetime.now().timestamp())
        expires = issued_at + (365 * 24 * 60 * 60)  # 1 year
        
        payload = {
            "iss": f"r:{self._generate_steam_claim_id()}",
            "sub": str(steam_id),
            "aud": ["machine"],
            "exp": expires,
            "nbf": issued_at - 86400,
            "iat": issued_at,
            "jti": self._generate_steam_claim_id(),
            "oat": issued_at,
            "rt_exp": expires + 86400,
            "per": 0,
            "ip_subject": "127.0.0.1",  # Placeholder
            "ip_confirmer": "127.0.0.1"
        }
        
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().strip('=')
        
        # Signature
        sig_length = self.config.get('main', 'generator_settings', 'steam_signature_length', default=86)
        signature = ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=sig_length))
        
        return f"{header}.{payload_b64}.{signature}"
    
    def _generate_steam_claim_id(self) -> str:
        """Generate Steam claim ID format."""
        # Format: XY##_##FY#####_HEXHEX
        part1 = f"{random.randint(1, 9)}{random.choice('ABCDEF')}{random.randint(10, 99)}"
        part2 = f"{random.randint(20, 24)}F{random.randint(70000, 79999)}"
        part3 = ''.join(random.choices('0123456789ABCDEF', k=6))
        return f"{part1}_{part2}_{part3}"
    
    def generate_google_tokens(self, persona: Persona, browser_profile: str) -> Optional[str]:
        """Generate Google OAuth tokens."""
        random.seed(self.get_persona_seed(persona.persona_id, f'tokens_{browser_profile}'))
        
        # Only generate if persona uses Gmail
        if 'gmail' not in persona.email_personal and 'gmail' not in persona.email_work:
            return None
        
        tokens = []
        token_range = self.config.get('ranges', 'google_tokens', default={'min': 1, 'max': 3})
        num_tokens = random.randint(token_range['min'], token_range['max'])
        
        prefixes = self.config.get('applications', 'google_token_prefixes', 
                                 default=['1//03', '1//04', '1//09', '1//0g'])
        
        for _ in range(num_tokens):
            prefix = random.choice(prefixes)
            
            # Token body
            token_length_range = self.config.get('ranges', 'google_token_length', 
                                               default={'min': 80, 'max': 120})
            token_length = random.randint(token_length_range['min'], token_length_range['max'])
            chars = string.ascii_letters + string.digits + '-_'
            token_body = ''.join(random.choices(chars, k=token_length))
            
            # User ID
            user_id = str(random.randint(100000000000000000, 999999999999999999))
            
            token = f"{prefix}{token_body}:{user_id}"
            tokens.append(token)
        
        return '\n'.join(tokens) + '\n'
    
    def generate_telegram_data(self, persona: Persona) -> Optional[Dict[str, bytes]]:
        """Generate Telegram tdata directory structure."""
        if persona.social_media_user != 'Heavy':
            return None
        
        telegram_probability = self.config.get('applications', 'telegram_probability', 
                                             'heavy_user', default=0.5)
        if random.random() > telegram_probability:
            return None
        
        random.seed(self.get_persona_seed(persona.persona_id, 'telegram'))
        
        files = {}
        
        # Generate file names and sizes from config
        file_configs = self.config.get('applications', 'telegram_files', default={})
        for filename, size_range in file_configs.items():
            if isinstance(size_range, dict) and 'min' in size_range and 'max' in size_range:
                size = random.randint(size_range['min'], size_range['max'])
            else:
                size = 100  # Default
            files[filename] = b'\x00' * size
        
        return files
    
    def generate_outlook_accounts(self, persona: Persona) -> Optional[str]:
        """Generate Outlook accounts.txt."""
        random.seed(self.get_persona_seed(persona.persona_id, 'outlook'))
        
        # Check if persona uses Outlook
        outlook_domains = self.config.get('applications', 'outlook_domains', 
                                        default=['outlook.com', 'hotmail.com', 'live.com'])
        
        email = persona.email_personal or persona.email_work
        if not email or not any(domain in email for domain in outlook_domains):
            return None
        
        accounts = []
        
        # Primary account template
        account_template = self.config.get('templates', 'outlook_account', default="")
        if account_template:
            mini_uid = random.randint(-999999999, -100000000)
            account = account_template.format(
                mini_uid=mini_uid,
                email=email,
                random_char=chr(random.randint(192, 255))
            )
            accounts.append(account)
        
        # Sometimes add archive
        if random.random() > 0.6:
            archive_template = self.config.get('templates', 'outlook_archive', default="")
            if archive_template:
                mini_uid = random.randint(-999999999, -100000000)
                archive = archive_template.format(mini_uid=mini_uid)
                accounts.append(archive)
        
        return '\n'.join(accounts) if accounts else None
    
    def generate_crypto_wallet(self, wallet_type: str) -> Dict[str, bytes]:
        """Generate crypto wallet data."""
        wallet_files = self.config.get('applications', 'crypto_wallet_files', wallet_type, default={})
        
        files = {}
        for filename, content_type in wallet_files.items():
            if content_type == 'empty':
                files[filename] = b''
            elif content_type == 'manifest':
                files[filename] = b'MANIFEST-000001\n'
            elif content_type == 'log_current':
                files[filename] = f"{datetime.now().strftime('%Y/%m/%d-%H:%M:%S.%f')[:-3]} Recovering log #3\n".encode()
            elif content_type == 'log_old':
                files[filename] = f"{(datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d-%H:%M:%S.%f')[:-3]} Recovering log #1\n".encode()
            elif isinstance(content_type, dict) and 'size' in content_type:
                files[filename] = b'\x00' * content_type['size']
            else:
                files[filename] = b''
        
        # Add numbered log file
        if wallet_type in ['MetaMask', 'Binance Wallet']:
            log_range = self.config.get('ranges', 'wallet_log_number', 
                                      default={'min': 100000, 'max': 999999})
            log_num = random.randint(log_range['min'], log_range['max'])
            files[f'{log_num:06d}.log'] = b''
        
        return files


class StealCLogGenerator:
    """Main generator class for StealC stealer logs.
    
    This generator reads personas from a CSV file and generates logs for personas
    marked with 'StealC' in the Infection column.
    """
    
    def __init__(self, csv_file: str, exclude_ids: Optional[List[str]] = None, 
                 sample_size: int = 24, config_dir: str = 'config'):
        """Initialize the StealC log generator.
        
        Args:
            csv_file: Path to personas CSV file with Infection column
            exclude_ids: Optional list of PersonaIDs to exclude
            sample_size: Maximum number of personas to process (default: 24)
            config_dir: Configuration directory path (default: 'config')
        """
        self.config = ConfigurationManager(config_dir)
        self.personas = self._load_windows_personas(csv_file, exclude_ids, sample_size)
        self.output_base_dir = self.config.get('main', 'output_directory', default='stealc_logs')
        self._initialize_generators()
    
    def _load_windows_personas(self, csv_file: str, exclude_ids: Optional[List[str]], 
                              sample_size: int) -> List[Persona]:
        """Load Windows personas marked for StealC infection."""
        stealc_personas = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check if Infection column exists
                fieldnames = reader.fieldnames
                if 'Infection' not in fieldnames:
                    logger.warning("No 'Infection' column found in CSV. Looking for 'Stealer' or 'InfectedBy' column.")
                    infection_column = None
                    for col in ['Stealer', 'InfectedBy', 'Malware']:
                        if col in fieldnames:
                            infection_column = col
                            break
                    if not infection_column:
                        raise ValueError("No infection column found. Expected 'Infection', 'Stealer', 'InfectedBy', or 'Malware'")
                else:
                    infection_column = 'Infection'
                
                # Read personas infected by StealC
                for row in reader:
                    infection_value = row.get(infection_column, '').strip().lower()
                    if infection_value == 'stealc':
                        # Verify it's a Windows user (StealC only infects Windows)
                        if 'Windows' not in row.get('OS', ''):
                            logger.warning(f"Persona {row['PersonaID']} marked for StealC but has OS: {row.get('OS')}. Skipping.")
                            continue
                        stealc_personas.append(Persona.from_csv_row(row))
                        
                        # Apply sample_size limit if we have enough
                        if len(stealc_personas) >= sample_size:
                            break
            
            logger.info(f"Found {len(stealc_personas)} personas marked for StealC infection")
            
            if not stealc_personas:
                logger.warning("No personas found with StealC infection. Check the 'Infection' column in your CSV.")
                logger.warning("Make sure personas are marked with 'StealC' (case-insensitive) in the Infection column.")
            
            # Exclude any explicitly provided IDs
            if exclude_ids and stealc_personas:
                stealc_personas = [p for p in stealc_personas if p.persona_id not in exclude_ids]
                logger.info(f"After excluding provided IDs: {len(stealc_personas)} personas remain")
            
            # Log selected personas
            if stealc_personas:
                self._log_selected_personas(stealc_personas)
            
            return stealc_personas
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            raise
    
    def _log_selected_personas(self, personas: List[Persona]):
        """Log and save personas marked for StealC."""
        print("\n" + "="*50)
        print(f"FOUND {len(personas)} PERSONAS MARKED FOR STEALC:")
        print("="*50)
        print("PersonaID | First Name | Last Name | Archetype")
        print("-"*50)
        for p in personas:
            print(f"{p.persona_id} | {p.first_name} | {p.last_name} | {p.persona_archetype}")
        print("="*50)
        
        # Save to file for reference
        with open('stealc_infected_personas.txt', 'w') as f:
            f.write("PersonaIDs marked for StealC infection:\n")
            f.write(",".join([p.persona_id for p in personas]))
            f.write("\n\nDetails:\n")
            for p in personas:
                f.write(f"{p.persona_id}: {p.first_name} {p.last_name} ({p.persona_archetype})\n")
            f.write(f"\n\nTotal: {len(personas)} personas\n")
    
    def _initialize_generators(self):
        """Initialize all content generators."""
        self.system_generator = SystemInfoGenerator(self.config)
        self.browser_generator = BrowserDataGenerator(self.config)
        self.marketing_generator = MarketingGenerator(self.config)
        self.app_generator = ApplicationDataGenerator(self.config)
        self.hardware_generator = HardwareGenerator(self.config)
        self.network_generator = NetworkGenerator(self.config)
    
    def generate_stealc_log(self, persona: Persona) -> str:
        """Generate complete StealC log for a persona."""
        log_dir = os.path.join(
            self.output_base_dir, 
            f"StealC_{persona.persona_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info(f"Generating StealC log for {persona.persona_id}: {persona.first_name} {persona.last_name}")
        
        # Create directory structure
        os.makedirs(log_dir, exist_ok=True)
        
        try:
            # Generate copyright.txt
            copyright_content = self.marketing_generator.generate_copyright_header()
            self._write_file(log_dir, 'copyright.txt', copyright_content)
            
            # Generate system_info.txt
            system_info = self.system_generator.generate(persona)
            self._write_file(log_dir, 'system_info.txt', system_info)
            
            # Get browser profiles
            browser_profiles = self.browser_generator.get_browser_profiles(persona)
            
            # Create directories
            os.makedirs(os.path.join(log_dir, 'autofill'), exist_ok=True)
            os.makedirs(os.path.join(log_dir, 'cookies'), exist_ok=True)
            os.makedirs(os.path.join(log_dir, 'history'), exist_ok=True)
            os.makedirs(os.path.join(log_dir, 'AccountTokens'), exist_ok=True)
            
            # Track domains for cookie_list.txt
            all_cookie_domains = []
            
            # Generate browser data
            for browser, profile in browser_profiles:
                # Clean filename format
                profile_clean = profile.replace(' ', '_')
                filename_base = f"{browser}_{profile_clean}"
                
                # Autofill
                autofill_content = self.browser_generator.generate_autofill(persona, filename_base)
                self._write_file(os.path.join(log_dir, 'autofill'), f'{filename_base}.txt', autofill_content)
                
                # Cookies
                cookie_content, cookie_domains = self.browser_generator.generate_cookies(persona, filename_base)
                self._write_file(os.path.join(log_dir, 'cookies'), f'{filename_base} Network.txt', cookie_content)
                all_cookie_domains.extend(cookie_domains)
                
                # History
                history_content = self.browser_generator.generate_history(persona, filename_base)
                self._write_file(os.path.join(log_dir, 'history'), f'{filename_base}.txt', history_content)
                
                # Account tokens (Google OAuth)
                if 'Chrome' in browser or 'Edge' in browser:
                    tokens = self.app_generator.generate_google_tokens(persona, filename_base)
                    if tokens:
                        self._write_file(os.path.join(log_dir, 'AccountTokens'), 
                                       f'{filename_base}.txt', tokens)
            
            # Generate passwords.txt
            passwords_content = copyright_content + self.browser_generator.generate_passwords(persona)
            self._write_file(log_dir, 'passwords.txt', passwords_content)
            
            # Generate cookie_list.txt
            unique_domains = sorted(set(all_cookie_domains))
            self._write_file(log_dir, 'cookie_list.txt', '\n'.join(unique_domains) + '\n')
            
            # Generate domain_detect.txt (empty as per documentation)
            self._write_file(log_dir, 'domain_detect.txt', '')
            
            # Generate marketing file with random name
            marketing_filename, marketing_content = self.marketing_generator.generate_marketing_file()
            self._write_file(log_dir, marketing_filename, marketing_content)
            
            # Generate /soft/ applications
            self._generate_soft_applications(persona, log_dir)
            
            # Generate /plugins/ for crypto wallets
            if persona.crypto_user != 'None':
                self._generate_crypto_plugins(persona, log_dir, browser_profiles)
            
            logger.info(f"✓ Generated log in {log_dir}/")
            return log_dir
            
        except Exception as e:
            logger.error(f"Error generating log for {persona.persona_id}: {e}")
            raise
    
    def _write_file(self, directory: str, filename: str, content: str):
        """Write content to a file."""
        filepath = os.path.join(directory, filename) if os.path.isdir(directory) else directory
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_binary_file(self, directory: str, filename: str, content: bytes):
        """Write binary content to a file."""
        filepath = os.path.join(directory, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(content)
    
    def _generate_soft_applications(self, persona: Persona, log_dir: str):
        """Generate /soft/ directory with applications."""
        soft_dir = os.path.join(log_dir, 'soft')
        steam_token_content = ""
        
        # Discord
        discord_tokens = self.app_generator.generate_discord_tokens(persona)
        if discord_tokens:
            discord_dir = os.path.join(soft_dir, 'Discord')
            os.makedirs(discord_dir, exist_ok=True)
            self._write_file(discord_dir, 'tokens.txt', discord_tokens)
        
        # Steam
        steam_data = self.app_generator.generate_steam_data(persona)
        if steam_data:
            steam_dir = os.path.join(soft_dir, 'Steam')
            os.makedirs(steam_dir, exist_ok=True)
            
            # Write config files
            config_files = steam_data['config_files']
            
            for filename, content in config_files.items():
                if filename == 'ssfn_files':
                    for ssfn_name, ssfn_content in content:
                        self._write_binary_file(steam_dir, ssfn_name, ssfn_content)
                elif filename == 'dialog_resolutions':
                    for res in content:
                        self._write_file(steam_dir, f'DialogConfigOverlay_{res}.vdf', 
                                       '"DialogConfig"\n{\n}\n')
                else:
                    self._write_file(steam_dir, filename, content)
            
            # Basic dialog config
            self._write_file(steam_dir, 'DialogConfig.vdf', '"DialogConfig"\n{\n}\n')
            
            steam_token_content = steam_data['token']
        
        # Write steam_tokens.txt (even if empty)
        self._write_file(log_dir, 'steam_tokens.txt', steam_token_content + '\n' if steam_token_content else '')
        
        # Outlook
        outlook_accounts = self.app_generator.generate_outlook_accounts(persona)
        if outlook_accounts:
            outlook_dir = os.path.join(soft_dir, 'Outlook')
            os.makedirs(outlook_dir, exist_ok=True)
            self._write_file(outlook_dir, 'accounts.txt', outlook_accounts)
        
        # Telegram
        telegram_files = self.app_generator.generate_telegram_data(persona)
        if telegram_files:
            telegram_dir = os.path.join(soft_dir, 'Telegram', 'tdata')
            os.makedirs(telegram_dir, exist_ok=True)
            
            # Create subdirectory
            sub_dir = os.path.join(telegram_dir, 'D877F783D5D3EF8C')
            os.makedirs(sub_dir, exist_ok=True)
            
            for filename, content in telegram_files.items():
                if '/' in filename:
                    filepath = os.path.join(telegram_dir, filename)
                else:
                    filepath = os.path.join(telegram_dir, filename)
                
                self._write_binary_file(os.path.dirname(filepath), os.path.basename(filepath), content)
    
    def _generate_crypto_plugins(self, persona: Persona, log_dir: str, 
                               browser_profiles: List[Tuple[str, str]]):
        """Generate crypto wallet plugins."""
        plugins_dir = os.path.join(log_dir, 'plugins')
        
        # Determine which wallets to include
        wallet_configs = self.config.get('applications', 'crypto_wallets', default={})
        wallets = []
        
        if random.random() > 0.4:
            wallets.append('MetaMask')
        if persona.crypto_user == 'Heavy' and random.random() > 0.6:
            wallets.append('Binance Wallet')
        
        for wallet in wallets:
            # Only Chrome supports these extensions
            chrome_profiles = [p for p in browser_profiles if 'Chrome' in p[0]]
            if chrome_profiles:
                browser, profile = chrome_profiles[0]  # Use first Chrome profile
                
                wallet_dir = os.path.join(plugins_dir, wallet, 'Google Chrome', 
                                        profile, 'LocalExtensionSettings')
                os.makedirs(wallet_dir, exist_ok=True)
                
                wallet_files = self.app_generator.generate_crypto_wallet(wallet)
                for filename, content in wallet_files.items():
                    self._write_binary_file(wallet_dir, filename, content)
    
    def generate_all_stealc_logs(self) -> List[str]:
        """Generate StealC logs for all personas marked for StealC infection."""
        generated_logs = []
        
        logger.info("Starting StealC stealer log generation...")
        logger.info(f"Processing {len(self.personas)} personas marked for StealC infection")
        logger.info("-" * 50)
        
        for persona in self.personas:
            try:
                log_dir = self.generate_stealc_log(persona)
                generated_logs.append(log_dir)
            except Exception as e:
                logger.error(f"Error generating log for {persona.persona_id}: {str(e)}")
                traceback.print_exc()
        
        logger.info("-" * 50)
        logger.info(f"Successfully generated {len(generated_logs)} StealC stealer logs")
        return generated_logs


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate synthetic StealC Stealer logs for personas marked with StealC infection'
    )
    parser.add_argument('csv_file', help='Path to personas CSV file with Infection column')
    parser.add_argument('--exclude', nargs='+', help='PersonaIDs to exclude')
    parser.add_argument('--sample-size', type=int, default=24, 
                       help='Maximum number of StealC-infected personas to process (default: 24)')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--single', help='Generate log for single persona ID (must be marked for StealC)')
    
    args = parser.parse_args()
    
    try:
        generator = StealCLogGenerator(
            args.csv_file, 
            exclude_ids=args.exclude,
            sample_size=args.sample_size,
            config_dir=args.config_dir
        )
        
        if args.single:
            # Find and generate for single persona
            persona = next((p for p in generator.personas if p.persona_id == args.single), None)
            if persona:
                generator.generate_stealc_log(persona)
            else:
                logger.error(f"Persona ID '{args.single}' not found in personas marked for StealC")
        else:
            # Generate all logs
            generator.generate_all_stealc_logs()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
