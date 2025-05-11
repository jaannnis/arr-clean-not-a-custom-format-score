#!/usr/bin/env python3
import requests
import json
import time
import logging
import os
from datetime import datetime

# Get configuration from environment variables
def get_env_bool(name, default):
    value = os.environ.get(name, str(default)).lower()
    return value in ('true', '1', 'yes', 'y')

# Configuration from environment variables
CONFIG = {
    'sonarr': {
        'url': os.environ.get('SONARR_URL', '').rstrip('/'),
        'api_key': os.environ.get('SONARR_API_KEY', ''),
        'enabled': get_env_bool('SONARR_ENABLED', True)
    },
    'radarr': {
        'url': os.environ.get('RADARR_URL', '').rstrip('/'),
        'api_key': os.environ.get('RADARR_API_KEY', ''),
        'enabled': get_env_bool('RADARR_ENABLED', True)
    },
    'check_interval': int(os.environ.get('CHECK_INTERVAL_SECONDS', 3600)),
    'log_file': os.environ.get('LOG_FILE', '/logs/cleanup_script.log'),
    'debug': get_env_bool('DEBUG', False)
}

# Set up logging
log_level = logging.DEBUG if CONFIG['debug'] else logging.INFO

# Make sure the logs directory exists
os.makedirs(os.path.dirname(CONFIG['log_file']), exist_ok=True)

# Configure logging to both file and console
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(CONFIG['log_file']),
        logging.StreamHandler()
    ]
)

def get_all_queue_items(base_url, headers, service_name):
    """Get all queue items handling pagination"""
    all_items = []
    page = 1
    page_size = 100  # Request max items per page to reduce number of API calls
    
    while True:
        queue_url = f"{base_url}/api/v3/queue?page={page}&pageSize={page_size}&includeUnknownMovieItems=true"
        try:
            response = requests.get(queue_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            records = data.get('records', [])
            all_items.extend(records)
            
            # If we got fewer records than page size, we've reached the end
            if len(records) < page_size or page * page_size >= data.get('totalRecords', 0):
                break
                
            page += 1
        except Exception as e:
            logging.error(f"Error fetching {service_name} queue page {page}: {str(e)}")
            break
    
    logging.info(f"[{service_name}] Retrieved {len(all_items)} queue items total")
    return all_items

def has_custom_format_rejection(item):
    """Check if the item has been rejected due to custom format issues"""
    # Check if the item is pending import or blocked
    if item.get('trackedDownloadState') not in ['importPending', 'importBlocked']:
        return False
    
    # Look for custom format rejection message in any of the status messages
    for status_message in item.get('statusMessages', []):
        for message in status_message.get('messages', []):
            if "Not a Custom Format upgrade" in message:
                return True
    
    return False

def check_and_clean_queue(service_name):
    """Check queue for the given service and delete rejected custom format items"""
    service_config = CONFIG[service_name]
    if not service_config['enabled']:
        logging.info(f"[{service_name}] Service disabled, skipping")
        return
    
    # Check if URL and API key are configured
    if not service_config['url'] or not service_config['api_key']:
        logging.warning(f"[{service_name}] URL or API key not configured, skipping")
        return
    
    base_url = service_config['url']
    headers = {'X-Api-Key': service_config['api_key']}
    
    # Get all queue items, handling pagination
    queue_items = get_all_queue_items(base_url, headers, service_name)
    
    # Process queue items
    items_to_delete = []
    
    for item in queue_items:
        if has_custom_format_rejection(item):
            items_to_delete.append({
                'id': item['id'],
                'title': item['title'],
                'state': item.get('trackedDownloadState', 'unknown')
            })
    
    # Delete the identified items
    for item in items_to_delete:
        delete_url = f"{base_url}/api/v3/queue/{item['id']}?removeFromClient=true&blocklist=false"
        try:
            response = requests.delete(delete_url, headers=headers)
            response.raise_for_status()
            logging.info(f"[{service_name}] Deleted: {item['title']} (State: {item['state']})")
        except Exception as e:
            logging.error(f"[{service_name}] Error deleting {item['title']}: {str(e)}")
    
    logging.info(f"[{service_name}] Processed {len(queue_items)} items, deleted {len(items_to_delete)} rejected items")

def main():
    """Main function to run cleanup checks periodically"""
    logging.info("Starting automatic custom format rejection cleanup")
    logging.info(f"Configuration: Check interval: {CONFIG['check_interval']} seconds")
    logging.info(f"Sonarr enabled: {CONFIG['sonarr']['enabled']}")
    logging.info(f"Radarr enabled: {CONFIG['radarr']['enabled']}")
    
    while True:
        try:
            # Run cleanup for each service
            for service in ['sonarr', 'radarr']:
                check_and_clean_queue(service)
            
            logging.info(f"Cleanup completed. Next run in {CONFIG['check_interval']} seconds")
            time.sleep(CONFIG['check_interval'])
        except KeyboardInterrupt:
            logging.info("Script terminated by user")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            time.sleep(300)  # Wait 5 minutes before retry on unexpected error

if __name__ == "__main__":
    main()
