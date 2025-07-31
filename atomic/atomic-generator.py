#!/usr/bin/env python3
"""
Synthetic Atomic Stealer Log Generator for DEFCON Red Team Village Workshop
Generates realistic but obviously fake stealer logs for educational purposes.

This generator reads personas from a CSV file and generates logs for all personas
where the 'Infection' column contains 'Atomic'. This ensures each persona is only
infected once and respects pre-assigned stealer infections.
"""

import csv
import hashlib
import json
import logging
import os
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

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
    country: str
    city: str
    os: str
    device_type: str
    income_level: str
    primary_browser: str
    secondary_browser: str
    password_habits: str
    persona_archetype: str

    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Persona':
        """Create a Persona instance from a CSV row."""
        return cls(
            persona_id=row['PersonaID'],
            first_name=row['FirstName'],
            last_name=row['LastName'],
            email_personal=row['EmailPersonal'],
            country=row['Country'],
            city=row['City'],
            os=row['OS'],
            device_type=row['DeviceType'],
            income_level=row['IncomeLevel'],
            primary_browser=row['PrimaryBrowser'],
            secondary_browser=row['SecondaryBrowser'],
            password_habits=row['PasswordHabits'],
            persona_archetype=row['PersonaArchetype']
        )


class ConfigurationManager:
    """Manages all configuration data from external files."""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all JSON configuration files from the config directory."""
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Configuration directory '{self.config_dir}' not found. Run setup_configs.py first.")
        
        for config_file in self.config_dir.glob('*.json'):
            config_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.configs[config_name] = json.load(f)
                logger.info(f"Loaded {config_name}.json")
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
                    logger.warning(f"Key path '{config_name}.{'.'.join(keys[:keys.index(key)+1])}' not found")
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
        """Generate realistic Mac hardware based on persona."""
        random.seed(self.get_persona_seed(persona.persona_id, 'hardware'))
        
        # Get hardware config for device type and income level
        hardware_config = self.config.get('hardware', persona.device_type, persona.income_level)
        if not hardware_config:
            # Fallback to default
            hardware_config = self.config.get('hardware', 'Personal_Laptop', 'Medium')
        
        return {
            'model_name': hardware_config['model'],
            'model_id': random.choice(hardware_config['identifier']),
            'chip': random.choice(hardware_config['chip']),
            'cores': random.choice(hardware_config['cores']),
            'memory': random.choice(hardware_config['memory']),
            'display_res': hardware_config['display'],
            'serial_num': self._generate_serial_number(),
            'hardware_uuid': self._generate_hardware_uuid()
        }
    
    def _generate_serial_number(self) -> str:
        """Generate a realistic serial number."""
        length = self.config.get('main', 'generator_settings', 'serial_number_length', default=10)
        chars = self.config.get('charsets', 'serial_number', default='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        return ''.join(random.choices(chars, k=length))
    
    def _generate_hardware_uuid(self) -> str:
        """Generate a realistic hardware UUID."""
        ranges = self.config.get('ranges', 'hardware_uuid')
        parts = []
        for range_config in ranges:
            value = random.randint(range_config['min'], range_config['max'])
            parts.append(f"{value:0{range_config['format']}X}")
        return '-'.join(parts)


class UserInfoGenerator(BaseGenerator):
    """Generates UserInformation.txt content."""
    
    def __init__(self, config: ConfigurationManager):
        super().__init__(config)
        self.hardware_generator = HardwareGenerator(config)
        self.template_renderer = TemplateRenderer(config)
    
    def generate(self, persona: Persona) -> str:
        """Generate UserInformation.txt content."""
        random.seed(self.get_persona_seed(persona.persona_id, 'userinfo'))
        
        hardware = self.hardware_generator.generate(persona)
        ip_address = self._generate_ip_address(persona.country)
        os_info = self._get_os_info(persona.os)
        
        # Use template to format output
        return self.template_renderer.render(
            'user_info',
            stealer_name=self.config.get('main', 'stealer_info', 'name'),
            country=persona.country,
            ip=ip_address,
            ip_suffix=random.randint(100000000, 999999999),
            city=persona.city,
            product_name=os_info['product'],
            product_version=os_info['version'],
            build_version=os_info['build'],
            **hardware,
            firmware_version=self.config.get('constants', 'firmware_version'),
            os_loader_version=self.config.get('constants', 'os_loader_version'),
            provisioning_udid=self.config.get('constants', 'provisioning_udid'),
            metal_support=self.config.get('constants', 'metal_support')
        )
    
    def _generate_ip_address(self, country: str) -> str:
        """Generate IP address based on country."""
        ip_ranges = self.config.get('network', 'country_ip_ranges')
        ip_prefix = ip_ranges.get(country, ip_ranges.get('default'))
        ip_suffix = random.randint(1, 254)
        return f"{ip_prefix}.{ip_suffix}"
    
    def _get_os_info(self, os_name: str) -> Dict[str, str]:
        """Get macOS version information."""
        versions = self.config.get('network', 'macos_versions')
        return versions.get(os_name, versions.get('default'))


class PasswordGenerator(BaseGenerator):
    """Generates password-related content."""
    
    def generate(self, persona: Persona) -> str:
        """Generate Passwords.txt content in correct format."""
        random.seed(self.get_persona_seed(persona.persona_id, 'passwords'))
        
        passwords = []
        all_sites = self._get_sites_for_persona(persona)
        available_passwords = self._get_passwords_for_habit(persona.password_habits)
        
        # Generate password entries based on config
        min_passwords = self.config.get('main', 'generator_settings', 'min_passwords')
        max_passwords = self.config.get('main', 'generator_settings', 'max_passwords')
        num_passwords = random.randint(min_passwords, max_passwords)
        
        for _ in range(num_passwords):
            site = random.choice(all_sites)
            login = self._generate_login(persona)
            password = self._select_password(persona.password_habits, available_passwords)
            
            password_entry = f"URL: {site}\nLOGIN: {login}\nPASSWORD: {password}"
            passwords.append(password_entry)
        
        return '\n'.join(passwords)
    
    def generate_brute(self, passwords_content: str) -> str:
        """Extract passwords for Brute.txt from Passwords.txt content."""
        brute_passwords = []
        for line in passwords_content.split('\n'):
            if line.startswith('PASSWORD: '):
                password = line.replace('PASSWORD: ', '').strip()
                if password:
                    brute_passwords.append(password)
        return '\n'.join(brute_passwords)
    
    def _get_sites_for_persona(self, persona: Persona) -> List[str]:
        """Get websites based on persona type."""
        persona_sites = self.config.get('websites', 'persona_websites', persona.persona_archetype, default=[])
        common_sites = self.config.get('websites', 'common_websites', default=[])
        return persona_sites + common_sites
    
    def _get_passwords_for_habit(self, habit: str) -> List[str]:
        """Get passwords based on password habits."""
        return self.config.get('passwords', habit, default=['DefaultPass123!'])
    
    def _generate_login(self, persona: Persona) -> str:
        """Generate login based on persona."""
        login_types = self.config.get('main', 'login_types', default=['empty', 'email', 'username'])
        weights = self.config.get('main', 'login_weights', default=[1, 1, 1])
        
        login_type = random.choices(login_types, weights=weights)[0]
        
        if login_type == 'empty':
            return ''
        elif login_type == 'email':
            return persona.email_personal
        else:
            return f"{persona.first_name.lower()}{random.randint(100, 999)}"
    
    def _select_password(self, habit: str, available_passwords: List[str]) -> str:
        """Select password based on habit."""
        if habit == 'Reuses_Passwords':
            return available_passwords[0]  # Always use the same password
        else:
            return random.choice(available_passwords)


class CookieGenerator(BaseGenerator):
    """Generates browser cookie files."""
    
    def generate(self, persona: Persona) -> Dict[str, str]:
        """Generate browser-specific cookie files."""
        random.seed(self.get_persona_seed(persona.persona_id, 'cookies'))
        
        cookie_files = {}
        browsers = self._get_browsers_for_persona(persona)
        
        for browser in browsers:
            cookies = self._generate_cookies_for_browser()
            cookie_files[f"{browser}.txt"] = '\n'.join(cookies)
        
        return cookie_files
    
    def _get_browsers_for_persona(self, persona: Persona) -> List[str]:
        """Determine which browsers to generate cookies for."""
        browsers = []
        browser_profiles = self.config.get('browsers', 'profiles')
        
        if persona.primary_browser in browser_profiles:
            browsers.append(browser_profiles[persona.primary_browser]['primary'])
        if persona.secondary_browser in browser_profiles:
            browsers.append(browser_profiles[persona.secondary_browser]['secondary'])
        
        return browsers
    
    def _generate_cookies_for_browser(self) -> List[str]:
        """Generate cookie entries for a browser."""
        cookies = []
        min_cookies = self.config.get('main', 'generator_settings', 'min_cookies', default=5)
        max_cookies = self.config.get('main', 'generator_settings', 'max_cookies', default=12)
        num_cookies = random.randint(min_cookies, max_cookies)
        
        domains = self.config.get('websites', 'cookie_domains', default=['.example.com'])
        names = self.config.get('websites', 'cookie_names', default=['SESSION_ID'])
        
        for _ in range(num_cookies):
            domain = random.choice(domains)
            expiration = self._generate_expiration()
            cookie_name = random.choice(names)
            cookie_value = self._generate_cookie_value()
            
            cookie_line = f"{domain}\tTRUE\t/\tTRUE\t{expiration}\t{cookie_name}\t{cookie_value}"
            cookies.append(cookie_line)
        
        return cookies
    
    def _generate_expiration(self) -> int:
        """Generate cookie expiration timestamp."""
        min_days = self.config.get('main', 'cookie_expiration', 'min_days', default=30)
        max_days = self.config.get('main', 'cookie_expiration', 'max_days', default=365)
        days_ahead = random.randint(min_days, max_days)
        expiration_date = datetime.now() + timedelta(days=days_ahead)
        return int(expiration_date.timestamp())
    
    def _generate_cookie_value(self) -> str:
        """Generate realistic cookie value."""
        length = self.config.get('main', 'generator_settings', 'cookie_value_length', default=120)
        chars = self.config.get('charsets', 'cookie_value', 
                               default='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        return ''.join(random.choices(chars, k=length))


class AutofillGenerator(BaseGenerator):
    """Generates Autofills.txt content."""
    
    def __init__(self, config: ConfigurationManager):
        super().__init__(config)
        self.template_renderer = TemplateRenderer(config)
    
    def generate(self, persona: Persona) -> str:
        """Generate Autofills.txt content."""
        random.seed(self.get_persona_seed(persona.persona_id, 'autofills'))
        
        separator_char = self.config.get('main', 'generator_settings', 'password_separator', default='=')
        separator = separator_char * 50
        
        autofills = []
        fields = self.config.get('autofill', 'fields')
        
        for field in fields:
            value = self._get_field_value(field, persona)
            entry = self.template_renderer.render(
                'autofill_entry',
                name=field['name'],
                value=value,
                separator=separator
            )
            autofills.append(entry)
        
        return '\n'.join(autofills)
    
    def _get_field_value(self, field: Dict[str, str], persona: Persona) -> str:
        """Get the value for a specific autofill field."""
        field_type = field['type']
        
        if field_type == 'persona_field':
            return getattr(persona, field['source'])
        elif field_type == 'generated':
            if field['generator'] == 'phone':
                return self._generate_phone_number()
            elif field['generator'] == 'address':
                return self._generate_address()
        
        return ''
    
    def _generate_phone_number(self) -> str:
        """Generate a realistic phone number."""
        ranges = self.config.get('ranges', 'phone_number')
        area_code = random.randint(ranges['area_code']['min'], ranges['area_code']['max'])
        prefix = random.randint(ranges['prefix']['min'], ranges['prefix']['max'])
        suffix = random.randint(ranges['suffix']['min'], ranges['suffix']['max'])
        return f"({area_code}) {prefix}-{suffix}"
    
    def _generate_address(self) -> str:
        """Generate a realistic street address."""
        street_names = self.config.get('network', 'autofill_street_names', 
                                      default=['Oak St', 'Main Ave', 'Park Blvd', 'First St', 'Maple Dr'])
        num_range = self.config.get('ranges', 'street_number', default={'min': 100, 'max': 9999})
        street_num = random.randint(num_range.get('min', 100), num_range.get('max', 9999))
        street_name = random.choice(street_names)
        return f"{street_num} {street_name}"


class KeychainGenerator(BaseGenerator):
    """Generates keychain.txt content."""
    
    def __init__(self, config: ConfigurationManager):
        super().__init__(config)
        self.template_renderer = TemplateRenderer(config)
    
    def generate(self, persona: Persona) -> str:
        """Generate keychain content."""
        random.seed(self.get_persona_seed(persona.persona_id, 'keychain'))
        
        # Generate Mac OS password
        passwords = self._get_passwords_for_habit(persona.password_habits)
        macos_password = random.choice(passwords)
        
        keychain_content = f"MacOS Password:{macos_password}\n\n"
        
        # Generate keychain entries
        min_entries = self.config.get('main', 'generator_settings', 'min_keychain_entries')
        max_entries = self.config.get('main', 'generator_settings', 'max_keychain_entries')
        num_entries = random.randint(min_entries, max_entries)
        
        services = self.config.get('keychain', 'services')
        selected_services = random.sample(services, min(num_entries, len(services)))
        
        for service in selected_services:
            entry = self._generate_keychain_entry(persona, service)
            keychain_content += entry
        
        return keychain_content
    
    def _get_passwords_for_habit(self, habit: str) -> List[str]:
        """Get passwords based on password habits."""
        return self.config.get('passwords', habit, default=['DefaultPass123!'])
    
    def _generate_keychain_entry(self, persona: Persona, service: Dict[str, str]) -> str:
        """Generate a single keychain entry."""
        # Handle special placeholders
        account = service['account']
        if account == '{email_prefix}':
            account = persona.email_personal.split('@')[0]
        
        # Generate timestamps
        date_ranges = self.config.get('ranges', 'keychain_dates')
        create_days_ago = random.randint(date_ranges['create']['min'], date_ranges['create']['max'])
        modify_days_after = random.randint(date_ranges['modify']['min'], date_ranges['modify']['max'])
        
        create_date = datetime.now() - timedelta(days=create_days_ago)
        modified_date = create_date + timedelta(days=modify_days_after)
        
        # Generate password
        password = self._generate_password_for_type(service['password_type'], persona)
        
        return self.template_renderer.render(
            'keychain_entry',
            create_date=create_date.strftime('%Y-%m-%d %H:%M:%S'),
            modified_date=modified_date.strftime('%Y-%m-%d %H:%M:%S'),
            print_name=service['print_name'],
            account=account,
            service=service['service'],
            password=password
        )
    
    def _generate_password_for_type(self, password_type: str, persona: Persona) -> str:
        """Generate password based on type."""
        password_configs = self.config.get('keychain', 'password_types')
        config = password_configs.get(password_type)
        
        if config['source'] == 'charset':
            chars = self.config.get('charsets', config['charset'])
            length = random.randint(config['min_length'], config['max_length'])
            return ''.join(random.choices(chars, k=length))
        elif config['source'] == 'persona':
            passwords = self._get_passwords_for_habit(persona.password_habits)
            return random.choice(passwords)
        
        return 'DefaultPassword'


class GoogleTokenGenerator(BaseGenerator):
    """Generates GoogleTokens.txt content."""
    
    def generate(self, persona: Persona) -> str:
        """Generate Google tokens."""
        random.seed(self.get_persona_seed(persona.persona_id, 'tokens'))
        
        min_tokens = self.config.get('main', 'generator_settings', 'min_google_tokens')
        max_tokens = self.config.get('main', 'generator_settings', 'max_google_tokens')
        num_tokens = random.randint(min_tokens, max_tokens)
        
        tokens = []
        token_config = self.config.get('tokens', 'google')
        
        for _ in range(num_tokens):
            prefix = token_config['prefix']
            middle_range = token_config['middle_range']
            middle = random.randint(middle_range['min'], middle_range['max'])
            connector = token_config['connector']
            
            suffix_length = self.config.get('main', 'generator_settings', 'token_suffix_length')
            suffix_chars = self.config.get('charsets', 'token_suffix')
            suffix = ''.join(random.choices(suffix_chars, k=suffix_length))
            
            token = f"{prefix}{middle}{connector}{suffix}"
            tokens.append(token)
        
        return '\n'.join(tokens)


class AtomicLogGenerator:
    """Main generator class for Atomic stealer logs."""
    
    def __init__(self, csv_file_path: str, config_dir: str = 'config'):
        self.config = ConfigurationManager(config_dir)
        self.personas = self.load_atomic_personas(csv_file_path)
        self._initialize_generators()
    
    def load_atomic_personas(self, csv_file_path: str) -> List[Persona]:
        """Load personas from CSV where Infection column indicates Atomic."""
        atomic_personas = []
        
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
                
                # Read personas infected by Atomic
                for row in reader:
                    infection_value = row.get(infection_column, '').strip().lower()
                    if infection_value == 'atomic':
                        # Verify it's a Mac user (Atomic only infects macOS)
                        if 'macOS' not in row.get('OS', ''):
                            logger.warning(f"Persona {row['PersonaID']} marked for Atomic but has OS: {row.get('OS')}. Skipping.")
                            continue
                        atomic_personas.append(Persona.from_csv_row(row))
            
            logger.info(f"Found {len(atomic_personas)} personas infected by Atomic")
            
            if not atomic_personas:
                logger.warning("No personas found with Atomic infection. Check the 'Infection' column in your CSV.")
            
            # Log selected personas
            self._log_selected_personas(atomic_personas)
            
            return atomic_personas
            
        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            raise
    
    def _log_selected_personas(self, personas: List[Persona]):
        """Log personas infected by Atomic."""
        print("\n" + "="*50)
        print(f"FOUND {len(personas)} PERSONAS INFECTED BY ATOMIC:")
        print("="*50)
        print("PersonaID | First Name | Last Name | OS | Archetype")
        print("-"*50)
        for p in personas:
            print(f"{p.persona_id} | {p.first_name} | {p.last_name} | {p.os} | {p.persona_archetype}")
        print("="*50)
        
        # Save to file for reference
        with open('atomic_infected_personas.txt', 'w') as f:
            f.write("PersonaIDs infected by Atomic (from Infection column):\n")
            f.write(",".join([p.persona_id for p in personas]))
            f.write("\n\nDetails:\n")
            for p in personas:
                f.write(f"{p.persona_id}: {p.first_name} {p.last_name} - {p.os} ({p.persona_archetype})\n")
            f.write(f"\n\nTotal: {len(personas)} personas\n")
    
    def _initialize_generators(self):
        """Initialize all content generators."""
        self.user_info_generator = UserInfoGenerator(self.config)
        self.password_generator = PasswordGenerator(self.config)
        self.cookie_generator = CookieGenerator(self.config)
        self.autofill_generator = AutofillGenerator(self.config)
        self.keychain_generator = KeychainGenerator(self.config)
        self.token_generator = GoogleTokenGenerator(self.config)
    
    def generate_atomic_log(self, persona: Persona) -> str:
        """Generate complete Atomic stealer log for a persona."""
        logger.info(f"Generating log for {persona.persona_id} - {persona.first_name} {persona.last_name}")
        
        # Create output directory
        log_dir = f"Atomic_{persona.persona_id}_{persona.first_name}_{persona.last_name}"
        os.makedirs(log_dir, exist_ok=True)
        
        file_structure = self.config.get('main', 'file_structure')
        
        try:
            # Generate all components
            self._write_file(log_dir, file_structure['user_info_filename'], 
                           self.user_info_generator.generate(persona))
            
            passwords_content = self.password_generator.generate(persona)
            self._write_file(log_dir, file_structure['passwords_filename'], passwords_content)
            
            brute_content = self.password_generator.generate_brute(passwords_content)
            self._write_file(log_dir, file_structure['brute_filename'], brute_content)
            
            self._write_file(log_dir, file_structure['autofills_filename'], 
                           self.autofill_generator.generate(persona))
            
            self._write_file(log_dir, file_structure['google_tokens_filename'], 
                           self.token_generator.generate(persona))
            
            self._write_file(log_dir, file_structure['keychain_filename'], 
                           self.keychain_generator.generate(persona))
            
            # Generate cookie files
            cookie_files = self.cookie_generator.generate(persona)
            cookies_dir = os.path.join(log_dir, file_structure['cookies_dir'])
            os.makedirs(cookies_dir, exist_ok=True)
            
            for filename, content in cookie_files.items():
                self._write_file(cookies_dir, filename, content)
            
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
    
    def generate_all_atomic_logs(self) -> List[str]:
        """Generate Atomic logs for all assigned personas."""
        generated_logs = []
        
        logger.info("Starting Atomic stealer log generation...")
        logger.info(f"Processing {len(self.personas)} personas infected by Atomic")
        logger.info("-" * 50)
        
        for persona in self.personas:
            try:
                log_dir = self.generate_atomic_log(persona)
                generated_logs.append(log_dir)
            except Exception as e:
                logger.error(f"Failed to generate log for {persona.persona_id}: {e}")
        
        logger.info("-" * 50)
        logger.info(f"Successfully generated {len(generated_logs)} Atomic stealer logs")
        return generated_logs


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic Atomic Stealer logs')
    parser.add_argument('csv_file', help='Path to personas CSV file with Infection column')
    parser.add_argument('--config-dir', default='config', help='Configuration directory (default: config)')
    parser.add_argument('--single', help='Generate log for single persona ID')
    
    args = parser.parse_args()
    
    try:
        generator = AtomicLogGenerator(args.csv_file, args.config_dir)
        
        if args.single:
            # Find and generate for single persona
            persona = next((p for p in generator.personas if p.persona_id == args.single), None)
            if persona:
                generator.generate_atomic_log(persona)
            else:
                logger.error(f"Persona ID '{args.single}' not found or not infected by Atomic")
        else:
            # Generate all logs
            generator.generate_all_atomic_logs()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
