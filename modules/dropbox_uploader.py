"""
Dropbox uploader module
Summary: Uploads campaign assets to Dropbox cloud storage
"""

import logging
from pathlib import Path
from typing import Optional, List
import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode

from config import settings

logger = logging.getLogger(__name__)


class DropboxUploader:
    """Uploads campaign assets to Dropbox"""

    def __init__(self):
        """
        Initialize Dropbox uploader
        """
        self.enabled = settings.dropbox_upload_enabled
        self.base_path = settings.dropbox_base_path.rstrip('/')

        if self.enabled:
            if not settings.dropbox_access_token:
                logger.error("Dropbox upload enabled but DROPBOX_ACCESS_TOKEN not configured")
                self.enabled = False
                self.dbx = None
            else:
                try:
                    self.dbx = dropbox.Dropbox(settings.dropbox_access_token)
                    self.dbx.users_get_current_account()
                except AuthError:
                    logger.error("Invalid Dropbox access token")
                    self.enabled = False
                    self.dbx = None
                except Exception as e:
                    logger.error(f"Dropbox initialization error: {e}")
                    self.enabled = False
                    self.dbx = None
        else:
            self.dbx = None

    def upload_file(self, local_path: Path, dropbox_path: str) -> Optional[str]:
        """
        Upload single file to Dropbox
        Summary: Uploads file and returns shared link
        """
        if not self.enabled:
            return None

        try:
            with open(local_path, 'rb') as f:
                file_data = f.read()

            full_path = f"{self.base_path}/{dropbox_path}".replace('//', '/')

            self.dbx.files_upload(
                file_data,
                full_path,
                mode=WriteMode('overwrite'),
                autorename=False
            )

            try:
                shared_link = self.dbx.sharing_create_shared_link_with_settings(full_path)
                return shared_link.url
            except ApiError as e:
                if 'shared_link_already_exists' in str(e):
                    links = self.dbx.sharing_list_shared_links(path=full_path)
                    if links.links:
                        return links.links[0].url
                logger.warning(f"Could not create shared link for {full_path}")
                return None

        except FileNotFoundError as e:
            logger.error(f"Dropbox upload failed - File not found: {local_path}")
            return None
        except PermissionError as e:
            logger.error(f"Dropbox upload failed - Permission denied: {local_path}")
            return None
        except Exception as e:
            logger.error(f"Dropbox upload failed for {local_path}: {type(e).__name__}: {e}")
            return None

    def upload_campaign_assets(
        self,
        campaign_id: str,
        product_name: str,
        asset_paths: List[Path],
        delete_existing: bool = True
    ) -> dict:
        """
        Upload all campaign assets for a product
        Summary: Uploads product assets and campaign variations, optionally deletes existing campaign folder first
        """
        if not self.enabled:
            logger.warning(f"`self.enabled` is False in upload_campaign_assets. Update to True to enable Dropbox uploads.")
            return {}

        uploaded = {}
        failed = []
        safe_product_name = "".join(c if c.isalnum() or c in "_ " else "_" for c in product_name).replace(" ", "_")
        campaign_folder = f"{campaign_id}/{safe_product_name}"

        # Delete existing campaign folder if requested (fresh upload)
        if delete_existing:
            self.delete_folder(campaign_folder)

        # Create campaign folder
        folder_created = self.create_folder(campaign_folder)
        if folder_created:
            logger.info(f"Dropbox folder ready: {self.base_path}/{campaign_folder}")

        for asset_path in asset_paths:
            if not asset_path.exists():
                logger.warning(f"Dropbox upload skipped - Asset not found: {asset_path}")
                failed.append(str(asset_path))
                continue

            dropbox_path = f"{campaign_id}/{safe_product_name}/{asset_path.name}"
            url = self.upload_file(asset_path, dropbox_path)

            if url:
                uploaded[str(asset_path)] = url
            else:
                logger.error(f"Dropbox upload failed for asset: {asset_path.name}")
                failed.append(str(asset_path))

        # Log completion summary
        if failed:
            logger.warning(f"Dropbox upload incomplete - {len(failed)} of {len(asset_paths)} assets failed")
        else:
            logger.info(f"Dropbox upload complete - {len(uploaded)} assets uploaded to {self.base_path}/{campaign_folder}")

        return uploaded

    def upload_report(self, campaign_id: str, report_path: Path) -> Optional[str]:
        """
        Upload campaign report to Dropbox
        Summary: Uploads JSON report and returns shared link
        """
        if not self.enabled:
            return None

        if not report_path.exists():
            logger.error(f"Dropbox upload failed - Report not found: {report_path}")
            return None

        # Create reports folder
        reports_folder = f"{campaign_id}/reports"
        self.create_folder(reports_folder)

        dropbox_path = f"{campaign_id}/reports/{report_path.name}"
        url = self.upload_file(report_path, dropbox_path)

        if url:
            logger.info(f"Dropbox report uploaded: {self.base_path}/{dropbox_path}")
        else:
            logger.error(f"Dropbox upload failed for report: {report_path.name}")

        return url

    def upload_directory(self, local_dir: Path, dropbox_dir: str) -> int:
        """
        Upload entire directory to Dropbox
        Summary: Recursively uploads all files in directory, returns count of uploaded files
        """
        if not self.enabled:
            return 0

        if not local_dir.exists() or not local_dir.is_dir():
            logger.warning(f"Directory not found: {local_dir}")
            return 0

        uploaded_count = 0

        for file_path in local_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(local_dir)
                dropbox_path = f"{dropbox_dir}/{relative_path}".replace('\\', '/')

                if self.upload_file(file_path, dropbox_path):
                    uploaded_count += 1

        return uploaded_count

    def delete_folder(self, folder_path: str) -> bool:
        """
        Delete folder from Dropbox
        Summary: Deletes folder and all its contents
        """
        if not self.enabled:
            return False

        try:
            full_path = f"{self.base_path}/{folder_path}".replace('//', '/')
            self.dbx.files_delete_v2(full_path)
            logger.info(f"Deleted Dropbox folder: {full_path}")
            return True
        except ApiError as e:
            error_str = str(e)
            # Folder doesn't exist - this is fine
            if 'not_found' in error_str.lower():
                logger.debug(f"Folder doesn't exist (already deleted): {full_path}")
                return True
            logger.error(f"Failed to delete folder {folder_path}: {e}")
            return False

    def create_folder(self, folder_path: str, delete_if_exists: bool = False) -> bool:
        """
        Create folder in Dropbox
        Summary: Creates folder if it doesn't exist, optionally deletes existing folder first
        """
        if not self.enabled:
            return False

        full_path = f"{self.base_path}/{folder_path}".replace('//', '/')

        # Delete existing folder if requested
        if delete_if_exists:
            self.delete_folder(folder_path)

        try:
            self.dbx.files_create_folder_v2(full_path)
            logger.info(f"Created Dropbox folder: {full_path}")
            return True
        except ApiError as e:
            error_str = str(e)
            # Folder already exists - this is fine
            if 'conflict' in error_str.lower() or 'folder' in error_str.lower():
                logger.debug(f"Folder already exists: {full_path}")
                return True
            logger.error(f"Failed to create folder {folder_path}: {e}")
            return False
