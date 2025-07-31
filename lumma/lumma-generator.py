#!/usr/bin/env python3
"""
Synthetic Lumma Stealer Log Generator for DEFCON Red Team Village Workshop
Generates realistic but obviously fake stealer logs for educational purposes.

This generator reads personas from a CSV file and generates logs for all personas
where the 'Infection' column contains 'Lumma'. This ensures each persona is only
infected once and respects pre-assigned stealer infections.
"""

import csv
import hashlib
import json
import logging
import os
import random
import string
import traceback
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
    os: str
    device_type: str
    income_level: str
    primary_browser: str
    secondary_browser: str
    password_habits: str
    persona_archetype: str
    infection_vector: str
    crypto_user: str
    social_media_user: str
    online_shopper: str
    business_access: str
    antivirus_type: str

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
            os=row['OS'],
            device_type=row.get('DeviceType', 'Personal_Laptop'),
            income_level=row.get('IncomeLevel', 'Medium'),
            primary_browser=row.get('PrimaryBrowser', 'Chrome'),
            secondary_browser=row.get('SecondaryBrowser', 'None'),
            password_habits=row.get('PasswordHabits', 'Mixed'),
            persona_archetype=row.get('PersonaArchetype', 'General'),
            infection_vector=row.get('InfectionVector', 'Unknown'),
            crypto_user=row.get('CryptoUser', 'None'),
            social_media_user=row.get('SocialMediaUser', 'Light'),
            online_shopper=row.get('OnlineShopper', 'Light'),
            business_access=row.get('BusinessAccess', 'No'),
            antivirus_type=row.get('AntivirusType', 'Windows Defender')
        )


class ConfigurationManager:
    """Manages all configuration data from external files."""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all JSON configuration files from the config directory."""
        lumma_config_dir = self.config_dir / 'lumma'
        if not lumma_config_dir.exists():
            raise FileNotFoundError(f"Lumma configuration directory '{lumma_config_dir}' not found.")
        
        for config_file in lumma_config_dir.glob('*.json'):
            config_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configs[config_name] = json.load(f)
                logger.info(f"Loaded lumma/{config_name}.json")
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
        """Generate realistic Windows hardware based on persona."""
        random.seed(self.get_persona_seed(persona.persona_id, 'hardware'))
        
        # Get hardware config for device type and income level
        hardware_config = self.config.get('hardware', persona.device_type, persona.income_level)
        if not hardware_config:
            # Fallback to default
            hardware_config = self.config.get('hardware', 'Personal_Laptop', 'Medium')
        
        return {
            'cpu': random.choice(hardware_config['cpu']),
            'gpu': random.choice(hardware_config['gpu']),
            'ram': random.choice(hardware_config['ram']),
            'resolution': random.choice(hardware_config['resolution'])
        }
    
    def generate_computer_id(self) -> str:
        """Generate random computer ID."""
        chars = self.config.get('charsets', 'computer_id', default='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        length = self.config.get('main', 'generator_settings', 'computer_id_length', default=8)
        return ''.join(random.choices(chars, k=length))
    
    def generate_machine_id(self) -> str:
        """Generate machine GUID."""
        parts = []
        for i in range(5):
            if i == 0:
                length = 8
            elif i < 4:
                length = 4
            else:
                length = 12
            part = ''.join(random.choices('0123456789abcdef', k=length))
            parts.append(part)
        return '-'.join(parts)
    
    def generate_hwid(self) -> str:
        """Generate hardware ID."""
        chars = self.config.get('charsets', 'hwid', default='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        length = self.config.get('main', 'generator_settings', 'hwid_length', default=16)
        return ''.join(random.choices(chars, k=length))
    
    def generate_product_id(self) -> str:
        """Generate Windows product ID."""
        ranges = self.config.get('ranges', 'product_id')
        parts = []
        for _ in range(4):
            parts.append(str(random.randint(ranges['min'], ranges['max'])))
        return '-'.join(parts)


class NetworkGenerator:
    """Generates network-related information."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    def generate_ip_for_country(self, country: str) -> str:
        """Generate IP address based on country."""
        ip_ranges = self.config.get('network', 'country_ip_ranges')
        
        if country in ip_ranges:
            prefix = ip_ranges[country]
            # Handle different IP range formats
            if isinstance(prefix, str):
                parts = prefix.split('.')
                if len(parts) == 3:
                    # Complete the IP
                    return f"{prefix}.{random.randint(1, 254)}"
                elif len(parts) == 2:
                    return f"{prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"
            elif isinstance(prefix, dict):
                # Range format
                return f"{random.randint(prefix['start'], prefix['end'])}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        
        # Default fallback
        return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    def get_timezone_for_country(self, country: str) -> str:
        """Get timezone for country."""
        timezones = self.config.get('network', 'country_timezones', default={})
        return timezones.get(country, '(UTC+00:00) UTC')
    
    def get_language_for_country(self, country: str) -> str:
        """Get language for country."""
        languages = self.config.get('network', 'country_languages', default={})
        return languages.get(country, 'English (United States)')


