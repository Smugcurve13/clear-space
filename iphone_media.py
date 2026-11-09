from __future__ import annotations

from pathlib import Path
from threading import Event

MEDIA_EXTENSIONS = {".3gp", ".avi", ".heic", ".jpeg", ".jpg", ".m4v", ".mov", ".mp4", ".png", ".webp"}
VIDEO_EXTENSIONS = {".3gp", ".avi", ".m4v", ".mov", ".mp4"}


def is_phone_media(name: str) -> bool:
    return Path(name).suffix.lower() in MEDIA_EXTENSIONS


def media_kind(name: str) -> str:
    return "Video" if Path(name).suffix.lower() in VIDEO_EXTENSIONS else "Photo"


def available_filename(destination: Path, filename: str) -> str:
    candidate = Path(filename).name or "iPhone media"
    stem, suffix = Path(candidate).stem, Path(candidate).suffix
    index = 1
    while (destination / candidate).exists():
        candidate = f"{stem} {index}{suffix}"
        index += 1
    return candidate


try:
    from Foundation import NSObject, NSURL
    from objc import super as objc_super
    from ImageCaptureCore import (
        ICCameraDevice,
        ICDeleteAfterSuccessfulDownload,
        ICDeviceBrowser,
        ICDeviceLocationTypeMaskLocal,
        ICDeviceTypeMaskCamera,
        ICDownloadsDirectoryURL,
        ICOverwrite,
        ICSaveAsFilename,
    )
except ImportError:
    NATIVE_IPHONE_MEDIA_AVAILABLE = False
else:
    NATIVE_IPHONE_MEDIA_AVAILABLE = True


if NATIVE_IPHONE_MEDIA_AVAILABLE:
    class _CatalogDelegate(NSObject):
        def initWithReady_(self, ready):
            self = objc_super(_CatalogDelegate, self).init()
            if self is not None:
                self.ready = ready
            return self

        def deviceDidBecomeReadyWithCompleteContentCatalog_(self, device):
            self.ready.set()


    class _DownloadDelegate(NSObject):
        def initWithRemaining_(self, remaining):
            self = objc_super(_DownloadDelegate, self).init()
            if self is not None:
                self.remaining = remaining
                self.completed = []
                self.failures = []
                self.finished = Event()
            return self

        def didDownloadFile_error_options_contextInfo_(self, file, error, options, context_info):
            filename = str(file.originalFilename())
            if error is None:
                self.completed.append(filename)
            else:
                self.failures.append(f"{filename}: {error.localizedDescription()}")
            self.remaining.discard(filename)
            if not self.remaining:
                self.finished.set()


    class IPhoneMedia:
        def __init__(self):
            self.browser = ICDeviceBrowser.alloc().init()
            self.browser.setBrowsedDeviceTypeMask_(ICDeviceTypeMaskCamera | ICDeviceLocationTypeMaskLocal)
            self.browser.start()
            self._catalog_delegates = []
            self._download_delegates = []

        def devices(self) -> list[dict]:
            phones = []
            for device in self.browser.devices() or []:
                if not isinstance(device, ICCameraDevice) or not device.isAppleDevice():
                    continue
                phones.append({"id": str(device.deviceID()), "name": str(device.name())})
            return phones

        def media(self, device_id: str) -> dict:
            device = self._device(device_id)
            ready = Event()
            delegate = _CatalogDelegate.alloc().initWithReady_(ready)
            self._catalog_delegates.append(delegate)
            device.setDelegate_(delegate)
            if not device.hasOpenSession():
                device.requestOpenSession()
            ready.wait(12)
            if not device.hasOpenSession():
                raise RuntimeError("Unlock the iPhone, tap Trust if asked, then try again.")
            files = [self._payload(file) for file in self._files(device) if is_phone_media(str(file.originalFilename()))]
            files.sort(key=lambda item: item["name"].lower())
            return {"device": {"id": str(device.deviceID()), "name": str(device.name())}, "files": files}

        def copy(self, device_id: str, filenames: list[str], destination: str) -> dict:
            destination_path = Path(destination).expanduser()
            if not destination_path.is_dir():
                raise ValueError("Choose a writable hard-drive folder.")
            device = self._device(device_id)
            if not device.hasOpenSession():
                raise RuntimeError("Open the iPhone media list first, then copy selected items.")
            wanted = set(filenames)
            files = [file for file in self._files(device) if str(file.originalFilename()) in wanted and is_phone_media(str(file.originalFilename()))]
            if not files:
                raise ValueError("Select at least one iPhone photo or video.")
            names = [str(file.originalFilename()) for file in files]
            if len(set(names)) != len(names):
                raise ValueError("Duplicate iPhone filenames are not supported in one copy. Copy them in separate batches.")
            delegate = _DownloadDelegate.alloc().initWithRemaining_(set(names))
            self._download_delegates.append(delegate)
            saved = []
            for file in files:
                filename = available_filename(destination_path, str(file.originalFilename()))
                saved.append(destination_path / filename)
                options = {
                    ICDownloadsDirectoryURL: NSURL.fileURLWithPath_(str(destination_path)),
                    ICSaveAsFilename: filename,
                    ICDeleteAfterSuccessfulDownload: False,
                    ICOverwrite: False,
                }
                device.requestDownloadFile_options_downloadDelegate_didDownloadSelector_contextInfo_(
                    file,
                    options,
                    delegate,
                    b"didDownloadFile:error:options:contextInfo:",
                    None,
                )
            if not delegate.finished.wait(600):
                raise RuntimeError("The iPhone transfer timed out. Keep the phone unlocked and connected, then retry.")
            if delegate.failures:
                raise RuntimeError("Could not copy all selected media: " + "; ".join(delegate.failures))
            missing = [path.name for path in saved if not path.is_file()]
            if missing:
                raise RuntimeError("The iPhone reported success but these files were not saved: " + ", ".join(missing))
            return {"count": len(saved), "destination": str(destination_path), "files": [str(path) for path in saved]}

        def _device(self, device_id: str):
            for device in self.browser.devices() or []:
                if str(device.deviceID()) == device_id and isinstance(device, ICCameraDevice) and device.isAppleDevice():
                    return device
            raise ValueError("Connect and unlock the iPhone, then try again.")

        def _files(self, item):
            children = getattr(item, "mediaFiles", lambda: [])() or []
            for child in children:
                yield from self._files(child)
            if hasattr(item, "originalFilename"):
                yield item

        def _payload(self, file) -> dict:
            name = str(file.originalFilename())
            size = int(file.fileSize() or 0)
            created = file.fileCreationDate()
            return {"name": name, "size": size, "kind": media_kind(name), "created": str(created) if created else "Unknown date"}
else:
    class IPhoneMedia:
        def __init__(self):
            raise RuntimeError("iPhone import is available only in the macOS app.")
