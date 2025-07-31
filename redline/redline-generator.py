#!/usr/bin/env python3
"""
Synthetic RedLine Stealer Log Generator for DEFCON Red Team Village Workshop
Generates realistic but obviously fake stealer logs for educational purposes.

Usage:
1. First run: python setup_redline_configs.py
2. Then run: python redline-generator.py personas.csv
"""

import csv
import hashlib
import json
import logging
import os
import random
import string
import base64
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
	timezone: str
	os: str
	device_type: str
	income_level: str
	primary_browser: str
	secondary_browser: str
	password_habits: str
	persona_archetype: str
	social_media_user: str
	online_shopper: str
	crypto_user: str
	business_access: str
	financial_value: str
	antivirus_type: str
	tech_savviness: str
	download_habits: str
	gaming_user: str

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
			timezone=row.get('Timezone', 'UTC'),
			os=row['OS'],
			device_type=row.get('DeviceType', 'Personal_Laptop'),
			income_level=row.get('IncomeLevel', 'Medium'),
			primary_browser=row.get('PrimaryBrowser', 'Chrome'),
			secondary_browser=row.get('SecondaryBrowser', 'None'),
			password_habits=row.get('PasswordHabits', 'Mixed'),
			persona_archetype=row.get('PersonaArchetype', 'General'),
			social_media_user=row.get('SocialMediaUser', 'Light'),
			online_shopper=row.get('OnlineShopper', 'Light'),
			crypto_user=row.get('CryptoUser', 'None'),
			business_access=row.get('BusinessAccess', 'No'),
			financial_value=row.get('FinancialValue', 'Low'),
			antivirus_type=row.get('AntivirusType', 'Windows Defender'),
			tech_savviness=row.get('TechSavviness', 'Medium'),
			download_habits=row.get('DownloadHabits', 'Moderate'),
			gaming_user=row.get('GamingUser', 'None')
		)


class ConfigurationManager:
	"""Manages all configuration data from external files."""
	
	def __init__(self, config_dir: str = 'config'):
		self.config_dir = Path(config_dir)
		self.configs = {}
		self._value_mappings = {}
		self._load_all_configs()
		self._build_value_mappings()
	
	def _load_all_configs(self):
		"""Load all JSON configuration files from the config directory."""
		redline_config_dir = self.config_dir / 'redline'
		
		if not redline_config_dir.exists():
			logger.error(f"Configuration directory '{redline_config_dir}' not found!")
			logger.error("Please run 'python setup_redline_configs.py' first to create configuration files.")
			raise FileNotFoundError(f"Configuration directory '{redline_config_dir}' not found. Run setup_redline_configs.py first.")
		
		for config_file in redline_config_dir.glob('*.json'):
			config_name = config_file.stem
			try:
				with open(config_file, 'r', encoding='utf-8') as f:
					self.configs[config_name] = json.load(f)
				logger.debug(f"Loaded redline/{config_name}.json")
			except Exception as e:
				logger.error(f"Error loading {config_file}: {e}")
				raise
	
	def _build_value_mappings(self):
		"""Build mappings to normalize values between CSV and configs."""
		# Device type mappings
		self._value_mappings['device_type'] = {
			'personal laptop': 'Personal_Laptop',
			'personal_laptop': 'Personal_Laptop',
			'personallaptop': 'Personal_Laptop',
			'laptop': 'Personal_Laptop',
			'gaming rig': 'Gaming_Rig',
			'gaming_rig': 'Gaming_Rig',
			'gamingrig': 'Gaming_Rig',
			'gaming': 'Gaming_Rig',
			'office desktop': 'Office_Desktop',
			'office_desktop': 'Office_Desktop',
			'officedesktop': 'Office_Desktop',
			'desktop': 'Office_Desktop',
			'office': 'Office_Desktop'
		}
		
		# Income level mappings
		self._value_mappings['income_level'] = {
			'low': 'Low',
			'medium': 'Medium',
			'high': 'High',
			'l': 'Low',
			'm': 'Medium',
			'h': 'High'
		}
	
	def normalize_value(self, value: str, value_type: str) -> str:
		"""Normalize a value using the mappings."""
		if value_type not in self._value_mappings:
			return value
		
		normalized = value.lower().strip()
		mapping = self._value_mappings[value_type]
		
		return mapping.get(normalized, value)
	
	def get(self, config_name: str, *keys, default=None):
		"""Get a configuration value by name and nested keys with normalization."""
		try:
			value = self.configs.get(config_name)
			if value is None:
				logger.warning(f"Configuration '{config_name}' not found, using default")
				return default
			
			# Special handling for hardware config
			if config_name == 'hardware' and len(keys) >= 2:
				device_type = self.normalize_value(str(keys[0]), 'device_type')
				income_level = self.normalize_value(str(keys[1]), 'income_level')
				
				# Try normalized values
				if device_type in value and income_level in value[device_type]:
					return value[device_type][income_level]
				
				# Log what we're looking for vs what's available
				logger.warning(f"Hardware config not found for {device_type}/{income_level}")
				logger.debug(f"Available device types: {list(value.keys())}")
				
				# Return default
				return default
			
			# Normal navigation for other configs
			for key in keys:
				if isinstance(value, dict):
					value = value.get(key)
				elif isinstance(value, list) and isinstance(key, int):
					if 0 <= key < len(value):
						value = value[key]
					else:
						return default
				else:
					return default
					
				if value is None:
					return default
					
			return value
		except Exception as e:
			logger.error(f"Error accessing config {config_name}.{'.'.join(map(str, keys))}: {e}")
			return default


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