class SystemInfoGenerator(BaseGenerator):
    """Generates System.txt content."""
    
    def __init__(self, config: ConfigurationManager):
        super().__init__(config)
        self.hardware_generator = HardwareGenerator(config)
        self.network_generator = NetworkGenerator(config)
    
    def generate(self, persona: Persona) -> str:
        """Generate System.txt content in correct Lumma format."""
        random.seed(self.get_persona_seed(persona.persona_id, 'system'))
        
        # Generate all system components
        hardware = self.hardware_generator.generate(persona)
        
        # System identifiers
        computer_id = self.hardware_generator.generate_computer_id()
        computer_name = f"DESKTOP-{computer_id}"
        hwid = self.hardware_generator.generate_hwid()
        
        # Network info
        ip = self.network_generator.generate_ip_for_country(persona.country)
        timezone = self.network_generator.get_timezone_for_country(persona.country)
        language = self.network_generator.get_language_for_country(persona.country)
        
        # Get language code
        lang_codes = {
            "English (United States)": "en-US",
            "English (United Kingdom)": "en-GB", 
            "German (Germany)": "de-DE",
            "French (France)": "fr-FR",
            "Japanese (Japan)": "ja-JP",
            "Portuguese (Brazil)": "pt-BR",
            "English (India)": "en-IN",
            "Russian (Russia)": "ru-RU",
            "English (Belgium)": "en-BE",
            "Norwegian (Norway)": "nb-NO"
        }
        lang_code = lang_codes.get(language, "en-US")
        
        # Override for specific countries
        if persona.country == "NO":
            lang_code = "nb-NO"
        elif persona.country == "ES" and random.random() > 0.5:
            lang_code = "en-BE"  # Some Spanish IPs show Belgian English
        
        # Execution info
        execution_path = self._generate_execution_path(persona)
        
        # Campaign info
        campaigns = self.config.get('main', 'lumma_campaigns', default=['default--CAMPAIGN'])
        lid = random.choice(campaigns)
        
        # Headers
        headers = self.config.get('main', 'buy_headers', default=[])
        if not headers:
            headers = [
                ["# Buy now: TG @lummanowork", "# Buy&Sell logs: @lummamarketplace_bot"],
                ["# Buy now: TG @lummanowork", "# Buy&Sell logs: @lummamarketbot"],
                ["# Buy now: ARHONT CLOUD || t.me/ArhontCloud", "# Buy&Sell logs: TG @ArhontSupport"]
            ]
        header_lines = random.choice(headers)
        
        # Build info
        build_dates = self.config.get('main', 'build_dates', default=['Jan 01 2024'])
        build_date = random.choice(build_dates)
        
        # OS Version
        os_version = self._get_windows_version(persona.os)
        
        # Generate dates
        install_date = self._generate_install_date()
        current_datetime = datetime.now()
        local_date = current_datetime.strftime('%d.%m.%Y %H:%M:%S')
        
        # Adjust time for timezone
        utc_offset = self._get_utc_offset(timezone)
        adjusted_time = current_datetime + timedelta(hours=utc_offset)
        sig_timestamp = int(adjusted_time.timestamp())
        sig_hash = hashlib.md5(str(random.random()).encode()).hexdigest()
        time_str = adjusted_time.strftime('%d.%m.%Y %H:%M:%S')
        
        # Security info
        elevated = 'true' if random.random() > 0.7 else 'false'
        
        # Config hash
        config_hash = hashlib.md5(str(random.random()).encode()).hexdigest()
        
        # CPU info
        cpu_info = hardware['cpu']
        # Extract thread count from CPU name if possible
        cpu_threads = 4  # default
        cpu_cores = 2    # default
        if 'i9' in cpu_info:
            cpu_threads = random.choice([16, 20, 24])
            cpu_cores = cpu_threads // 2
        elif 'i7' in cpu_info:
            cpu_threads = random.choice([8, 12, 16])
            cpu_cores = cpu_threads // 2
        elif 'i5' in cpu_info:
            cpu_threads = random.choice([6, 8, 12])
            cpu_cores = cpu_threads // 2
        elif 'i3' in cpu_info:
            cpu_threads = 4
            cpu_cores = 2
        elif 'Ryzen 9' in cpu_info:
            cpu_threads = random.choice([16, 24, 32])
            cpu_cores = cpu_threads // 2
        elif 'Ryzen 7' in cpu_info:
            cpu_threads = random.choice([12, 16])
            cpu_cores = cpu_threads // 2
        elif 'Ryzen 5' in cpu_info:
            cpu_threads = random.choice([6, 12])
            cpu_cores = cpu_threads // 2
        elif 'Xeon' in cpu_info:
            cpu_threads = 12
            cpu_cores = 6
        
        # Build System.txt
        lines = []
        
        # Headers
        lines.extend(header_lines)
        
        # Build info
        lines.append(f"- LummaC2 Build: {build_date}")
        lines.append(f"- LID: {lid}")
        lines.append(f"- Configuration: {config_hash}")
        lines.append(f"- Path: {execution_path}")
        lines.append("")
        
        # OS info
        lines.append(f"- OS Version: {os_version}")
        lines.append(f"- Local Date: {local_date}")
        lines.append(f"- Time Zone: {timezone}")
        lines.append(f"- Install Date: {install_date}")
        lines.append(f"- Elevated: {elevated}")
        lines.append(f"- Computer: {computer_name}")
        lines.append(f"- User: {persona.first_name.lower()[:5]}")
        lines.append(f"- Domain: ")
        lines.append(f"- Hostname: {computer_name}")
        lines.append(f"- NetBIOS: {computer_name}")
        lines.append(f"- Language: {lang_code}")
        lines.append(f"- Anti Virus:")
        lines.append(f"\t- {persona.antivirus_type}")
        lines.append(f"- HWID: {hwid}")
        lines.append(f"- RAM Size: {hardware['ram']}MB")
        lines.append(f"- CPU Vendor: {'GenuineIntel' if 'Intel' in cpu_info else 'AuthenticAMD'}")
        lines.append(f"- CPU Name: {cpu_info}")
        lines.append(f"- CPU Threads: {cpu_threads}")
        lines.append(f"- CPU Cores: {cpu_cores}")
        lines.append(f"- GPU: {hardware['gpu']}")
        lines.append(f"- Display resolution: {hardware['resolution']}")
        lines.append("")
        
        # Network info
        lines.append(f"- IP Address: {ip}")
        lines.append(f"- Time: {time_str} (sig:{sig_timestamp}.{sig_hash})")
        lines.append(f"- Country: {persona.country}")
        lines.append("")
        
        # Marketing footers
        lines.append("------------------------------------")
        lines.append("")
        
        # Add marketing messages
        marketing = self.config.get('main', 'marketing_messages', default=[])
        if not marketing:
            marketing = [
                ["Automated log store >> t.me/lummamarketplace_bot",
                 "Tens of thousands of logs for sale, rating system, search by filters and countries, hundreds of sellers with their own storefronts. Unique development based on MaaS from LummaC2.",
                 "Purchase quality material right now - t.me/lummamarketplace_bot"],
                ["Automated log store >> t.me/lummamarketbot",
                 "Tens of thousands of logs for sale, rating system, search by filters and countries, hundreds of sellers with their own storefronts. Unique development based on MaaS from LummaC2.",
                 "Purchase quality material right now - t.me/lummamarketbot"]
            ]
        
        msg_set = random.choice(marketing)
        lines.append(msg_set[0])
        lines.append(msg_set[1])
        lines.append(msg_set[2])
        
        # Sometimes add additional marketing
        if random.random() > 0.5:
            additional = self.config.get('main', 'additional_marketing', default=[])
            if not additional:
                additional = [
                    ["",
                     "------------------------------------",
                     "",
                     "",
                     "LIT ENERGY — это для тех, кто готов залетать в самый лютый движ, газовать до отсечки и с непоколебимой волей двигаться вперед, чтобы забирать свое.",
                     "Увеличенное содержание энергетических веществ для максимальной подростки заряда и только лучшие ингредиенты: натуральные соки, не вызывающие изжогу.",
                     "Линейка вкусов на выбор: Classic, Original, Blueberry, Mango Coconut.",
                     "",
                     "Приобрести: litenergy.ru",
                     ""],
                    ["",
                     "------------------------------------",
                     "",
                     "Italiano - это пример достойного сервиса. Качественный брут и отработка папки Wallets (Metamask, Exodus, Phantom, .dat и другие).",
                     "В наличии около 500 видеокарт, ≈50.000.000 паролей в секунду. Опыт работы в этой сфере более 5 лет. Онлайн 20 часов в сутки.",
                     "Общий депозит на форумах 1.5btc.",
                     "",
                     "",
                     "Принимаю балансы от 5.000$",
                     "Процент за работу - 70/30 (70% Клиенту)",
                     "",
                     "",
                     "Заработать вместе >> https://t.me/milan_brute"]
                ]
            lines.extend(random.choice(additional))
        
        return '\n'.join(lines)
    
    def _get_windows_version(self, os_string: str) -> str:
        """Convert OS string to Lumma format."""
        if 'Windows 11' in os_string:
            editions = ['Pro', 'Home', 'Enterprise']
            edition = random.choice(editions)
            return f"Windows 11 {edition} (10.0.22631) x64"
        else:  # Windows 10
            editions = ['Pro', 'Home', 'Enterprise']
            edition = random.choice(editions)
            return f"Windows 10 {edition} (10.0.19045) x64"
    
    def _get_utc_offset(self, timezone: str) -> int:
        """Extract UTC offset from timezone string."""
        if 'UTC+' in timezone:
            return int(timezone.split('+')[1].split(':')[0])
        elif 'UTC-' in timezone:
            return -int(timezone.split('-')[1].split(':')[0])
        return 0
    
    def _generate_execution_path(self, persona: Persona) -> str:
        """Generate execution path."""
        paths = self.config.get('main', 'execution_paths', default=[])
        if paths:
            path = random.choice(paths)
            username = persona.first_name.lower()[:5]
            return path.replace('{username}', username)
        
        # Default paths
        username = persona.first_name.lower()[:5]
        default_paths = [
            f"C:\\Users\\{username}\\AppData\\Local\\Temp\\Setup.exe",
            f"C:\\Users\\{username}\\AppData\\Local\\Temp\\Rar$EXb{random.randint(10000,99999)}.{random.randint(10000,99999)}\\Setup.exe",
            f"C:\\Users\\{username}\\AppData\\Local\\Temp\\{random.randint(100000,999999)}\\Author.com",
            f"C:\\WINDOWS\\SysWOW64\\msiexec.exe"
        ]
        return random.choice(default_paths)
    
    def _generate_install_date(self) -> str:
        """Generate Windows install date."""
        days_range = self.config.get('ranges', 'install_date_days', default={'min': 180, 'max': 1095})
        days_ago = random.randint(days_range['min'], days_range['max'])
        install_date = datetime.now() - timedelta(days=days_ago)
        # Format: DD.MM.YYYY HH:MM:SS
        return install_date.strftime('%d.%m.%Y %H:%M:%S')


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
    
    def generate_browser_structure(self, persona: Persona) -> Dict[str, List[str]]:
        """Determine which browsers and profiles to create."""
        browsers = []
        
        # Add primary browser
        if persona.primary_browser and persona.primary_browser != 'None':
            browsers.append(persona.primary_browser)
        
        # Add secondary browser
        if persona.secondary_browser and persona.secondary_browser != 'None':
            browsers.append(persona.secondary_browser)
        
        # Ensure at least one browser
        if not browsers:
            browsers = ['Chrome']
        
        # Generate profiles for each browser
        browser_profiles = {}
        for browser in browsers:
            profiles = ['Default']
            
            # Heavy users get multiple profiles
            if persona.social_media_user == 'Heavy' or persona.online_shopper == 'Heavy':
                max_profiles = self.config.get('main', 'generator_settings', 'max_browser_profiles', default=4)
                num_profiles = random.randint(2, max_profiles)
                profiles.extend([f'Profile {i}' for i in range(1, num_profiles)])
            
            browser_profiles[browser] = profiles
        
        return browser_profiles
    
    def generate_passwords(self, persona: Persona, browser: str, profile: str) -> List[str]:
        """Generate passwords for a specific browser profile."""
        random.seed(self.get_persona_seed(persona.persona_id, f'passwords_{browser}_{profile}'))
        
        # Number of passwords based on usage
        password_ranges = self.config.get('ranges', 'password_count')
        if persona.password_habits == 'Browser_Storage':
            num_passwords = random.randint(password_ranges['browser_storage']['min'], 
                                         password_ranges['browser_storage']['max'])
        else:
            num_passwords = random.randint(password_ranges['default']['min'], 
                                         password_ranges['default']['max'])
        
        passwords = []
        sites = self._get_sites_for_persona(persona)
        browser_versions = self.config.get('browsers', 'versions', default={})
        version = random.choice(browser_versions.get(browser, ['130.0.0.0']))
        
        for _ in range(num_passwords):
            site = random.choice(sites)
            username = self._generate_username_for_site(persona, site)
            password = self._generate_password_for_persona(persona)
            
            entry = self.template_renderer.render(
                'password_entry',
                browser=browser,
                profile=profile,
                version=version,
                site=site,
                username=username,
                password=password
            )
            passwords.append(entry)
        
        return passwords
    
    def generate_autofills(self, persona: Persona) -> List[str]:
        """Generate autofill data."""
        random.seed(self.get_persona_seed(persona.persona_id, 'autofills'))
        
        entries = []
        ranges = self.config.get('ranges', 'autofill_count', default={'min': 50, 'max': 100})
        num_entries = random.randint(ranges['min'], ranges['max'])
        
        # Generate address
        address = self._generate_address(persona)
        
        # Generate phone
        phone = self._generate_phone_number(persona.country)
        
        # Common fields
        common_fields = {
            'first_name': persona.first_name,
            'last_name': persona.last_name,
            'full_name': f"{persona.first_name} {persona.last_name}",
            'email': persona.email_personal,
            'phone': phone,
            'address': address['street'],
            'city': address['city'],
            'state': address['state'],
            'zip': address['zip'],
            'billing_first_name': persona.first_name,
            'billing_last_name': persona.last_name,
            'shipping_address': address['street'],
            'cardnumber': self._generate_credit_card_number(),
            'cardExpiry': f"{random.randint(1,12):02d} / {random.randint(25,29)}"
        }
        
        # Add form fields (70%)
        field_list = list(common_fields.keys())
        for _ in range(int(num_entries * 0.7)):
            field = random.choice(field_list)
            value = common_fields[field]
            
            entry = self.template_renderer.render(
                'autofill_entry',
                field=field,
                value=value
            )
            entries.append(entry)
        
        # Add search queries (25%)
        searches = self._generate_search_queries(persona, int(num_entries * 0.25))
        for search in searches:
            entry = self.template_renderer.render(
                'autofill_entry',
                field='q',
                value=search
            )
            entries.append(entry)
        
        # Add passwords (5%)
        for _ in range(int(num_entries * 0.05)):
            entry = self.template_renderer.render(
                'autofill_entry',
                field='password',
                value=self._generate_password_for_persona(persona)
            )
            entries.append(entry)
        
        random.shuffle(entries)
        return entries
    
    def generate_history(self, persona: Persona) -> List[str]:
        """Generate browsing history."""
        random.seed(self.get_persona_seed(persona.persona_id, 'history'))
        
        entries = []
        sites = self._get_sites_for_persona(persona)
        
        # Time range
        time_range = self.config.get('ranges', 'history_days', default={'min': 14, 'max': 28})
        end_date = datetime.now()
        start_date = end_date - timedelta(days=random.randint(time_range['min'], time_range['max']))
        
        # Number of entries
        entry_range = self.config.get('ranges', 'history_entries', default={'min': 50, 'max': 100})
        num_entries = random.randint(entry_range['min'], entry_range['max'])
        
        # Bug entries
        bug_range = self.config.get('ranges', 'history_bug_entries', default={'min': 10, 'max': 20})
        num_bug_entries = random.randint(bug_range['min'], bug_range['max'])
        
        for i in range(num_entries):
            # Generate timestamp
            if i < num_bug_entries:
                # 1601 bug
                timestamp = datetime(1601, 1, 1, 2, 30, 17)
            else:
                # Random timestamp in range
                timestamp = start_date + timedelta(
                    seconds=random.randint(0, int((end_date - start_date).total_seconds()))
                )
            
            site = random.choice(sites)
            url = f"https://{site}/"
            
            # Add search parameters for Google
            if 'google.com' in site and random.random() > 0.5:
                searches = self._generate_search_queries(persona, 5)
                if searches:
                    search_term = random.choice(searches)
                    url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                    title = f"{search_term} - Google Search"
                else:
                    title = self._get_site_title(site)
            else:
                title = self._get_site_title(site)
            
            entry = self.template_renderer.render(
                'history_entry',
                url=url,
                title=title,
                timestamp=timestamp.strftime('%d.%m.%Y %H:%M:%S')
            )
            entries.append(entry)
        
        return entries
    
    def generate_cookies(self, persona: Persona, sites: List[str]) -> List[str]:
        """Generate cookie data."""
        random.seed(self.get_persona_seed(persona.persona_id, 'cookies'))
        
        cookies = []
        ranges = self.config.get('ranges', 'cookie_count', default={'min': 50, 'max': 100})
        num_cookies = random.randint(ranges['min'], ranges['max'])
        
        cookie_names = self.config.get('browsers', 'cookie_names', 
                                     default=['session_id', 'auth_token', 'user_id'])
        
        for site in sites[:num_cookies]:
            domain = f".{site}"
            
            # Expiry date
            expiry_range = self.config.get('ranges', 'cookie_expiry_days', 
                                         default={'min': 30, 'max': 365})
            expiry_days = random.randint(expiry_range['min'], expiry_range['max'])
            expiry = int((datetime.now() + timedelta(days=expiry_days)).timestamp())
            
            # Cookie value
            if 'google' in site or 'facebook' in site:
                value = self._generate_auth_token()
            else:
                value = self._generate_uuid()
            
            cookie_name = random.choice(cookie_names)
            
            cookie = f"{domain}\tFALSE\t/\tTRUE\t{expiry}\t{cookie_name}\t{value}"
            cookies.append(cookie + '\n')
        
        return cookies
    
    def _get_sites_for_persona(self, persona: Persona) -> List[str]:
        """Get relevant sites based on persona."""
        # Start with common sites
        sites = self.config.get('websites', 'common_sites', default=[]).copy()
        
        # Add archetype-specific sites
        archetype_sites = self.config.get('websites', 'archetype_sites', 
                                        persona.persona_archetype, default=[])
        sites.extend(archetype_sites)
        
        return sites
    
    def _generate_username_for_site(self, persona: Persona, site: str) -> str:
        """Generate username for a specific site."""
        if random.random() > 0.5 and persona.email_personal:
            return persona.email_personal
        else:
            return f"{persona.first_name.lower()}{random.randint(100,999)}"
    
    def _generate_password_for_persona(self, persona: Persona) -> str:
        """Generate password based on persona habits."""
        password_patterns = self.config.get('passwords', persona.password_habits, default=[])
        
        if not password_patterns:
            # Fallback pattern
            password_patterns = ["{first_name}{year}!"]
        
        pattern = random.choice(password_patterns)
        
        # Replace placeholders
        password = pattern.replace('{first_name}', persona.first_name)
        password = password.replace('{last_name}', persona.last_name)
        password = password.replace('{year}', str(random.randint(2020, 2024)))
        password = password.replace('{number}', str(random.randint(100, 999)))
        
        # Handle {random} placeholder
        if '{random}' in password:
            chars = self.config.get('charsets', 'password_random', 
                                  default='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%')
            length = random.randint(12, 20)
            random_part = ''.join(random.choices(chars, k=length))
            password = password.replace('{random}', random_part)
        
        return password
    
    def _generate_address(self, persona: Persona) -> Dict[str, str]:
        """Generate address for persona."""
        streets = self.config.get('network', 'street_names', 
                                default=['Main St', 'Oak Ave', 'Elm St'])
        
        street_number_range = self.config.get('ranges', 'street_number', 
                                            default={'min': 100, 'max': 9999})
        street_num = random.randint(street_number_range['min'], street_number_range['max'])
        
        return {
            'street': f"{street_num} {random.choice(streets)}",
            'city': persona.city,
            'state': persona.state_region,
            'zip': str(random.randint(10000, 99999))
        }
    
    def _generate_phone_number(self, country: str) -> str:
        """Generate phone number for country."""
        formats = self.config.get('network', 'phone_formats', default={})
        
        if country in formats:
            format_str = formats[country]
            # Replace placeholders
            phone = format_str
            while '{' in phone:
                start = phone.find('{')
                end = phone.find('}', start)
                if end == -1:
                    break
                    
                range_str = phone[start+1:end]
                if '-' in range_str:
                    min_val, max_val = map(int, range_str.split('-'))
                    value = str(random.randint(min_val, max_val))
                    phone = phone[:start] + value + phone[end+1:]
                else:
                    break
            return phone
        else:
            # Default format
            return f"+{random.randint(1,99)} {random.randint(100,999)} {random.randint(100,999)} {random.randint(1000,9999)}"
    
    def _generate_credit_card_number(self) -> str:
        """Generate fake credit card number."""
        ranges = self.config.get('ranges', 'credit_card', default={'prefix': {'min': 4000, 'max': 5999}})
        prefix = random.randint(ranges['prefix']['min'], ranges['prefix']['max'])
        return f"{prefix}{random.randint(1000,9999)}{random.randint(1000,9999)}{random.randint(1000,9999)}"
    
    def _generate_search_queries(self, persona: Persona, count: int) -> List[str]:
        """Generate search queries based on persona."""
        # Base queries
        queries = self.config.get('browsers', 'search_queries', 'base', default=[]).copy()
        
        # Archetype-specific queries
        archetype_queries = self.config.get('browsers', 'search_queries', 
                                          persona.persona_archetype, default=[])
        queries.extend(archetype_queries)
        
        random.shuffle(queries)
        return queries[:count]
    
    def _get_site_title(self, site: str) -> str:
        """Get realistic title for site."""
        titles = self.config.get('browsers', 'site_titles', default={})
        return titles.get(site, site.replace('.com', '').title())
    
    def _generate_auth_token(self) -> str:
        """Generate realistic auth token."""
        parts = []
        token_config = self.config.get('browsers', 'auth_token', default={'parts': 4, 'min_length': 20, 'max_length': 50})
        
        for _ in range(token_config['parts']):
            part_len = random.randint(token_config['min_length'], token_config['max_length'])
            chars = self.config.get('charsets', 'auth_token', 
                                  default='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
            parts.append(''.join(random.choices(chars, k=part_len)))
        
        return ''.join(parts)
    
    def _generate_uuid(self) -> str:
        """Generate UUID-like string."""
        parts = []
        for length in [8, 4, 4, 12]:
            part = ''.join(random.choices('0123456789abcdef', k=length))
            parts.append(part)
        return '-'.join(parts)


class SystemFilesGenerator:
    """Generates system-related files."""
    
    def __init__(self, config: ConfigurationManager):
        self.config = config
    
    @staticmethod
    def get_persona_seed(persona_id: str, suffix: str = "") -> int:
        """Generate consistent seed for persona-specific data."""
        seed_string = f"{persona_id}_{suffix}"
        return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
    
    def generate_debug_txt(self) -> str:
        """Generate Debug.txt with Lumma operation codes."""
        random.seed(random.random())  # Different each time
        
        codes = self.config.get('main', 'debug_codes', default=['reg', 'fin'])
        optional_codes = self.config.get('main', 'debug_optional_codes', default=[])
        
        lines = [codes[0]]  # Start with 'reg'
        
        # Randomly include optional codes
        if optional_codes and random.random() > 0.5:
            lines.extend(optional_codes)
        
        # Add remaining codes
        lines.extend(codes[1:-1])  # All except first and last
        
        # Add dynamic values
        lines.extend([
            f"res - {random.randint(1000, 5000)}",
            f"dat - {random.randint(10000, 4000000)}"
        ])
        
        lines.append(codes[-1])  # End with 'fin'
        
        # Sometimes repeat
        if random.random() > 0.5:
            lines.extend(lines[1:-1])  # Repeat without 'reg' and 'fin'
            lines.append(codes[-1])  # End with 'fin' again
        
        return '\n'.join(lines)
    
    def generate_software_txt(self, persona: Persona) -> List[str]:
        """Generate Software.txt - installed programs list."""
        random.seed(self.get_persona_seed(persona.persona_id, 'software'))
        
        # Base Windows software
        software = self.config.get('software', 'windows_base', default=[]).copy()
        
        # Add browsers
        browser_software = self.config.get('software', 'browsers', default={})
        if persona.primary_browser in browser_software:
            software.append(browser_software[persona.primary_browser])
        if persona.secondary_browser in browser_software:
            software.append(browser_software[persona.secondary_browser])
        
        # Add archetype-specific software
        archetype_software = self.config.get('software', 'archetype', 
                                           persona.persona_archetype, default=[])
        software.extend(archetype_software)
        
        # Add random common software
        common_software = self.config.get('software', 'common', default=[])
        if common_software:
            num_to_add = min(random.randint(2, 4), len(common_software))
            software.extend(random.sample(common_software, num_to_add))
        
        # Shuffle (keeping Windows stuff at top)
        windows_count = len(self.config.get('software', 'windows_base', default=[]))
        if len(software) > windows_count:
            shuffled = software[windows_count:]
            random.shuffle(shuffled)
            software = software[:windows_count] + shuffled
        
        # Limit to reasonable number
        max_software = self.config.get('ranges', 'software_count', 'max', default=100)
        return software[:max_software]
    
    def generate_processes_txt(self, persona: Persona) -> List[str]:
        """Generate Processes.txt - running processes."""
        random.seed(self.get_persona_seed(persona.persona_id, 'processes'))
        
        # System processes
        processes = self.config.get('processes', 'system', default=[]).copy()
        
        # Multiple svchost instances
        svchost_range = self.config.get('ranges', 'svchost_count', default={'min': 20, 'max': 40})
        num_svchost = random.randint(svchost_range['min'], svchost_range['max'])
        processes.extend(['svchost.exe'] * num_svchost)
        
        # Browser processes
        if 'Chrome' in persona.primary_browser:
            chrome_range = self.config.get('ranges', 'chrome_processes', default={'min': 5, 'max': 15})
            processes.extend(['chrome.exe'] * random.randint(chrome_range['min'], chrome_range['max']))
        
        # Archetype-specific processes
        archetype_processes = self.config.get('processes', 'archetype', 
                                            persona.persona_archetype, default=[])
        processes.extend(archetype_processes)
        
        # Add the malware
        processes.append('Setup.exe')
        
        return processes
    
    def generate_clipboard(self, persona: Persona) -> Optional[str]:
        """Generate Clipboard.txt content if applicable."""
        random.seed(self.get_persona_seed(persona.persona_id, 'clipboard'))
        
        # Based on infection vector
        if persona.infection_vector in ['Cracked_Software', 'Fake_Update']:
            # Malware download URL
            filenames = self.config.get('main', 'malware_filenames', 
                                      default=['Setup_2024.zip', 'Installer.zip'])
            if filenames:
                filename = random.choice(filenames)
                file_id = hashlib.md5(str(random.random()).encode()).hexdigest()[:12]
                return f"https://www.mediafire.com/file/{file_id}/{filename}/file"
        
        # Crypto address
        elif persona.crypto_user != 'None' and random.random() > 0.5:
            if random.random() > 0.5:
                # Bitcoin
                chars = self.config.get('charsets', 'bitcoin', 
                                      default='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')
                return f"1{''.join(random.choices(chars, k=33))}"
            else:
                # Ethereum
                return f"0x{''.join(random.choices('0123456789abcdef', k=40))}"
        
        # Password
        elif persona.password_habits == 'Browser_Storage' and random.random() > 0.3:
            browser_gen = BrowserDataGenerator(self.config)
            return browser_gen._generate_password_for_persona(persona)
        
        return None
    
    def generate_google_accounts(self, persona: Persona) -> Optional[List[str]]:
        """Generate Google account tokens if applicable."""
        if 'gmail' not in persona.email_personal and 'gmail' not in persona.email_work:
            return None
        
        random.seed(self.get_persona_seed(persona.persona_id, 'google'))
        
        tokens = []
        
        # Determine number of accounts
        num_accounts = 1
        if persona.business_access == 'Yes':
            num_accounts = 2
        
        # Generate tokens
        token_length = self.config.get('main', 'generator_settings', 'google_token_length', default=200)
        chars = self.config.get('charsets', 'google_token', 
                              default='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        
        for _ in range(num_accounts):
            token = ''.join(random.choices(chars, k=token_length))
            tokens.append(token)
        
        return tokens


class LummaLogGenerator:
    """Main generator class for Lumma stealer logs."""
    
    def __init__(self, csv_file_path: str, config_dir: str = 'config'):
        self.config = ConfigurationManager(config_dir)
        self.personas = self.load_lumma_personas(csv_file_path)
        self.output_base_dir = self.config.get('main', 'output_directory', default='lumma_logs')
        self._initialize_generators()
    
    def load_lumma_personas(self, csv_file_path: str) -> List[Persona]:
        """Load personas from CSV where Infection column indicates Lumma."""
        lumma_personas = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
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
                
                # Read personas infected by Lumma
                for row in reader:
                    infection_value = row.get(infection_column, '').strip().lower()
                    if infection_value == 'lumma':
                        # Verify it's a Windows user (Lumma only infects Windows)
                        if 'Windows' not in row.get('OS', ''):
                            logger.warning(f"Persona {row['PersonaID']} marked for Lumma but has OS: {row.get('OS')}. Skipping.")
                            continue
                        lumma_personas.append(Persona.from_csv_row(row))
            
            logger.info(f"Found {len(lumma_personas)} personas infected by Lumma")
            
            if not lumma_personas:
                logger.warning("No personas found with Lumma infection. Check the 'Infection' column in your CSV.")
            
            # Log selected personas
            self._log_selected_personas(lumma_personas)
            
            return lumma_personas
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            raise
    
    def _log_selected_personas(self, personas: List[Persona]):
        """Log personas infected by Lumma."""
        print("\n" + "="*50)
        print(f"FOUND {len(personas)} PERSONAS INFECTED BY LUMMA:")
        print("="*50)
        print("PersonaID | First Name | Last Name | OS | Archetype")
        print("-"*50)
        for p in personas:
            print(f"{p.persona_id} | {p.first_name} | {p.last_name} | {p.os} | {p.persona_archetype}")
        print("="*50)
        
        # Save to file for reference
        with open('lumma_infected_personas.txt', 'w') as f:
            f.write("PersonaIDs infected by Lumma (from Infection column):\n")
            f.write(",".join([p.persona_id for p in personas]))
            f.write("\n\nDetails:\n")
            for p in personas:
                f.write(f"{p.persona_id}: {p.first_name} {p.last_name} - {p.os} ({p.persona_archetype})\n")
            f.write(f"\n\nTotal: {len(personas)} personas\n")
    
    def _initialize_generators(self):
        """Initialize all content generators."""
        self.system_generator = SystemInfoGenerator(self.config)
        self.browser_generator = BrowserDataGenerator(self.config)
        self.system_files_generator = SystemFilesGenerator(self.config)
        self.hardware_generator = HardwareGenerator(self.config)
    
    def generate_lumma_log(self, persona: Persona) -> str:
        """Generate complete Lumma log for a persona."""
        logger.info(f"Generating log for {persona.persona_id} - {persona.first_name} {persona.last_name}")
        
        # Create output directory
        hwid = self.hardware_generator.generate_hwid()
        log_dir = os.path.join(self.output_base_dir, f"Lumma_{persona.persona_id}_{hwid}")
        os.makedirs(log_dir, exist_ok=True)
        
        try:
            # Generate System.txt
            self._write_file(log_dir, 'System.txt', self.system_generator.generate(persona))
            
            # Generate browser structure
            browser_profiles = self.browser_generator.generate_browser_structure(persona)
            all_passwords = []
            
            # Process each browser
            for browser, profiles in browser_profiles.items():
                browser_dir = os.path.join(log_dir, browser)
                os.makedirs(browser_dir, exist_ok=True)
                
                # Write Debug.txt
                self._write_file(browser_dir, 'Debug.txt', 
                               self.system_files_generator.generate_debug_txt())
                
                # Process each profile
                for profile in profiles:
                    profile_dir = os.path.join(browser_dir, profile)
                    os.makedirs(profile_dir, exist_ok=True)
                    
                    # Generate passwords
                    passwords = self.browser_generator.generate_passwords(persona, browser, profile)
                    self._write_file(profile_dir, 'Passwords.txt', ''.join(passwords))
                    all_passwords.extend(passwords)
                    
                    # Generate autofills
                    autofills = self.browser_generator.generate_autofills(persona)
                    self._write_file(profile_dir, 'Autofills.txt', ''.join(autofills))
                    
                    # Generate history
                    history = self.browser_generator.generate_history(persona)
                    self._write_file(profile_dir, 'History.txt', ''.join(history))
                    
                    # Generate cookies
                    sites = self.browser_generator._get_sites_for_persona(persona)
                    cookies = self.browser_generator.generate_cookies(persona, sites)
                    self._write_file(profile_dir, 'Cookies_dev.txt', ''.join(cookies))
            
            # Create Cookies directory
            self._consolidate_cookies(log_dir, browser_profiles)
            
            # Write All Passwords.txt
            self._write_file(log_dir, 'All Passwords.txt', ''.join(all_passwords))
            
            # Generate Brute.txt
            brute_content = self._extract_brute_passwords(all_passwords)
            self._write_file(log_dir, 'Brute.txt', brute_content)
            
            # Generate Software.txt
            software = self.system_files_generator.generate_software_txt(persona)
            self._write_file(log_dir, 'Software.txt', '\n'.join(software))
            
            # Generate Processes.txt
            processes = self.system_files_generator.generate_processes_txt(persona)
            self._write_file(log_dir, 'Processes.txt', '\n'.join(processes))
            
            # Generate Clipboard.txt (conditional)
            clipboard_content = self.system_files_generator.generate_clipboard(persona)
            if clipboard_content:
                self._write_file(log_dir, 'Clipboard.txt', clipboard_content)
            
            # Generate GoogleAccounts (conditional)
            google_tokens = self.system_files_generator.generate_google_accounts(persona)
            if google_tokens:
                ga_dir = os.path.join(log_dir, 'GoogleAccounts')
                os.makedirs(ga_dir, exist_ok=True)
                self._write_file(ga_dir, 'Restore_Chrome_Default.txt', '\n'.join(google_tokens))
            
            # Create placeholder Screen.png
            with open(os.path.join(log_dir, 'Screen.png'), 'wb') as f:
                f.write(b'PNG_PLACEHOLDER')
            
            logger.info(f"✓ Generated log in {log_dir}/")
            return log_dir
            
        except Exception as e:
            logger.error(f"Error generating log for {persona.persona_id}: {e}")
            raise
    
    def _write_file(self, directory: str, filename: str, content: str):
        """Write content to a file."""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _consolidate_cookies(self, log_dir: str, browser_profiles: Dict[str, List[str]]):
        """Consolidate cookies from all browsers."""
        cookies_dir = os.path.join(log_dir, 'Cookies')
        os.makedirs(cookies_dir, exist_ok=True)
        
        for browser, profiles in browser_profiles.items():
            for profile in profiles:
                src = os.path.join(log_dir, browser, profile, 'Cookies_dev.txt')
                dst = os.path.join(cookies_dir, f'Cookies_{browser}_dev_{profile}.txt')
                if os.path.exists(src):
                    with open(src, 'r', encoding='utf-8') as f_src:
                        with open(dst, 'w', encoding='utf-8') as f_dst:
                            f_dst.write(f_src.read())
    
    def _extract_brute_passwords(self, all_passwords: List[str]) -> str:
        """Extract passwords only for Brute.txt."""
        brute_passwords = []
        for pwd_entry in all_passwords:
            lines = pwd_entry.strip().split('\n')
            for line in lines:
                if line.startswith('PASS: '):
                    brute_passwords.append(line.replace('PASS: ', ''))
        return '\n'.join(brute_passwords)
    
    def generate_all_lumma_logs(self) -> List[str]:
        """Generate Lumma logs for all assigned personas."""
        generated_logs = []
        
        logger.info("Starting Lumma stealer log generation...")
        logger.info(f"Processing {len(self.personas)} personas infected by Lumma")
        logger.info("-" * 50)
        
        for persona in self.personas:
            try:
                log_dir = self.generate_lumma_log(persona)
                generated_logs.append(log_dir)
            except Exception as e:
                logger.error(f"Failed to generate log for {persona.persona_id}: {e}")
                traceback.print_exc()
        
        logger.info("-" * 50)
        logger.info(f"Successfully generated {len(generated_logs)} Lumma stealer logs")
        return generated_logs


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic Lumma Stealer logs')
    parser.add_argument('csv_file', help='Path to personas CSV file with Infection column')
    parser.add_argument('--config-dir', default='config', help='Configuration directory (default: config)')
    parser.add_argument('--single', help='Generate log for single persona ID')
    
    args = parser.parse_args()
    
    try:
        generator = LummaLogGenerator(args.csv_file, args.config_dir)
        
        if args.single:
            # Find and generate for single persona
            persona = next((p for p in generator.personas if p.persona_id == args.single), None)
            if persona:
                generator.generate_lumma_log(persona)
            else:
                logger.error(f"Persona ID '{args.single}' not found or not infected by Lumma")
        else:
            # Generate all logs
            generator.generate_all_lumma_logs()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