class HardwareGenerator(BaseGenerator):
	"""Generates hardware information for personas."""
	
	def generate(self, persona: Persona) -> Dict[str, str]:
		"""Generate realistic Windows hardware based on persona."""
		random.seed(self.get_persona_seed(persona.persona_id, 'hardware'))
		
		# Get hardware config with normalization
		hardware_config = self.config.get('hardware', persona.device_type, persona.income_level)
		
		if not hardware_config:
			logger.warning(f"Using default hardware for {persona.device_type}/{persona.income_level}")
			hardware_config = {
				'cpu': ['Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz'],
				'gpu': ['Intel(R) UHD Graphics 630'],
				'ram': ['8192 MB'],
				'resolution': ['1920x1080x32']
			}
		
		return {
			'cpu': random.choice(hardware_config.get('cpu', ['Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz'])),
			'gpu': random.choice(hardware_config.get('gpu', ['Intel(R) UHD Graphics 630'])),
			'ram': random.choice(hardware_config.get('ram', ['8192 MB'])),
			'resolution': random.choice(hardware_config.get('resolution', ['1920x1080x32']))
		}
	
	def generate_computer_id(self) -> str:
		"""Generate random computer ID."""
		chars = self.config.get('charsets', 'computer_id', default='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
		length = self.config.get('main', 'generator_settings', 'computer_id_length', default=8)
		return ''.join(random.choices(chars, k=length))
	
	def generate_hwid(self) -> str:
		"""Generate hardware ID."""
		return hashlib.md5(str(random.random()).encode()).hexdigest().upper()[:32]
	
	def generate_log_id(self) -> str:
		"""Generate RedLine log ID format."""
		return hashlib.md5(str(random.random()).encode()).hexdigest().upper()[:8]


class NetworkGenerator:
	"""Generates network-related information."""
	
	def __init__(self, config: ConfigurationManager):
		self.config = config
	
	def generate_ip_for_country(self, country: str) -> str:
		"""Generate IP address based on country."""
		ip_ranges = self.config.get('network', 'country_ip_ranges', default={})
		
		if country in ip_ranges:
			ip_config = ip_ranges[country]
			if isinstance(ip_config, dict) and 'prefixes' in ip_config:
				prefix = random.choice(ip_config['prefixes'])
				return f"{prefix}.{random.randint(0,255)}.{random.randint(1,254)}"
		
		# Default fallback
		return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
	
	def get_language_for_country(self, country: str) -> str:
		"""Get language for country."""
		languages = self.config.get('network', 'country_languages', default={})
		return languages.get(country, 'en-US')


class SystemInfoGenerator(BaseGenerator):
	"""Generates UserInformation.txt content in authentic RedLine format."""
	
	def __init__(self, config: ConfigurationManager):
		super().__init__(config)
		self.hardware_generator = HardwareGenerator(config)
		self.network_generator = NetworkGenerator(config)
	
	def generate(self, persona: Persona) -> str:
		"""Generate UserInformation.txt content matching RedLine format."""
		random.seed(self.get_persona_seed(persona.persona_id, 'system'))
		
		# Generate components
		content = []
		
		# ASCII art header
		content.append(self._generate_header())
		content.append("")
		
		# Build ID
		build_ids = self.config.get('redline', 'build_ids', default=['@hitok4111', '@hydroshot'])
		build_id = random.choice(build_ids)
		content.append(f"Build ID: {build_id}")
		
		# IP
		ip = self.network_generator.generate_ip_for_country(persona.country)
		content.append(f"IP: {ip}")
		
		# FileLocation - execution path
		exe_names = self.config.get('redline', 'executable_names', default=['MSBuild.exe', 'RegAsm.exe'])
		exe_name = random.choice(exe_names)
		
		dotnet_exes = self.config.get('redline', 'dotnet_executables', default=['MSBuild.exe', 'vbc.exe'])
		if exe_name in dotnet_exes:
			file_location = f"C:\\Windows\\Microsoft.NET\\Framework\\v4.0.30319\\{exe_name}"
		else:
			temp_id = random.randint(100000, 999999)
			file_location = f"C:\\Users\\{persona.first_name}\\AppData\\Local\\Temp\\{temp_id}\\{exe_name}"
		content.append(f"FileLocation: {file_location}")
		
		# UserName
		content.append(f"UserName: {persona.first_name}")
		
		# MachineName (appears in most samples)
		computer_id = self.hardware_generator.generate_computer_id()
		content.append(f"MachineName: DESKTOP-{computer_id}")
		
		# Country
		content.append(f"Country: {persona.country}")
		
		# Zip Code
		zip_code = self._generate_zip_code(persona.country)
		content.append(f"Zip Code: {zip_code}")
		
		# Location
		state = self._get_state_for_city(persona.city, persona.country)
		content.append(f"Location: {persona.city}, {state}")
		
		# HWID
		hwid = self.hardware_generator.generate_hwid().upper()
		content.append(f"HWID: {hwid}")
		
		# Current Language
		language = self._get_language_display_name(persona.country)
		content.append(f"Current Language: {language}")
		
		# ScreenSize
		hardware = self.hardware_generator.generate(persona)
		resolution = hardware['resolution'].split('x')
		width, height = resolution[0], resolution[1].split('x')[0] if 'x' in resolution[1] else resolution[1]
		content.append(f"ScreenSize: {{Width={width}, Height={height}}}")
		
		# TimeZone
		timezone_display = self._get_timezone_display(persona.timezone)
		content.append(f"TimeZone: {timezone_display}")
		
		# Operation System
		os_display = self._format_os_display(persona.os)
		content.append(f"Operation System: {os_display}")
		
		# UAC (only sometimes included)
		uac_probability = self.config.get('redline', 'field_probabilities', 'uac', default=0.3)
		if random.random() < uac_probability:
			uac_values = self.config.get('redline', 'uac_values', default=['AllowAll', 'RequireAdmin', 'Default'])
			content.append(f"UAC: {random.choice(uac_values)}")
		
		# Process Elevation (only sometimes included)
		elevation_probability = self.config.get('redline', 'field_probabilities', 'process_elevation', default=0.3)
		if random.random() < elevation_probability:
			content.append(f"Process Elevation: {random.choice(['True', 'False'])}")
		
		# Log date
		log_date = datetime.now().strftime("%-m/%-d/%Y %-I:%M:%S %p")
		content.append(f"Log date: {log_date}")
		
		content.append("")
		
		# Available KeyboardLayouts
		content.append("Available KeyboardLayouts: ")
		keyboards = self._get_keyboard_layouts(persona.country)
		for kb in keyboards:
			content.append(kb)
		
		content.append("")
		content.append("")
		
		# Hardwares
		content.append("Hardwares: ")
		
		# RAM (listed first in samples)
		ram_mb = int(hardware['ram'].replace(' MB', ''))
		ram_bytes = ram_mb * 1024 * 1024
		# Some use "Mb", some use "MB"
		mb_suffixes = self.config.get('redline', 'ram_suffixes', default=['Mb', 'MB'])
		mb_suffix = random.choice(mb_suffixes)
		content.append(f"Name: Total of RAM, {ram_mb:.2f} {mb_suffix} or {ram_bytes} bytes")
		
		# CPU
		cpu_cores = self._get_cpu_cores(hardware['cpu'])
		content.append(f"Name: {hardware['cpu']}, {cpu_cores} Cores")
		
		# GPU
		gpu_bytes = self._get_gpu_memory(hardware['gpu'])
		content.append(f"Name: {hardware['gpu']}, {gpu_bytes} bytes")
		
		content.append("")
		content.append("")
		
		# Anti-Viruses
		content.append("Anti-Viruses: ")
		av_list = self._get_antivirus_list(persona)
		for av in av_list:
			content.append(av)
		
		return '\n'.join(content)
	
	def _generate_header(self) -> str:
		"""Generate ASCII art header for RedLine."""
		headers = self.config.get('redline', 'ascii_headers', default=[])
		if not headers:
			# Fallback header
			headers = ["""***********************************************
*  Telegram: https://t.me/redline_market_bot  *
***********************************************"""]
		
		return random.choice(headers)
	
	def _generate_zip_code(self, country: str) -> str:
		"""Generate appropriate zip code for country."""
		zip_formats = self.config.get('redline', 'zip_code_formats', default={})
		
		if country in zip_formats:
			format_config = zip_formats[country]
			if isinstance(format_config, dict):
				if format_config.get('type') == 'numeric':
					return f"{random.randint(format_config['min'], format_config['max'])}"
				elif format_config.get('type') == 'canadian':
					letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
					return f"{random.choice(letters)}{random.randint(0,9)}{random.choice(letters)} {random.randint(0,9)}{random.choice(letters)}{random.randint(0,9)}"
				elif format_config.get('type') == 'uk':
					return f"{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.randint(1,99)} {random.randint(1,9)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
				elif format_config.get('type') == 'portuguese':
					return f"{random.randint(1000, 9999)}-{random.randint(100, 999)}"
				elif format_config.get('type') == 'japanese':
					return f"{random.randint(100, 999)}-{random.randint(1000, 9999)}"
			else:
				return format_config
		
		# Default behavior
		return random.choice(['UNKNOWN', f"{random.randint(10000, 99999)}"])
	
	def _get_state_for_city(self, city: str, country: str) -> str:
		"""Get state/region for city."""
		city_states = self.config.get('redline', 'city_state_mapping', default={})
		
		if country in city_states and city in city_states[country]:
			return city_states[country][city]
		
		# Return city as fallback
		return city
	
	def _get_language_display_name(self, country: str) -> str:
		"""Get display name for language based on country."""
		language_map = self.config.get('redline', 'country_languages', default={})
		return language_map.get(country, 'English (United States)')
	
	def _get_timezone_display(self, timezone: str) -> str:
		"""Convert timezone to Windows display format."""
		tz_map = self.config.get('redline', 'timezone_display_names', default={})
		
		# Handle special cases
		if timezone in ['AST', 'Arabia Standard Time']:
			return '(UTC+03:00) Baghdad'
		
		return tz_map.get(timezone, '(UTC+00:00) Coordinated Universal Time')
	
	def _format_os_display(self, os_version: str) -> str:
		"""Format OS version for display."""
		# Add x64 architecture if not present
		if 'x64' not in os_version and 'x86' not in os_version:
			return f"{os_version} x64"
		return os_version
	
	def _get_keyboard_layouts(self, country: str) -> List[str]:
		"""Get keyboard layouts for country."""
		layouts = self.config.get('redline', 'keyboard_layouts', default={})
		return layouts.get(country, ['English (United States)'])
	
	def _get_cpu_cores(self, cpu_name: str) -> int:
		"""Extract or determine CPU core count."""
		cpu_cores = self.config.get('redline', 'cpu_core_mapping', default={})
		
		# Check for matches in CPU name
		for pattern, cores in cpu_cores.items():
			if pattern in cpu_name:
				if isinstance(cores, list):
					return random.choice(cores)
				else:
					return cores
		
		# Default
		return random.choice([2, 4, 6])
	
	def _get_gpu_memory(self, gpu_name: str) -> int:
		"""Get GPU memory in bytes."""
		gpu_memory = self.config.get('redline', 'gpu_memory_bytes', default={})
		
		# Check GPU name against known models
		for model, memory in gpu_memory.items():
			if model in gpu_name:
				return memory
		
		# Default for unknown GPUs
		return 4294967296  # 4GB default
	
	def _get_antivirus_list(self, persona: Persona) -> List[str]:
		"""Generate antivirus list based on persona."""
		# Windows Defender is always present
		av_list = ['Windows Defender']
		
		# Add additional AV based on persona attributes
		if persona.antivirus_type and persona.antivirus_type != 'Windows Defender':
			av_list.append(persona.antivirus_type)
			
			# Check for firewall components
			firewall_map = self.config.get('redline', 'antivirus_firewall_names', default={})
			if persona.antivirus_type in firewall_map:
				av_list.append(firewall_map[persona.antivirus_type])
		
		# Tech-savvy users might have additional security
		if persona.tech_savviness == 'High' and random.random() > 0.5:
			additional_avs = self.config.get('redline', 'additional_antivirus', default=[
				'Malwarebytes',
				'360 Total Security'
			])
			additional_av = random.choice(additional_avs)
			if additional_av not in av_list:
				av_list.append(additional_av)
		
		return av_list


class AutofillGenerator(BaseGenerator):
	"""Generates autofill content."""
	
	def __init__(self, config: ConfigurationManager):
		super().__init__(config)
		self.template_renderer = TemplateRenderer(config)
	
	def get_header(self) -> str:
		"""Get the META header for autofill files."""
		return self.config.get('main', 'meta_header', default='META_DATA\n')
	
	def generate(self, persona: Persona, browser_profile: str) -> str:
		"""Generate autofill content for a specific browser profile."""
		random.seed(self.get_persona_seed(persona.persona_id, f'autofill_{browser_profile}'))
		
		entries = []
		
		# Get field names
		field_names = self.config.get('autofill', 'field_names', default=[
			'email', 'username', 'login', 'user', 'emailAddress'
		])
		
		# Build values pool
		values_pool = self._build_values_pool(persona)
		
		# Generate entries
		ranges = self.config.get('ranges', 'autofill_entries', default={'min': 50, 'max': 100})
		num_entries = random.randint(ranges['min'], ranges['max'])
		
		for _ in range(num_entries):
			field = random.choice(field_names)
			value = random.choice(values_pool)
			
			entry = self.template_renderer.render(
				'autofill_entry',
				field=field,
				value=value
			)
			if not entry:  # Fallback if template not found
				entry = f'Field: {field} | Value: {value}'
			entries.append(entry)
		
		# Add header and join entries
		return self.get_header() + '\n'.join(entries) + '\n'
	
	def generate_important(self, persona: Persona) -> str:
		"""Generate ImportantAutofills.txt content."""
		random.seed(self.get_persona_seed(persona.persona_id, 'important_autofills'))
		
		entries = []
		
		# Create email variations
		emails = [persona.email_personal]
		if persona.email_work:
			emails.append(persona.email_work)
		
		# Add persona-specific emails
		email_templates = self.config.get('autofill', 'email_templates', default={})
		for archetype, templates in email_templates.items():
			if archetype in persona.persona_archetype:
				for template in templates:
					email = template.replace('{first_name}', persona.first_name.lower())
					email = email.replace('{last_name}', persona.last_name.lower())
					email = email.replace('{number}', str(random.randint(100, 9999)))
					email = email.replace('{year}', str(random.randint(20, 24)))
					emails.append(email)
		
		# Field patterns
		field_patterns = self.config.get('autofill', 'important_field_patterns', default=[
			'email', 'login[email]', 'user[email]'
		])
		
		# Generate entries
		ranges = self.config.get('ranges', 'important_autofill_entries', default={'min': 10, 'max': 20})
		num_entries = random.randint(ranges['min'], ranges['max'])
		
		used_fields = set()
		for _ in range(num_entries):
			available_fields = [f for f in field_patterns if f not in used_fields]
			if not available_fields:
				available_fields = field_patterns
			
			field = random.choice(available_fields)
			used_fields.add(field)
			
			selected_email = random.choice(emails)
			
			# Sometimes truncate for emailOrPhone fields
			if field == 'emailOrPhone' and random.random() > 0.5:
				selected_email = selected_email.split('@')[0]
			
			entries.append(f"{field}: {selected_email}")
		
		return self.get_header() + '\n'.join(entries) + '\n'
	
	def _build_values_pool(self, persona: Persona) -> List[str]:
		"""Build pool of autofill values based on persona."""
		values_pool = [persona.email_personal]
		
		# Add username variations
		if '@' in persona.email_personal:
			username_part = persona.email_personal.split('@')[0]
			values_pool.extend([
				username_part,
				f"{persona.first_name.lower()}{persona.last_name.lower()}",
				f"{persona.first_name.lower()}.{persona.last_name.lower()}",
				f"{persona.first_name.lower()}_{persona.last_name.lower()}",
				f"{persona.first_name.lower()}{random.randint(100, 999)}"
			])
		
		if persona.email_work:
			values_pool.append(persona.email_work)
			if '@' in persona.email_work:
				values_pool.append(persona.email_work.split('@')[0])
		
		# Add archetype-specific usernames
		archetype_usernames = self.config.get('autofill', 'archetype_usernames', default={})
		for archetype, templates in archetype_usernames.items():
			if archetype in persona.persona_archetype:
				for template in templates:
					username = template.replace('{first_name}', persona.first_name)
					username = username.replace('{last_name}', persona.last_name)
					username = username.replace('{number}', str(random.randint(100, 999)))
					username = username.replace('{suffix}', random.choice(['YT', 'TTV', 'GG']))
					values_pool.append(username)
		
		# Ensure we have at least some values
		if len(values_pool) < 5:
			values_pool.extend([
				f"user{random.randint(1000, 9999)}",
				f"{persona.first_name.lower()}123",
				f"test_{persona.last_name.lower()}"
			])
		
		return values_pool


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
		"""Determine which browsers and profiles to generate for persona."""
		browser_profiles = []
		
		# Browser mapping
		browser_mapping = self.config.get('browsers', 'browser_mapping', default={
			'Chrome': 'Google_[Chrome]',
			'Firefox': 'Mozilla_[Firefox]',
			'Edge': 'Microsoft_[Edge]'
		})
		
		# Primary browser
		if persona.primary_browser and persona.primary_browser != 'None':
			browser_name = browser_mapping.get(persona.primary_browser, persona.primary_browser)
			if browser_name:  # Check if not None
				# Determine number of profiles
				profiles_count = 1
				if persona.primary_browser == 'Chrome':
					if persona.social_media_user == 'Heavy':
						profiles_count = random.randint(2, 5)
					elif persona.business_access == 'Yes':
						profiles_count = random.randint(2, 3)
				
				browser_profiles.append((browser_name, 'Default'))
				
				# Additional profiles
				profile_numbers = self.config.get('browsers', 'chrome_profile_numbers', default=[1, 2, 4, 5])
				for i in range(1, profiles_count):
					profile_num = random.choice(profile_numbers)
					browser_profiles.append((browser_name, f'Profile {profile_num}'))
		
		# Secondary browser
		if persona.secondary_browser and persona.secondary_browser != 'None':
			browser_name = browser_mapping.get(persona.secondary_browser, persona.secondary_browser)
			if browser_name:  # Check if not None
				# Check if not already added
				if not any(bp[0] == browser_name and bp[1] == 'Default' for bp in browser_profiles):
					browser_profiles.append((browser_name, 'Default'))
		
		# Gaming users might have Opera GX
		if persona.gaming_user == 'Heavy' and random.random() > 0.6:
			browser_profiles.append(('Opera GX', 'Default'))
		
		# Ensure we always have at least one browser
		if not browser_profiles:
			browser_profiles.append(('Google_[Chrome]', 'Default'))
		
		return browser_profiles
	
	def generate_cookies(self, persona: Persona, browser_profile: str, cookie_type: str = 'Network') -> Tuple[str, List[str]]:
		"""Generate cookies and return content and domains."""
		random.seed(self.get_persona_seed(persona.persona_id, f'cookies_{browser_profile}_{cookie_type}'))
		
		cookies = []
		domains_found = []
		
		# Get base domains
		base_domains = self.config.get('websites', 'common_domains', default=[
			'.google.com', '.youtube.com', '.facebook.com', '.amazon.com'
		]).copy()
		
		# Add archetype-specific domains
		archetype_domains = self.config.get('websites', 'archetype_domains', persona.persona_archetype, default=[])
		if archetype_domains:
			base_domains.extend(archetype_domains)
		
		# Add crypto domains if applicable
		if persona.crypto_user != 'None':
			crypto_domains = self.config.get('websites', 'crypto_domains', default=[])
			if crypto_domains:
				base_domains.extend(crypto_domains)
		
		# Generate cookies
		ranges = self.config.get('ranges', 'cookie_count', default={'min': 45, 'max': 55})
		num_cookies = random.randint(ranges['min'], ranges['max'])
		
		for _ in range(num_cookies):
			domain = random.choice(base_domains)
			domains_found.append(domain)
			
			# Cookie properties
			include_subdomains = 'TRUE' if random.random() > 0.2 else 'FALSE'
			path = '/'
			secure = 'TRUE' if random.random() > 0.3 else 'FALSE'
			
			# Expiry
			expiry_range = self.config.get('ranges', 'cookie_expiry_days', default={'min': 30, 'max': 730})
			days_ahead = random.randint(expiry_range['min'], expiry_range['max'])
			expiry = int((datetime.now() + timedelta(days=days_ahead)).timestamp())
			
			# Cookie name and value
			cookie_name, cookie_value = self._generate_cookie_data(domain, cookie_type)
			
			cookie_line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{cookie_name}\t{cookie_value}"
			cookies.append(cookie_line)
		
		return '\n'.join(cookies) + '\n', domains_found
	
	def _generate_cookie_data(self, domain: str, cookie_type: str) -> Tuple[str, str]:
		"""Generate cookie name and value based on domain."""
		site_cookies = self.config.get('cookies', 'site_specific', default={})
		
		# Find matching site config
		for site, cookie_config in site_cookies.items():
			if site in domain:
				names = cookie_config.get('names', ['session_id'])
				cookie_name = random.choice(names)
				
				# Generate value based on type
				value = self._generate_cookie_value(cookie_config.get('value_type', 'generic'))
				
				return cookie_name, value
		
		# Generic cookies
		if cookie_type == 'Extension':
			generic_names = self.config.get('cookies', 'extension_names', default=['ext_session'])
		else:
			generic_names = self.config.get('cookies', 'generic_names', default=['session_id'])
		
		return random.choice(generic_names), self._generate_cookie_value('generic')
	
	def _generate_cookie_value(self, value_type: str) -> str:
		"""Generate cookie value based on type."""
		value_configs = self.config.get('cookies', 'value_types', default={})
		
		if value_type in value_configs:
			config = value_configs[value_type]
			chars = self.config.get('charsets', config.get('charset', 'alphanumeric'), 
								  default=string.ascii_letters + string.digits)
			length = random.randint(config.get('min_length', 16), config.get('max_length', 64))
			
			if config.get('numeric', False) and random.random() > 0.5:
				return str(random.randint(10**(length-1), 10**length-1))
			else:
				return ''.join(random.choices(chars, k=length))
		else:
			# Default generic
			return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(16, 64)))
	
	def generate_passwords(self, persona: Persona, browser_profiles: List[Tuple[str, str]]) -> Tuple[str, List[str]]:
		"""Generate Passwords.txt content and return domains found."""
		random.seed(self.get_persona_seed(persona.persona_id, 'passwords'))
		
		entries = []
		domains_found = []
		
		# Get base URLs
		base_urls = self.config.get('passwords', 'base_urls', default={
			'google.com': ['https://accounts.google.com'],
			'facebook.com': ['https://www.facebook.com/']
		}).copy()
		
		# Add archetype-specific URLs
		archetype_urls = self.config.get('passwords', 'archetype_urls', persona.persona_archetype, default={})
		if archetype_urls:
			base_urls.update(archetype_urls)
		
		# Add crypto URLs if applicable
		if persona.crypto_user != 'None':
			crypto_urls = self.config.get('passwords', 'crypto_urls', default={})
			if crypto_urls:
				base_urls.update(crypto_urls)
		
		# Add financial URLs for high-value targets
		if persona.financial_value == 'High':
			financial_urls = self.config.get('passwords', 'financial_urls', default={})
			if financial_urls:
				base_urls.update(financial_urls)
		
		# Generate passwords based on habits
		passwords = self._generate_password_list(persona)
		
		# Generate entries
		ranges = self.config.get('ranges', 'password_entries', default={'min': 20, 'max': 50})
		num_passwords = random.randint(ranges['min'], ranges['max'])
		
		header = self.config.get('main', 'meta_header', default='META_DATA\n')
		
		for _ in range(num_passwords):
			# Pick domain and URL
			domain = random.choice(list(base_urls.keys()))
			url = random.choice(base_urls[domain])
			domains_found.append(domain)
			
			# Generate username
			username = self._generate_username(persona, domain)
			
			# Pick password
			if persona.password_habits == 'Reuses_Passwords':
				password = passwords[0] if passwords else 'Password123!'
			else:
				password = random.choice(passwords) if passwords else 'Password123!'
			
			# Pick browser application
			if browser_profiles:
				app = random.choice([f"{bp[0]}_{bp[1].replace(' ', '_')}" for bp in browser_profiles])
			else:
				app = "Google_[Chrome]_Default"
			
			entry = self.template_renderer.render(
				'password_entry',
				url=url,
				username=username,
				password=password,
				application=app
			)
			if not entry:  # Fallback if template not found
				entry = f'''URL: {url}
Username: {username}
Password: {password}
Application: {app}
'''
			entries.append(entry)
		
		return header + '\n'.join(entries) + '\n', domains_found
	
	def _generate_password_list(self, persona: Persona) -> List[str]:
		"""Generate list of passwords based on persona habits."""
		patterns = self.config.get('passwords', 'patterns', persona.password_habits, default=None)
		
		# If no patterns found for this habit, use default
		if patterns is None:
			patterns = self.config.get('passwords', 'patterns', 'default', 
									 default=['{first_name}123!', 'Password123!'])
		
		if persona.password_habits == 'Reuses_Passwords':
			# Generate one password and use it everywhere
			pattern = patterns[0] if patterns else '{first_name}{year}!'
			password = self._expand_password_pattern(pattern, persona)
			return [password] * 10
		elif persona.password_habits == 'Good_Hygiene':
			# Generate unique strong passwords
			passwords = []
			chars = self.config.get('charsets', 'strong_password', 
								  default=string.ascii_letters + string.digits + '!@#$%^&*')
			for _ in range(20):
				length = random.randint(12, 20)
				passwords.append(''.join(random.choices(chars, k=length)))
			return passwords
		else:
			# Mixed approach
			passwords = []
			for pattern in patterns:
				passwords.append(self._expand_password_pattern(pattern, persona))
			
			# Ensure we have at least some passwords
			if not passwords:
				passwords = [
					f"{persona.first_name}123!",
					"Password123!",
					f"{persona.last_name}2024"
				]
			
			return passwords
	
	def _expand_password_pattern(self, pattern: str, persona: Persona) -> str:
		"""Expand password pattern with persona data."""
		password = pattern
		password = password.replace('{first_name}', persona.first_name)
		password = password.replace('{last_name}', persona.last_name)
		password = password.replace('{year}', str(random.randint(2020, 2024)))
		password = password.replace('{number}', str(random.randint(100, 999)))
		return password
	
	def _generate_username(self, persona: Persona, domain: str) -> str:
		"""Generate username for a specific domain."""
		username_type = random.choice(['email', 'username', 'unknown'])
		
		if username_type == 'unknown':
			return 'UNKNOWN'
		elif username_type == 'email':
			return persona.email_personal if random.random() > 0.3 else (persona.email_work or 'UNKNOWN')
		else:
			# Generate username based on site
			site_usernames = self.config.get('passwords', 'site_usernames', default={})
			
			for site, templates in site_usernames.items():
				if site in domain:
					template = random.choice(templates)
					username = template.replace('{first_name}', persona.first_name.lower())
					username = username.replace('{last_name}', persona.last_name.lower())
					username = username.replace('{number}', str(random.randint(100, 999)))
					return username
			
			# Default username
			return f"{persona.first_name.lower()}{random.randint(100, 999)}"
	
	def generate_user_agents(self, persona: Persona, browser: str) -> str:
		"""Generate UserAgent file for a browser."""
		random.seed(self.get_persona_seed(persona.persona_id, f'useragent_{browser}'))
		
		user_agents = self.config.get('browsers', 'user_agents', default={})
		
		if browser in user_agents:
			return random.choice(user_agents[browser]) + '\n'
		else:
			# Default Chrome user agent
			default_ua = self.config.get('browsers', 'default_user_agent', 
									   default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
			return default_ua + '\n'
	
	def generate_restore_cookies(self, persona: Persona, browser_profile: str) -> str:
		"""Generate Fresh Cookies for /Restore/ directory."""
		random.seed(self.get_persona_seed(persona.persona_id, f'restore_{browser_profile}'))
		
		cookies = []
		
		# Get auth sites configuration
		auth_sites = self.config.get('cookies', 'auth_sites', default={
			'accounts.google.com': {'cookies': ['SID', 'HSID', 'SSID']},
			'.facebook.com': {'cookies': ['c_user', 'xs']}
		}).copy()
		
		# Add crypto sites if applicable
		if persona.crypto_user != 'None':
			crypto_auth = self.config.get('cookies', 'crypto_auth_sites', default={})
			if crypto_auth:
				auth_sites.update(crypto_auth)
		
		# Add gaming sites if applicable
		if 'Gaming' in persona.persona_archetype:
			gaming_auth = self.config.get('cookies', 'gaming_auth_sites', default={})
			if gaming_auth:
				auth_sites.update(gaming_auth)
		
		# Generate fresh cookies
		ranges = self.config.get('ranges', 'restore_cookies', default={'min': 3, 'max': 8})
		num_sites = random.randint(ranges['min'], ranges['max'])
		
		selected_sites = random.sample(list(auth_sites.keys()), min(num_sites, len(auth_sites)))
		
		for site in selected_sites:
			site_info = auth_sites[site]
			
			# Generate cookies for this site
			cookies_list = site_info.get('cookies', ['session_id'])
			num_cookies = random.randint(1, min(3, len(cookies_list)))
			selected_cookies = random.sample(cookies_list, num_cookies)
			
			for cookie_name in selected_cookies:
				# Generate auth token value
				value = self._generate_auth_token()
				
				# Cookie properties
				include_subdomains = 'TRUE'
				path = '/'
				secure = 'TRUE' if random.random() > 0.3 else 'FALSE'
				expiry = random.randint(1800000000, 1900000000)	 # Year 2027
				
				cookie_line = f"{site}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{cookie_name}\t{value}"
				cookies.append(cookie_line)
		
		return '\n'.join(cookies) + '\n'
	
	def _generate_auth_token(self) -> str:
		"""Generate generic auth token."""
		chars = self.config.get('charsets', 'auth_token', 
							  default=string.ascii_letters + string.digits + '-_')
		length = random.randint(60, 150)
		return ''.join(random.choices(chars, k=length))
	
	def generate_restore_tokens(self, persona: Persona, browser_profile: str) -> str:
		"""Generate Token.txt files for /Restore/ directory."""
		random.seed(self.get_persona_seed(persona.persona_id, f'token_{browser_profile}'))
		
		tokens = []
		
		# Google OAuth refresh tokens
		oauth_config = self.config.get('tokens', 'google_oauth', default={
			'prefixes': ['1//04', '1//09'],
			'min_length': 80,
			'max_length': 120
		})
		prefixes = oauth_config.get('prefixes', ['1//04'])
		
		# Generate tokens
		ranges = self.config.get('ranges', 'oauth_tokens', default={'min': 1, 'max': 3})
		num_tokens = random.randint(ranges['min'], ranges['max'])
		
		for _ in range(num_tokens):
			prefix = random.choice(prefixes)
			min_len = oauth_config.get('min_length', 80)
			max_len = oauth_config.get('max_length', 120)
			length = random.randint(min_len, max_len)
			
			chars = self.config.get('charsets', 'oauth_token', 
								  default=string.ascii_letters + string.digits + '-_')
			token = prefix + ''.join(random.choices(chars, k=length))
			tokens.append(token)
		
		# Sometimes add API key
		if random.random() > 0.7:
			api_config = self.config.get('tokens', 'api_keys', default={
				'prefix': 'AIza',
				'length': 35
			})
			api_prefix = api_config.get('prefix', 'AIza')
			api_length = api_config.get('length', 35)
			
			chars = self.config.get('charsets', 'api_key', 
								  default=string.ascii_letters + string.digits + '-_')
			api_key = api_prefix + ''.join(random.choices(chars, k=api_length))
			tokens.append(api_key)
		
		return '\n'.join(tokens) + '\n'


class SystemFilesGenerator:
	"""Generates system-related files."""
	
	def __init__(self, config: ConfigurationManager):
		self.config = config
		self.template_renderer = TemplateRenderer(config)
	
	@staticmethod
	def get_persona_seed(persona_id: str, suffix: str = "") -> int:
		"""Generate consistent seed for persona-specific data."""
		seed_string = f"{persona_id}_{suffix}"
		return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
	
	def generate_installed_browsers(self, persona: Persona) -> str:
		"""Generate InstalledBrowsers.txt content."""
		random.seed(self.get_persona_seed(persona.persona_id, 'installed_browsers'))
		
		browsers = []
		header = self.config.get('main', 'meta_header', default='META_DATA\n')
		
		# Always include Windows default browsers
		default_browsers = self.config.get('browsers', 'windows_defaults', default=[
			{
				'name': 'Microsoft Edge',
				'path': 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
				'versions': ['126.0.2592.87']
			}
		])
		for browser_config in default_browsers:
			browsers.append({
				'name': browser_config['name'],
				'path': browser_config['path'],
				'version': random.choice(browser_config['versions'])
			})
		
		# Add primary browser
		if persona.primary_browser and persona.primary_browser != 'Edge' and persona.primary_browser != 'None':
			browser_config = self.config.get('browsers', 'installable', persona.primary_browser)
			if browser_config:
				path = browser_config['path'].replace('{username}', persona.first_name)
				browsers.append({
					'name': browser_config['name'],
					'path': path,
					'version': random.choice(browser_config['versions'])
				})
		
		# Add secondary browser
		if persona.secondary_browser and persona.secondary_browser != 'None':
			# Check if not already added
			browser_names = [b['name'] for b in browsers]
			browser_config = self.config.get('browsers', 'installable', persona.secondary_browser)
			if browser_config and browser_config['name'] not in browser_names:
				path = browser_config['path'].replace('{username}', persona.first_name)
				browsers.append({
					'name': browser_config['name'],
					'path': path,
					'version': random.choice(browser_config['versions'])
				})
		
		# Gaming users might have Opera GX
		if persona.gaming_user == 'Heavy' and random.random() > 0.6:
			opera_config = self.config.get('browsers', 'installable', 'Opera')
			if opera_config:
				path = opera_config['path'].replace('{username}', persona.first_name)
				browsers.append({
					'name': 'Opera GX',
					'path': path,
					'version': random.choice(opera_config['versions'])
				})
		
		# Build content
		entries = []
		for i, browser in enumerate(browsers, 1):
			entry = self.template_renderer.render(
				'installed_browser_entry',
				number=i,
				name=browser['name'],
				path=browser['path'],
				version=browser['version']
			)
			if not entry:  # Fallback if template not found
				entry = f"{i}) {browser['name']} | Path: {browser['path']} | Version: {browser['version']}"
			entries.append(entry)
		
		return header + '\n'.join(entries) + '\n'
	
	def generate_installed_software(self, persona: Persona) -> str:
		"""Generate InstalledSoftware.txt content."""
		random.seed(self.get_persona_seed(persona.persona_id, 'installed_software'))
		
		selected_software = []
		header = self.config.get('main', 'meta_header', default='META_DATA\n')
		
		# Get hardware configuration with improved error handling
		hardware_config = self.config.get('hardware', persona.device_type, persona.income_level)
		
		if not hardware_config:
			logger.warning(f"No hardware config found for {persona.device_type}/{persona.income_level}, using defaults")
			cpu = 'Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz'
		else:
			cpu = random.choice(hardware_config.get('cpu', ['Intel(R) Core(TM) i5-10400 CPU @ 2.90GHz']))
		
		is_amd = 'AMD' in cpu
		
		# Base Windows software
		base_software = self.config.get('software', 'windows_base', default=[
			['Microsoft Visual C++ 2015-2022 Redistributable (x64)', '14.34.31931'],
			['Microsoft Edge', '126.0.2592.87']
		])
		selected_software.extend(base_software)
		
		# Chipset-specific software
		if is_amd:
			amd_software = self.config.get('software', 'amd_chipset', default=[])
			selected_software.extend(amd_software)
		else:
			intel_software = self.config.get('software', 'intel_chipset', default=[])
			selected_software.extend(intel_software)
		
		# Archetype-specific software
		archetype_software = self.config.get('software', 'archetype', persona.persona_archetype, default=[])
		if archetype_software:
			ranges = self.config.get('ranges', 'archetype_software', persona.persona_archetype, 
								   default={'min': 3, 'max': 6})
			num_software = random.randint(ranges['min'], ranges['max'])
			selected_software.extend(random.sample(archetype_software, 
												 min(num_software, len(archetype_software))))
		
		# Crypto software if applicable
		if persona.crypto_user != 'None':
			crypto_software = self.config.get('software', 'crypto', default=[])
			if crypto_software:
				ranges = self.config.get('ranges', 'crypto_software', default={'min': 1, 'max': 4})
				num_crypto = random.randint(ranges['min'], ranges['max'])
				selected_software.extend(random.sample(crypto_software, 
													 min(num_crypto, len(crypto_software))))
		
		# Security software based on tech savviness
		if persona.tech_savviness in ['High', 'Medium']:
			security_software = self.config.get('software', 'security', default=[])
			if security_software:
				ranges = self.config.get('ranges', 'security_software', default={'min': 1, 'max': 3})
				num_security = random.randint(ranges['min'], ranges['max'])
				selected_software.extend(random.sample(security_software, 
													 min(num_security, len(security_software))))
		
		# Heavy downloaders get more software
		if persona.download_habits == 'Frequent':
			all_categories = ['gaming', 'creative', 'development', 'office']
			for category in all_categories:
				category_software = self.config.get('software', category, default=[])
				if category_software:
					extra = random.randint(2, 5)
					selected_software.extend(random.sample(category_software, 
														 min(extra, len(category_software))))
		
		# Remove duplicates while preserving order
		seen = set()
		unique_software = []
		for software in selected_software:
			if isinstance(software, (list, tuple)) and len(software) >= 2:
				if software[0] not in seen:
					seen.add(software[0])
					unique_software.append(software)
		
		# Sort alphabetically
		unique_software.sort(key=lambda x: x[0])
		
		# Format entries
		entries = []
		for i, software_item in enumerate(unique_software, 1):
			if isinstance(software_item, (list, tuple)) and len(software_item) >= 2:
				name, version = software_item[0], software_item[1]
			else:
				name = str(software_item)
				version = "1.0.0"
			entries.append(f"{i}) {name} [{version}]")
		
		return header + '\n'.join(entries) + '\n'
	
	def generate_process_list(self, persona: Persona) -> str:
		"""Generate ProcessList.txt content."""
		random.seed(self.get_persona_seed(persona.persona_id, 'process_list'))
		
		processes = []
		header = self.config.get('main', 'meta_header', default='META_DATA\n')
		
		# System processes
		system_processes = self.config.get('processes', 'system', default=[
			['System', ''],
			['services.exe', ''],
			['explorer.exe', 'C:\\WINDOWS\\Explorer.EXE']
		])
		for proc_name, cmd_template in system_processes:
			pid = random.randint(100, 99999)
			
			# Many system processes show empty command lines
			if random.random() > 0.4 and proc_name not in ['csrss.exe', 'SearchHost.exe', 'MpCmdRun.exe']:
				cmd_line = ''
			else:
				cmd_line = cmd_template.replace('{username}', persona.first_name)
			
			processes.append({'id': pid, 'name': proc_name, 'cmdline': cmd_line})
		
		# Multiple svchost instances
		svchost_services = self.config.get('processes', 'svchost_services', default=[
			'-k LocalService -p',
			'-k NetworkService -p'
		])
		
		ranges = self.config.get('ranges', 'svchost_count', default={'min': 20, 'max': 40})
		num_svchost = random.randint(ranges['min'], ranges['max'])
		
		for _ in range(num_svchost):
			pid = random.randint(100, 99999)
			service = random.choice(svchost_services)
			
			if random.random() > 0.7:
				cmdline = f'C:\\WINDOWS\\system32\\svchost.exe {service}'
			else:
				cmdline = ''
			
			processes.append({'id': pid, 'name': 'svchost.exe', 'cmdline': cmdline})
		
		# Browser processes
		self._add_browser_processes(processes, persona)
		
		# NVIDIA processes for gaming rigs
		if persona.device_type == 'Gaming_Rig' or (persona.income_level == 'High' and random.random() > 0.5):
			nvidia_processes = self.config.get('processes', 'nvidia', default=[])
			for proc_name, cmd_line in nvidia_processes:
				processes.append({
					'id': random.randint(100, 99999),
					'name': proc_name,
					'cmdline': cmd_line
				})
		
		# Archetype-specific processes
		archetype_processes = self.config.get('processes', 'archetype', persona.persona_archetype, default=[])
		for proc_name, cmd_template in archetype_processes:
			if random.random() > 0.5 and proc_name not in ['steamwebhelper.exe', 'Teams.exe', 'OUTLOOK.EXE']:
				cmd_line = ''
			else:
				cmd_line = cmd_template.replace('{username}', persona.first_name)
			
			processes.append({
				'id': random.randint(100, 99999),
				'name': proc_name,
				'cmdline': cmd_line
			})
		
		# Add the stealer process
		processes.append({
			'id': random.randint(10000, 20000),
			'name': 'rundll32.exe',
			'cmdline': ''
		})
		
		# Sort by PID
		processes.sort(key=lambda x: x['id'])
		
		# Format entries
		entries = []
		for proc in processes:
			entry = self.template_renderer.render(
				'process_entry',
				id=proc['id'],
				name=proc['name'],
				cmdline=proc['cmdline']
			)
			if not entry:  # Fallback if template not found
				entry = f'''ID: [{proc['id']}]
Name: [{proc['name']}]
CommandLine: [{proc['cmdline']}]
'''
			entries.append(entry)
		
		return header + '\n'.join(entries) + '\n'
	
	def _add_browser_processes(self, processes: List[Dict], persona: Persona):
		"""Add browser processes based on persona."""
		browser_processes = self.config.get('processes', 'browsers', default={})
		
		if 'Chrome' in persona.primary_browser or 'Chrome' in persona.secondary_browser:
			if 'Chrome' in browser_processes:
				ranges = browser_processes['Chrome'].get('count', {'min': 5, 'max': 15})
				num_chrome = random.randint(ranges['min'], ranges['max'])
				
				for i in range(num_chrome):
					pid = random.randint(100, 99999)
					
					if i == 0 and random.random() > 0.7:
						cmdline = browser_processes['Chrome'].get('gpu_cmdline', '')
					else:
						cmdline = ''
					
					processes.append({'id': pid, 'name': 'chrome.exe', 'cmdline': cmdline})
		
		if 'Edge' in persona.primary_browser or 'Edge' in persona.secondary_browser:
			if 'Edge' in browser_processes:
				ranges = browser_processes['Edge'].get('count', {'min': 3, 'max': 8})
				num_edge = random.randint(ranges['min'], ranges['max'])
				
				for _ in range(num_edge):
					pid = random.randint(100, 99999)
					cmdline = '' if random.random() > 0.8 else browser_processes['Edge'].get('renderer_cmdline', '')
					processes.append({'id': pid, 'name': 'msedge.exe', 'cmdline': cmdline})
		
		if 'Firefox' in persona.primary_browser or 'Firefox' in persona.secondary_browser:
			processes.append({
				'id': random.randint(100, 99999),
				'name': 'firefox.exe',
				'cmdline': ''  # Usually empty
			})


class DomainDetector:
	"""Detects and categorizes domains."""
	
	def __init__(self, config: ConfigurationManager):
		self.config = config
	
	def generate_domain_detects(self, password_domains: List[str], cookie_domains: List[str]) -> str:
		"""Generate DomainDetects.txt content."""
		pdd_counts = {}
		cdd_counts = {}
		
		domain_categories = self.config.get('domains', 'categories', default={})
		
		# Count password domains
		for domain in password_domains:
			if domain in domain_categories:
				category = domain_categories[domain]
				key = f"{category} {domain}"
				pdd_counts[key] = pdd_counts.get(key, 0) + 1
		
		# Count cookie domains
		for domain in cookie_domains:
			# Clean domain (remove leading dot)
			clean_domain = domain.lstrip('.')
			if clean_domain in domain_categories:
				category = domain_categories[clean_domain]
				key = f"{category} {clean_domain}"
				cdd_counts[key] = cdd_counts.get(key, 0) + 1
		
		# Format output
		content = "PDD: \n"
		if pdd_counts:
			pdd_items = []
			for domain_key, count in sorted(pdd_counts.items()):
				pdd_items.append(f"{domain_key} ({count})")
			content += ", ".join(pdd_items)
		content += "\nCDD: \n"
		
		if cdd_counts:
			cdd_items = []
			for domain_key, count in sorted(cdd_counts.items()):
				cdd_items.append(f"{domain_key} ({count})")
			content += ", ".join(cdd_items)
		content += "\n"
		
		return content


class AdvancedContentGenerator:
	"""Generates advanced content like FileGrabber, Telegram, and Wallets."""
	
	def __init__(self, config: ConfigurationManager):
		self.config = config
	
	@staticmethod
	def get_persona_seed(persona_id: str, suffix: str = "") -> int:
		"""Generate consistent seed for persona-specific data."""
		seed_string = f"{persona_id}_{suffix}"
		return int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
	
	def should_include_filegrabber(self, persona: Persona) -> bool:
		"""Determine if FileGrabber should be included."""
		probabilities = self.config.get('filegrabber', 'inclusion_probability', default={
			'high_value': 0.3,
			'crypto_user': 0.4,
			'business_access': 0.5,
			'default': 0.8
		})
		
		if persona.financial_value == 'High':
			return random.random() > probabilities.get('high_value', 0.3)
		elif persona.crypto_user != 'None':
			return random.random() > probabilities.get('crypto_user', 0.4)
		elif persona.business_access == 'Yes':
			return random.random() > probabilities.get('business_access', 0.5)
		else:
			return random.random() > probabilities.get('default', 0.8)
	
	def generate_filegrabber(self, persona: Persona, log_dir: str):
		"""Generate FileGrabber directory and contents if applicable."""
		random.seed(self.get_persona_seed(persona.persona_id, 'filegrabber'))
		
		if not self.should_include_filegrabber(persona):
			return
		
		# Create FileGrabber directory
		fg_dir = os.path.join(log_dir, 'Filegrabber')
		os.makedirs(fg_dir, exist_ok=True)
		
		# Decide which subdirectories to include
		include_toolong = random.random() > 0.3
		include_userdir = random.random() > 0.4
		
		if include_toolong:
			self._create_toolong_dir(persona, fg_dir)
		
		if include_userdir:
			self._create_user_dir(persona, fg_dir)
	
	def _create_toolong_dir(self, persona: Persona, fg_dir: str):
		"""Create TooLongDir with grabbed files."""
		toolong_dir = os.path.join(fg_dir, 'TooLongDir')
		os.makedirs(toolong_dir, exist_ok=True)
		
		files_to_create = []
		
		# Get files based on persona type
		if persona.crypto_user != 'None':
			crypto_files = self.config.get('filegrabber', 'crypto_files', default=['wallet.dat'])
			if crypto_files:
				num_files = random.randint(1, min(3, len(crypto_files)))
				files_to_create.extend(random.sample(crypto_files, num_files))
		
		if persona.business_access == 'Yes':
			business_files = self.config.get('filegrabber', 'business_files', default=['passwords.xlsx'])
			if business_files:
				num_files = random.randint(1, min(4, len(business_files)))
				files_to_create.extend(random.sample(business_files, num_files))
		
		# Generic valuable files
		generic_files = self.config.get('filegrabber', 'generic_files', default=['passwords.txt'])
		if generic_files:
			num_files = random.randint(1, min(3, len(generic_files)))
			files_to_create.extend(random.sample(generic_files, num_files))
		
		# Create placeholder files
		file_headers = self.config.get('filegrabber', 'file_headers', default={})
		
		for filename in files_to_create:
			filepath = os.path.join(toolong_dir, filename)
			with open(filepath, 'wb') as f:
				ext = os.path.splitext(filename)[1]
				if ext in file_headers:
					header = file_headers[ext]
					if header == "PNG_HEADER":
						f.write(b'\x89PNG\r\n\x1a\n')
					else:
						f.write(header.encode('utf-8') if isinstance(header, str) else header)
				else:
					f.write(b'[File content grabbed by RedLine]\n')
	
	def _create_user_dir(self, persona: Persona, fg_dir: str):
		"""Create user directory with documents."""
		user_dir = os.path.join(fg_dir, 'Users', persona.first_name)
		os.makedirs(user_dir, exist_ok=True)
		
		# Get archetype-specific files
		desktop_files = []
		docs_files = []
		
		archetype_files = self.config.get('filegrabber', 'archetype_files', persona.persona_archetype, default={})
		if archetype_files:
			desktop_files.extend(archetype_files.get('desktop', []))
			docs_files.extend(archetype_files.get('documents', []))
		
		# Add general files
		general_files = self.config.get('filegrabber', 'general_user_files', default={
			'desktop': ['notes.txt'],
			'documents': ['resume.docx']
		})
		desktop_files.extend(general_files.get('desktop', []))
		docs_files.extend(general_files.get('documents', []))
		
		# Create Desktop subfolder
		if desktop_files:
			desktop_dir = os.path.join(user_dir, 'Desktop')
			os.makedirs(desktop_dir, exist_ok=True)
			
			if len(desktop_files) >= 2:
				num_files = random.randint(2, min(5, len(desktop_files)))
			else:
				num_files = len(desktop_files)
			selected_desktop = random.sample(desktop_files, num_files)
			
			for filename in selected_desktop:
				filepath = os.path.join(desktop_dir, filename)
				with open(filepath, 'wb') as f:
					if filename.endswith('.txt'):
						f.write(b'[Desktop file content]\n')
					elif filename.endswith('.png'):
						f.write(b'\x89PNG\r\n\x1a\n')
					else:
						f.write(b'[File grabbed from Desktop]')
		
		# Create Documents subfolder
		if docs_files:
			docs_dir = os.path.join(user_dir, 'Documents')
			os.makedirs(docs_dir, exist_ok=True)
			
			num_files = random.randint(2, min(6, len(docs_files)))
			selected_docs = random.sample(docs_files, num_files)
			
			for filename in selected_docs:
				filepath = os.path.join(docs_dir, filename)
				with open(filepath, 'wb') as f:
					f.write(b'[Document file content]')
	
	def should_include_telegram(self, persona: Persona) -> bool:
		"""Determine if Telegram should be included."""
		probabilities = self.config.get('telegram', 'inclusion_probability', default={
			'heavy_social': 0.4,
			'student': 0.6,
			'crypto_user': 0.5,
			'default': 0.8
		})
		
		if persona.social_media_user == 'Heavy':
			return random.random() > probabilities.get('heavy_social', 0.4)
		elif 'Student' in persona.persona_archetype:
			return random.random() > probabilities.get('student', 0.6)
		elif persona.crypto_user != 'None':
			return random.random() > probabilities.get('crypto_user', 0.5)
		else:
			return random.random() > probabilities.get('default', 0.8)
	
	def generate_telegram_files(self, persona: Persona, log_dir: str):
		"""Generate Telegram directory if applicable."""
		random.seed(self.get_persona_seed(persona.persona_id, 'telegram'))
		
		if not self.should_include_telegram(persona):
			return
		
		# Create Telegram directory structure
		telegram_dir = os.path.join(log_dir, 'Telegram')
		profile_dir = os.path.join(telegram_dir, 'Profile_1')
		os.makedirs(profile_dir, exist_ok=True)
		
		# Get Telegram files from config
		telegram_files = self.config.get('telegram', 'profile_files', default=[
			'settingss', 'key_datas', 'countries'
		])
		
		# Create main profile files
		for filename in telegram_files:
			filepath = os.path.join(profile_dir, filename)
			with open(filepath, 'wb') as f:
				if filename.endswith('.json'):
					f.write(b'{"grabbed": true}')
				else:
					# Telegram uses encrypted binary format
					size_range = self.config.get('telegram', 'file_sizes', filename, 
											   default={'min': 100, 'max': 500})
					size = random.randint(size_range['min'], size_range['max'])
					f.write(b'\x00' * size)
		
		# Create subdirectory with more encrypted files
		sub_dir_name = self.config.get('telegram', 'sub_directory', default='D877F783D5D3EF8C')
		sub_dir = os.path.join(profile_dir, sub_dir_name)
		os.makedirs(sub_dir, exist_ok=True)
		
		sub_files = self.config.get('telegram', 'sub_files', default=['configs', 'maps'])
		for filename in sub_files:
			filepath = os.path.join(sub_dir, filename)
			with open(filepath, 'wb') as f:
				size_range = self.config.get('telegram', 'sub_file_sizes', filename, 
										   default={'min': 50, 'max': 200})
				size = random.randint(size_range['min'], size_range['max'])
				f.write(b'\x00' * size)
	
	def generate_wallet_files(self, persona: Persona, browser_profiles: List[Tuple[str, str]], log_dir: str):
		"""Generate Wallets directory for crypto users."""
		if persona.crypto_user == 'None':
			return
		
		random.seed(self.get_persona_seed(persona.persona_id, 'wallets'))
		
		# Create Wallets directory
		wallets_dir = os.path.join(log_dir, 'Wallets')
		os.makedirs(wallets_dir, exist_ok=True)
		
		wallets_to_create = []
		
		# MetaMask is most common
		metamask_probability = self.config.get('wallets', 'metamask_probability', default=0.7)
		if random.random() < metamask_probability:
			# Find a Chrome profile to associate with MetaMask
			chrome_profiles = [bp for bp in browser_profiles if 'Chrome' in bp[0]]
			if chrome_profiles:
				browser, profile = random.choice(chrome_profiles)
				wallets_to_create.append(('Metamask', browser, profile))
		
		# Other wallets for heavy crypto users
		if persona.crypto_user == 'Heavy':
			other_wallets = self.config.get('wallets', 'other_wallets', default=['Exodus'])
			if other_wallets:
				ranges = self.config.get('ranges', 'additional_wallets', default={'min': 1, 'max': 2})
				num_additional = random.randint(ranges['min'], ranges['max'])
				
				for wallet_name in random.sample(other_wallets, min(num_additional, len(other_wallets))):
					wallets_to_create.append((wallet_name, None, None))
		
		# Create wallet directories
		for wallet_info in wallets_to_create:
			wallet_name = wallet_info[0]
			
			if wallet_name == 'Metamask' and wallet_info[1]:
				# MetaMask uses browser-specific directory naming
				wallet_dir_name = f"{wallet_info[1]}_{wallet_info[2].replace(' ', '_')}_{wallet_name}"
			else:
				wallet_dir_name = wallet_name
			
			wallet_path = os.path.join(wallets_dir, wallet_dir_name)
			os.makedirs(wallet_path, exist_ok=True)
			
			# Get wallet files from config
			wallet_files = self.config.get('wallets', 'wallet_files', wallet_name, default=[])
			
			if not wallet_files and wallet_name == 'Metamask':
				# Default MetaMask files
				wallet_files = [
					{'name': '000005.ldb', 'size': 0},
					{'name': 'CURRENT', 'content': 'MANIFEST-000007\n'},
					{'name': 'LOG', 'content': ''}
				]
			
			for file_config in wallet_files:
				filename = file_config['name']
				filepath = os.path.join(wallet_path, filename)
				
				with open(filepath, 'wb') as f:
					if 'content' in file_config:
						content = file_config['content']
						if isinstance(content, str):
							if content == "":
								f.write(b'')
							else:
								f.write(content.encode('utf-8'))
						else:
							f.write(bytes(content))
					elif 'size' in file_config:
						f.write(b'\x00' * file_config['size'])
					else:
						f.write(b'')


class RedLineLogGenerator:
	"""Main generator class for RedLine stealer logs."""
	
	def __init__(self, csv_file_path: str, config_dir: str = 'config'):
		self.config = ConfigurationManager(config_dir)
		self.personas = self.load_redline_personas(csv_file_path)
		self.output_base_dir = self.config.get('main', 'output_directory', default='redline_logs')
		self._initialize_generators()
		self._check_csv_values()
	
	def _check_csv_values(self):
		"""Check and log unique values from the CSV to help with debugging."""
		device_types = set()
		income_levels = set()
		
		for persona in self.personas:
			device_types.add(persona.device_type)
			income_levels.add(persona.income_level)
		
		logger.info("=" * 50)
		logger.info("CSV VALUE CHECK")
		logger.info("=" * 50)
		logger.info(f"Unique DeviceType values: {sorted(device_types)}")
		logger.info(f"Unique IncomeLevel values: {sorted(income_levels)}")
		
		# Check if values need normalization
		for dt in device_types:
			normalized = self.config.normalize_value(dt, 'device_type')
			if normalized != dt:
				logger.info(f"	DeviceType '{dt}' will be normalized to '{normalized}'")
		
		for il in income_levels:
			normalized = self.config.normalize_value(il, 'income_level')
			if normalized != il:
				logger.info(f"	IncomeLevel '{il}' will be normalized to '{normalized}'")
		
		logger.info("=" * 50)
	
	def load_redline_personas(self, csv_file_path: str) -> List[Persona]:
		"""Load personas from CSV where Infection column indicates RedLine."""
		redline_personas = []
		
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
				
				# Read personas infected by RedLine
				for row in reader:
					infection_value = row.get(infection_column, '').strip().lower()
					if infection_value == 'redline':
						# Verify it's a Windows user (RedLine only infects Windows)
						if 'Windows' not in row.get('OS', ''):
							logger.warning(f"Persona {row['PersonaID']} marked for RedLine but has OS: {row.get('OS')}. Skipping.")
							continue
						redline_personas.append(Persona.from_csv_row(row))
			
			logger.info(f"Found {len(redline_personas)} personas infected by RedLine")
			
			if not redline_personas:
				logger.warning("No personas found with RedLine infection. Check the 'Infection' column in your CSV.")
			
			# Log selected personas
			self._log_selected_personas(redline_personas)
			
			return redline_personas
			
		except FileNotFoundError:
			logger.error(f"CSV file not found: {csv_file_path}")
			raise
		except Exception as e:
			logger.error(f"Error loading personas: {e}")
			raise
	
	def _log_selected_personas(self, personas: List[Persona]):
		"""Log personas infected by RedLine."""
		print("\n" + "="*50)
		print(f"FOUND {len(personas)} PERSONAS INFECTED BY REDLINE:")
		print("="*50)
		print("PersonaID | First Name | Last Name | OS | Archetype")
		print("-"*50)
		for p in personas[:10]:	 # Show first 10
			print(f"{p.persona_id} | {p.first_name} | {p.last_name} | {p.os} | {p.persona_archetype}")
		if len(personas) > 10:
			print(f"... and {len(personas) - 10} more personas")
		print("="*50)
		
		# Save to file for reference
		with open('redline_infected_personas.txt', 'w') as f:
			f.write("PersonaIDs infected by RedLine (from Infection column):\n")
			f.write(",".join([p.persona_id for p in personas]))
			f.write("\n\nDetails:\n")
			for p in personas:
				f.write(f"{p.persona_id}: {p.first_name} {p.last_name} - {p.os} ({p.persona_archetype})\n")
			f.write(f"\n\nTotal: {len(personas)} personas\n")
	
	def _initialize_generators(self):
		"""Initialize all content generators."""
		self.system_generator = SystemInfoGenerator(self.config)
		self.autofill_generator = AutofillGenerator(self.config)
		self.browser_generator = BrowserDataGenerator(self.config)
		self.system_files_generator = SystemFilesGenerator(self.config)
		self.domain_detector = DomainDetector(self.config)
		self.advanced_generator = AdvancedContentGenerator(self.config)
		self.hardware_generator = HardwareGenerator(self.config)
	
	def generate_redline_log(self, persona: Persona) -> str:
		"""Generate complete RedLine log for a persona."""
		logger.info(f"Generating log for {persona.persona_id} - {persona.first_name} {persona.last_name}")
		
		# Create output directory
		log_id = self.hardware_generator.generate_log_id()
		log_dir = os.path.join(self.output_base_dir, f"RedLine_{persona.persona_id}_{log_id}")
		os.makedirs(log_dir, exist_ok=True)
		
		try:
			# Generate UserInformation.txt
			self._write_file(log_dir, 'UserInformation.txt', 
						   self.system_generator.generate(persona))
			
			# Get browser profiles
			browser_profiles = self.browser_generator.get_browser_profiles(persona)
			
			# Track domains for DomainDetects
			password_domains = []
			cookie_domains = []
			
			# Create Autofills directory
			autofills_dir = os.path.join(log_dir, 'Autofills')
			os.makedirs(autofills_dir, exist_ok=True)
			
			for browser, profile in browser_profiles:
				filename = f"{browser}_{profile.replace(' ', '_')}.txt"
				self._write_file(autofills_dir, filename,
							   self.autofill_generator.generate(persona, f"{browser}_{profile}"))
			
			# Create Cookies directory
			cookies_dir = os.path.join(log_dir, 'Cookies')
			os.makedirs(cookies_dir, exist_ok=True)
			
			for browser, profile in browser_profiles:
				# Network cookies
				filename = f"{browser}_{profile.replace(' ', '_')}_Network.txt"
				content, domains = self.browser_generator.generate_cookies(
					persona, f"{browser}_{profile}", 'Network')
				self._write_file(cookies_dir, filename, content)
				cookie_domains.extend(domains)
				
				# Extension cookies (sometimes)
				if random.random() > 0.7 and 'Chrome' in browser:
					ext_filename = f"{browser}_{profile.replace(' ', '_')}_Extension.txt"
					ext_content, ext_domains = self.browser_generator.generate_cookies(
						persona, f"{browser}_{profile}", 'Extension')
					self._write_file(cookies_dir, ext_filename, ext_content)
					cookie_domains.extend(ext_domains)
			
			# Create Restore directory
			restore_dir = os.path.join(log_dir, 'Restore')
			os.makedirs(restore_dir, exist_ok=True)
			
			for browser, profile in browser_profiles:
				# Fresh Cookies
				cookies_filename = f"{browser}_{profile.replace(' ', '_')} Fresh Cookies.txt"
				self._write_file(restore_dir, cookies_filename,
							   self.browser_generator.generate_restore_cookies(persona, f"{browser}_{profile}"))
				
				# Token file (for Chrome/Google)
				if ('Chrome' in browser or 'Google' in browser) and random.random() > 0.3:
					token_filename = f"{browser}_{profile.replace(' ', '_')} Token.txt"
					self._write_file(restore_dir, token_filename,
								   self.browser_generator.generate_restore_tokens(persona, f"{browser}_{profile}"))
			
			# Create UserAgents directory
			ua_dir = os.path.join(log_dir, 'UserAgents')
			os.makedirs(ua_dir, exist_ok=True)
			
			browsers_seen = set()
			for browser, profile in browser_profiles:
				browser_base = browser.split(']')[0] + ']' if ']' in browser else browser
				
				if browser_base not in browsers_seen:
					browsers_seen.add(browser_base)
					ua_filename = f"{browser_base}.txt"
					self._write_file(ua_dir, ua_filename,
								   self.browser_generator.generate_user_agents(persona, browser_base))
			
			# Generate Passwords.txt
			passwords_content, password_domains = self.browser_generator.generate_passwords(
				persona, browser_profiles)
			self._write_file(log_dir, 'Passwords.txt', passwords_content)
			
			# Generate ImportantAutofills.txt
			self._write_file(log_dir, 'ImportantAutofills.txt',
						   self.autofill_generator.generate_important(persona))
			
			# Generate InstalledBrowsers.txt
			self._write_file(log_dir, 'InstalledBrowsers.txt',
						   self.system_files_generator.generate_installed_browsers(persona))
			
			# Generate InstalledSoftware.txt
			self._write_file(log_dir, 'InstalledSoftware.txt',
						   self.system_files_generator.generate_installed_software(persona))
			
			# Generate ProcessList.txt
			self._write_file(log_dir, 'ProcessList.txt',
						   self.system_files_generator.generate_process_list(persona))
			
			# Generate FileGrabber directory (conditional)
			self.advanced_generator.generate_filegrabber(persona, log_dir)
			
			# Generate Telegram directory (conditional)
			self.advanced_generator.generate_telegram_files(persona, log_dir)
			
			# Generate Wallets directory (for crypto users)
			self.advanced_generator.generate_wallet_files(persona, browser_profiles, log_dir)
			
			# Generate DomainDetects.txt
			self._write_file(log_dir, 'DomainDetects.txt',
						   self.domain_detector.generate_domain_detects(password_domains, cookie_domains))
			
			# Create Screenshot.jpg placeholder
			with open(os.path.join(log_dir, 'Screenshot.jpg'), 'wb') as f:
				# Write JPEG magic bytes
				f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
				f.write(b'[Screenshot placeholder]')
			
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
	
	def generate_all_redline_logs(self) -> List[str]:
		"""Generate RedLine logs for all assigned personas."""
		generated_logs = []
		
		logger.info("Starting RedLine stealer log generation...")
		logger.info(f"Processing {len(self.personas)} personas infected by RedLine")
		logger.info("-" * 50)
		
		for i, persona in enumerate(self.personas, 1):
			try:
				logger.info(f"[{i}/{len(self.personas)}] Processing {persona.persona_id}")
				log_dir = self.generate_redline_log(persona)
				generated_logs.append(log_dir)
			except Exception as e:
				logger.error(f"Failed to generate log for {persona.persona_id}: {e}")
				traceback.print_exc()
		
		logger.info("-" * 50)
		logger.info(f"Successfully generated {len(generated_logs)} RedLine stealer logs")
		
		if len(generated_logs) < len(self.personas):
			logger.warning(f"Failed to generate {len(self.personas) - len(generated_logs)} logs")
		
		return generated_logs


def main():
	"""Main entry point."""
	import argparse
	
	parser = argparse.ArgumentParser(description='Generate synthetic RedLine Stealer logs')
	parser.add_argument('csv_file', help='Path to personas CSV file with Infection column')
	parser.add_argument('--config-dir', default='config', help='Configuration directory (default: config)')
	parser.add_argument('--single', help='Generate log for single persona ID')
	parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
	
	args = parser.parse_args()
	
	if args.verbose:
		logging.getLogger().setLevel(logging.DEBUG)
	
	try:
		generator = RedLineLogGenerator(args.csv_file, args.config_dir)
		
		if args.single:
			# Find and generate for single persona
			persona = next((p for p in generator.personas if p.persona_id == args.single), None)
			if persona:
				generator.generate_redline_log(persona)
			else:
				logger.error(f"Persona ID '{args.single}' not found or not infected by RedLine")
		else:
			# Generate all logs
			generator.generate_all_redline_logs()
			
	except Exception as e:
		logger.error(f"Fatal error: {e}")
		exit(1)


if __name__ == "__main__":
	main()
