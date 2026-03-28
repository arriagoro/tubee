# DaVinci Resolve Scripting API — Complete Developer Reference
### Python & Lua Automation for DaVinci Resolve
*Based on official Blackmagic Design documentation, community docs, and practical examples*

---

## Table of Contents
1. [Overview & Prerequisites](#1-overview--prerequisites)
2. [Environment Setup](#2-environment-setup)
3. [API Object Hierarchy](#3-api-object-hierarchy)
4. [Complete API Reference](#4-complete-api-reference)
5. [Practical Script Examples](#5-practical-script-examples)
6. [Fusion Scripting](#6-fusion-scripting)
7. [Automation Recipes](#7-automation-recipes)
8. [Tips & Gotchas](#8-tips--gotchas)

---

## 1. Overview & Prerequisites

### What It Is
DaVinci Resolve exposes a scripting API that lets you control almost every aspect of the application via Python or Lua scripts. You can create projects, import media, build timelines, set render settings, start renders, manage color grades, add markers, and more — all programmatically.

### Requirements
- **DaVinci Resolve** must be running (scripts connect to a running instance)
- **DaVinci Resolve Studio** required for some features (headless mode, certain render codecs)
- **Python 3.6+** (64-bit) or **Lua 5.1**
- Scripts can run from:
  - The built-in Console (Fusion page → Console)
  - External scripts via command line
  - Menu scripts (placed in specific directories)

### What You Can Automate

| Category | What You Can Do |
|----------|----------------|
| **Project Management** | Create, open, close, save, archive, export projects |
| **Media** | Import files, set metadata, manage bins/folders |
| **Timeline** | Create timelines, append clips, get/set track info, add markers |
| **Editing** | Get/set clip properties, create compound clips, manage takes |
| **Color** | Apply LUTs, CDL values, copy grades, grab stills, export DRX |
| **Rendering** | Set format/codec/settings, add to queue, start/stop rendering |
| **Fusion** | Access Fusion comps, import/export comps |
| **Layout** | Save/load UI layouts, switch pages |

### What You CAN'T Automate (Limitations)
- Direct manipulation of Color Wheels (no API for lift/gamma/gain adjustments beyond CDL)
- Fusion node creation from the Resolve API (must use Fusion scripting separately)
- Fairlight mixer levels (very limited)
- Direct UI interaction (no button clicks or menu selections)
- Real-time playback control (limited)

---

## 2. Environment Setup

### macOS Setup

```bash
# Add to ~/.zshrc or ~/.bash_profile
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

### Windows Setup

```powershell
# Add as system environment variables
RESOLVE_SCRIPT_API=%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules\
```

### Linux Setup

```bash
export RESOLVE_SCRIPT_API="/opt/resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/opt/resolve/libs/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

### Script Directories (Menu-Invocable Scripts)

DaVinci Resolve scans these folders on startup and lists scripts in Workspace → Scripts:

**macOS:**
- All users: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/`
- Current user: `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/`

**Windows:**
- All users: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\`
- Current user: `%APPDATA%\Roaming\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\`

**Subfolder Organization:**
```
Scripts/
├── Utility/     → Listed in all pages
├── Comp/        → Available in Fusion page
├── Tool/        → Available in Fusion page
├── Edit/        → Available in Edit page
├── Color/       → Available in Color page
└── Deliver/     → Available in Deliver page (+ render jobs)
```

### Connecting to Resolve (Boilerplate)

```python
#!/usr/bin/env python3
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
if not resolve:
    print("ERROR: DaVinci Resolve is not running or not accessible")
    exit(1)

# Now you can access all API objects
fusion = resolve.Fusion()
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()
```

### Headless Mode (DaVinci Resolve Studio Only)

```bash
# Launch Resolve without UI
"/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve" -nogui
```

All scripting APIs work in headless mode. Useful for automated render farms.

---

## 3. API Object Hierarchy

```
Resolve
├── Fusion()                    → Fusion object (Fusion scripting access)
├── GetMediaStorage()           → MediaStorage
│   ├── GetMountedVolumeList()
│   ├── GetSubFolderList()
│   ├── GetFileList()
│   └── AddItemListToMediaPool()
├── GetProjectManager()         → ProjectManager
│   ├── CreateProject()         → Project
│   ├── LoadProject()           → Project
│   ├── GetCurrentProject()     → Project
│   │   ├── GetMediaPool()      → MediaPool
│   │   │   ├── GetRootFolder() → Folder
│   │   │   │   ├── GetClipList()    → [MediaPoolItem]
│   │   │   │   └── GetSubFolderList() → [Folder]
│   │   │   ├── CreateEmptyTimeline()  → Timeline
│   │   │   ├── AppendToTimeline()     → [TimelineItem]
│   │   │   ├── CreateTimelineFromClips() → Timeline
│   │   │   └── ImportTimelineFromFile()  → Timeline
│   │   ├── GetCurrentTimeline()  → Timeline
│   │   │   ├── GetTrackCount()
│   │   │   ├── GetItemListInTrack() → [TimelineItem]
│   │   │   │   ├── GetName()
│   │   │   │   ├── GetDuration()
│   │   │   │   ├── SetLUT()
│   │   │   │   ├── SetCDL()
│   │   │   │   ├── CopyGrades()
│   │   │   │   ├── GetFusionCompByIndex() → fusionComp
│   │   │   │   └── GetMediaPoolItem()    → MediaPoolItem
│   │   │   ├── AddMarker()
│   │   │   └── GetMarkers()
│   │   ├── GetGallery()          → Gallery
│   │   ├── SetRenderSettings()
│   │   ├── AddRenderJob()
│   │   ├── StartRendering()
│   │   └── GetRenderJobStatus()
│   └── GetDatabaseList()
└── OpenPage()                  → Switch pages
```

---

## 4. Complete API Reference

### Resolve Object

```python
resolve.Fusion()                                    # → Fusion object
resolve.GetMediaStorage()                           # → MediaStorage
resolve.GetProjectManager()                         # → ProjectManager
resolve.OpenPage(pageName)                          # → Bool
    # pageName: "media", "cut", "edit", "fusion", "color", "fairlight", "deliver"
resolve.GetCurrentPage()                            # → String or None
resolve.GetProductName()                            # → String
resolve.GetVersion()                                # → [major, minor, patch, build, suffix]
resolve.GetVersionString()                          # → String
resolve.LoadLayoutPreset(presetName)                # → Bool
resolve.SaveLayoutPreset(presetName)                # → Bool
resolve.ExportLayoutPreset(presetName, filePath)    # → Bool
resolve.ImportLayoutPreset(filePath, presetName)    # → Bool
resolve.DeleteLayoutPreset(presetName)              # → Bool
resolve.Quit()                                      # → None
resolve.ImportRenderPreset(presetPath)              # → Bool
resolve.ExportRenderPreset(presetName, exportPath)  # → Bool
```

### ProjectManager Object

```python
pm = resolve.GetProjectManager()

pm.CreateProject(projectName)                       # → Project or None
pm.DeleteProject(projectName)                       # → Bool
pm.LoadProject(projectName)                         # → Project or None
pm.GetCurrentProject()                              # → Project
pm.SaveProject()                                    # → Bool
pm.CloseProject(project)                            # → Bool
pm.CreateFolder(folderName)                         # → Bool
pm.DeleteFolder(folderName)                         # → Bool
pm.GetProjectListInCurrentFolder()                  # → [project names]
pm.GetFolderListInCurrentFolder()                   # → [folder names]
pm.GotoRootFolder()                                 # → Bool
pm.GotoParentFolder()                               # → Bool
pm.GetCurrentFolder()                               # → String
pm.OpenFolder(folderName)                           # → Bool
pm.ImportProject(filePath, projectName=None)         # → Bool
pm.ExportProject(projectName, filePath, withStillsAndLUTs=True)  # → Bool
pm.RestoreProject(filePath, projectName=None)        # → Bool
pm.ArchiveProject(projectName, filePath,
    isArchiveSrcMedia=True,
    isArchiveRenderCache=True,
    isArchiveProxyMedia=False)                       # → Bool
pm.GetCurrentDatabase()                             # → {DbType, DbName, IpAddress}
pm.GetDatabaseList()                                # → [{DbType, DbName, IpAddress}]
pm.SetCurrentDatabase({dbInfo})                     # → Bool
    # dbInfo keys: "DbType" ("Disk"/"PostgreSQL"), "DbName", "IpAddress" (optional)
```

### Project Object

```python
project = pm.GetCurrentProject()

# Media & Timeline
project.GetMediaPool()                              # → MediaPool
project.GetTimelineCount()                          # → int
project.GetTimelineByIndex(idx)                     # → Timeline (1-based index)
project.GetCurrentTimeline()                        # → Timeline
project.SetCurrentTimeline(timeline)                # → Bool
project.GetGallery()                                # → Gallery
project.GetName()                                   # → String
project.SetName(projectName)                        # → Bool
project.GetPresetList()                             # → [presets]
project.SetPreset(presetName)                       # → Bool
project.GetUniqueId()                               # → String

# Rendering
project.AddRenderJob()                              # → String (job ID)
project.DeleteRenderJob(jobId)                      # → Bool
project.DeleteAllRenderJobs()                       # → Bool
project.GetRenderJobList()                          # → [render jobs]
project.GetRenderPresetList()                       # → [presets]
project.StartRendering(jobId1, jobId2, ...)         # → Bool
project.StartRendering([jobIds], isInteractiveMode=False)  # → Bool
project.StartRendering(isInteractiveMode=False)     # → Bool (all jobs)
project.StopRendering()                             # → None
project.IsRenderingInProgress()                     # → Bool
project.LoadRenderPreset(presetName)                # → Bool
project.SaveAsNewRenderPreset(presetName)           # → Bool
project.GetRenderJobStatus(jobId)                   # → {status info}
project.GetRenderFormats()                          # → {format → file extension}
project.GetRenderCodecs(renderFormat)               # → {codec description → codec name}
project.GetCurrentRenderFormatAndCodec()            # → {format, codec}
project.SetCurrentRenderFormatAndCodec(format, codec)  # → Bool
project.GetCurrentRenderMode()                      # → int (0=Individual clips, 1=Single clip)
project.SetCurrentRenderMode(renderMode)            # → Bool

# Settings
project.GetSetting(settingName)                     # → String
project.SetSetting(settingName, settingValue)       # → Bool
project.SetRenderSettings({settings})               # → Bool
    # Supported keys: "SelectAllFrames", "MarkIn", "MarkOut", "TargetDir",
    # "CustomName", "UniqueFilenameStyle", "ExportVideo", "ExportAudio",
    # "FormatWidth", "FormatHeight", "FrameRate",
    # "PixelAspectRatio", "VideoQuality", "AudioCodec", "AudioBitDepth",
    # "AudioSampleRate", "ColorSpaceTag", "GammaTag",
    # "ExportAlpha", "EncodingProfile", "MultiPassEncode",
    # "AlphaMode", "NetworkOptimization"

project.RefreshLUTList()                            # → Bool
project.ExportCurrentFrameAsStill(filePath)         # → Bool
```

### MediaStorage Object

```python
ms = resolve.GetMediaStorage()

ms.GetMountedVolumeList()                           # → [paths]
ms.GetSubFolderList(folderPath)                     # → [paths]
ms.GetFileList(folderPath)                          # → [paths]
ms.RevealInStorage(path)                            # → Bool
ms.AddItemListToMediaPool(item1, item2, ...)        # → [MediaPoolItem]
ms.AddItemListToMediaPool([items])                  # → [MediaPoolItem]
ms.AddItemListToMediaPool([{                        # → [MediaPoolItem]
    "media": "/path/to/file",
    "startFrame": int,
    "endFrame": int
}])
ms.AddClipMattesToMediaPool(mpi, [paths], stereoEye)  # → Bool
ms.AddTimelineMattesToMediaPool([paths])            # → [MediaPoolItem]
```

### MediaPool Object

```python
mp = project.GetMediaPool()

mp.GetRootFolder()                                  # → Folder
mp.AddSubFolder(folder, name)                       # → Folder
mp.RefreshFolders()                                 # → Bool
mp.CreateEmptyTimeline(name)                        # → Timeline
mp.AppendToTimeline(clip1, clip2, ...)              # → [TimelineItem]
mp.AppendToTimeline([clips])                        # → [TimelineItem]
mp.AppendToTimeline([{                              # → [TimelineItem]
    "mediaPoolItem": mpi,
    "startFrame": int,
    "endFrame": int,
    "mediaType": int,      # 1=Video only, 2=Audio only (optional)
    "trackIndex": int,     # (optional)
    "recordFrame": int     # (optional)
}])
mp.CreateTimelineFromClips(name, clip1, clip2, ...) # → Timeline
mp.CreateTimelineFromClips(name, [clips])           # → Timeline
mp.CreateTimelineFromClips(name, [{clipInfo}])      # → Timeline
mp.ImportTimelineFromFile(filePath, {importOptions}) # → Timeline
    # importOptions keys: "timelineName", "importSourceClips", "sourceClipsPath",
    # "sourceClipsFolders", "interlaceProcessing"
mp.DeleteTimelines([timelines])                     # → Bool
mp.GetCurrentFolder()                               # → Folder
mp.SetCurrentFolder(folder)                         # → Bool
mp.DeleteClips([clips])                             # → Bool
mp.DeleteFolders([subfolders])                      # → Bool
mp.MoveClips([clips], targetFolder)                 # → Bool
mp.MoveFolders([folders], targetFolder)             # → Bool
mp.GetClipMatteList(mpi)                            # → [paths]
mp.GetTimelineMatteList(folder)                     # → [MediaPoolItem]
mp.DeleteClipMattes(mpi, [paths])                   # → Bool
mp.RelinkClips([mpis], folderPath)                  # → Bool
mp.UnlinkClips([mpis])                              # → Bool
mp.ImportMedia([items])                             # → [MediaPoolItem]
mp.ImportMedia([{"FilePath": "file_%03d.dpx", "StartIndex": 1, "EndIndex": 100}])
mp.ExportMetadata(fileName, [clips])                # → Bool
mp.GetUniqueId()                                    # → String
```

### Folder Object

```python
folder = mp.GetRootFolder()

folder.GetClipList()                                # → [MediaPoolItem]
folder.GetName()                                    # → String
folder.GetSubFolderList()                           # → [Folder]
folder.GetIsFolderStale()                           # → Bool (collaboration mode)
folder.GetUniqueId()                                # → String
folder.Export(filePath)                              # → Bool (DRB export)
```

### MediaPoolItem Object

```python
clip = folder.GetClipList()[0]

clip.GetName()                                      # → String
clip.GetMetadata(metadataType=None)                 # → String or dict
clip.SetMetadata(metadataType, metadataValue)       # → Bool
clip.SetMetadata({metadata})                        # → Bool
clip.GetMediaId()                                   # → String
clip.AddMarker(frameId, color, name, note, duration, customData)  # → Bool
clip.GetMarkers()                                   # → {frameId: {info}}
clip.GetMarkerByCustomData(customData)              # → {marker info}
clip.UpdateMarkerCustomData(frameId, customData)    # → Bool
clip.GetMarkerCustomData(frameId)                   # → String
clip.DeleteMarkersByColor(color)                    # → Bool ("All" for all)
clip.DeleteMarkerAtFrame(frameNum)                  # → Bool
clip.DeleteMarkerByCustomData(customData)           # → Bool
clip.AddFlag(color)                                 # → Bool
clip.GetFlagList()                                  # → [colors]
clip.ClearFlags(color)                              # → Bool ("All" for all)
clip.GetClipColor()                                 # → String
clip.SetClipColor(colorName)                        # → Bool
clip.ClearClipColor()                               # → Bool
clip.GetClipProperty(propertyName=None)             # → String or dict
clip.SetClipProperty(propertyName, propertyValue)   # → Bool
clip.LinkProxyMedia(proxyMediaFilePath)             # → Bool
clip.UnlinkProxyMedia()                             # → Bool
clip.ReplaceClip(filePath)                          # → Bool
clip.GetUniqueId()                                  # → String
clip.TranscribeAudio()                              # → Bool
clip.ClearTranscription()                           # → Bool
```

**Clip Property Keys:**
- Read/Write: "Clip Name", "Comments", "Description", "Shot", "Scene", "Take", "Reel Name", "Start TC", "End TC", "Good Take", "Angle", "Super Scale"
- Read-Only: "Alpha mode", "Bit Depth", "Camera #", "Clip Color", "Data Level", "Date Created", "Date Modified", "Duration", "File Name", "File Path", "Format", "Frames", "FPS", "Frame Rate", "Has Audio", "Height", "Input Color Space", "Input Sizing Preset", "PAR", "Proxy", "Resolution", "Sample Rate", "Start", "Type", "Usage", "Video Codec", "Width"

### Timeline Object

```python
timeline = project.GetCurrentTimeline()

timeline.GetName()                                  # → String
timeline.SetName(timelineName)                      # → Bool
timeline.GetStartFrame()                            # → int
timeline.GetEndFrame()                              # → int
timeline.SetStartTimecode(timecode)                 # → Bool
timeline.GetStartTimecode()                         # → String
timeline.GetTrackCount(trackType)                   # → int
    # trackType: "audio", "video", "subtitle"
timeline.AddTrack(trackType, optionalSubTrackType)  # → Bool
    # optionalSubTrackType for audio: "mono", "stereo", "5.1", "5.1film",
    # "7.1", "7.1film", "adaptive1" ... "adaptive24"
timeline.DeleteTrack(trackType, trackIndex)         # → Bool
timeline.SetTrackEnable(trackType, trackIndex, Bool) # → Bool
timeline.GetIsTrackEnabled(trackType, trackIndex)   # → Bool
timeline.SetTrackLock(trackType, trackIndex, Bool)  # → Bool
timeline.GetIsTrackLocked(trackType, trackIndex)    # → Bool
timeline.GetItemListInTrack(trackType, index)       # → [TimelineItem]
timeline.AddMarker(frameId, color, name, note, duration, customData)  # → Bool
timeline.GetMarkers()                               # → {frameId: {info}}
timeline.DeleteMarkersByColor(color)                # → Bool
timeline.DeleteMarkerAtFrame(frameNum)              # → Bool
timeline.DeleteClips([timelineItems], ripple=False)  # → Bool
timeline.SetClipsLinked([timelineItems], Bool)       # → Bool
timeline.ApplyGradeFromDRX(path, gradeMode, item1, ...)  # → Bool
    # gradeMode: 0="No keyframes", 1="Source Timecode aligned", 2="Start Frames aligned"
timeline.GetCurrentTimecode()                       # → String
timeline.SetCurrentTimecode(timecode)               # → Bool
timeline.GetCurrentVideoItem()                      # → TimelineItem
timeline.GetCurrentClipThumbnailImage()             # → {width, height, format, data}
timeline.GetTrackName(trackType, trackIndex)        # → String
timeline.SetTrackName(trackType, trackIndex, name)  # → Bool
timeline.DuplicateTimeline(timelineName)            # → Timeline
timeline.CreateCompoundClip([timelineItems], {clipInfo})  # → TimelineItem
timeline.CreateFusionClip([timelineItems])           # → TimelineItem
timeline.GetUniqueId()                              # → String
```

### TimelineItem Object

```python
item = timeline.GetItemListInTrack("video", 1)[0]

item.GetName()                                      # → String
item.GetDuration()                                  # → int
item.GetStart()                                     # → int
item.GetEnd()                                       # → int
item.GetLeftOffset()                                # → int
item.GetRightOffset()                               # → int
item.GetMediaPoolItem()                             # → MediaPoolItem

# Markers & Flags
item.AddMarker(frameId, color, name, note, duration, customData)  # → Bool
item.GetMarkers()                                   # → {frameId: {info}}
item.DeleteMarkersByColor(color)                    # → Bool
item.DeleteMarkerAtFrame(frameNum)                  # → Bool
item.AddFlag(color)                                 # → Bool
item.GetFlagList()                                  # → [colors]
item.ClearFlags(color)                              # → Bool
item.GetClipColor()                                 # → String
item.SetClipColor(colorName)                        # → Bool
item.ClearClipColor()                               # → Bool

# Color Grading
item.SetLUT(nodeIndex, lutPath)                     # → Bool (1-based nodeIndex)
item.SetCDL({                                       # → Bool
    "NodeIndex": "1",
    "Slope": "0.5 0.4 0.2",
    "Offset": "0.4 0.3 0.2",
    "Power": "0.6 0.7 0.8",
    "Saturation": "0.65"
})
item.CopyGrades([targetTimelineItems])              # → Bool

# Fusion
item.GetFusionCompCount()                           # → int
item.GetFusionCompByIndex(compIndex)                # → fusionComp (1-based)
item.GetFusionCompNameList()                        # → [names]
item.GetFusionCompByName(compName)                  # → fusionComp
item.AddFusionComp()                                # → fusionComp
item.ImportFusionComp(path)                         # → fusionComp
item.ExportFusionComp(path, compIndex)              # → Bool
item.DeleteFusionCompByName(compName)               # → Bool
item.LoadFusionCompByName(compName)                 # → fusionComp
item.RenameFusionCompByName(oldName, newName)       # → Bool

# Versions
item.AddVersion(versionName, versionType)           # → Bool (0=local, 1=remote)
item.DeleteVersionByName(versionName, versionType)  # → Bool
item.LoadVersionByName(versionName, versionType)    # → Bool
item.RenameVersionByName(oldName, newName, versionType)  # → Bool
item.GetVersionNameList(versionType)                # → [names]

# Takes
item.AddTake(mediaPoolItem, startFrame, endFrame)   # → Bool
item.GetSelectedTakeIndex()                         # → int
item.GetTakesCount()                                # → int
item.GetTakeByIndex(idx)                            # → {startFrame, endFrame, mediaPoolItem}
item.DeleteTakeByIndex(idx)                         # → Bool
item.SelectTakeByIndex(idx)                         # → Bool
item.FinalizeTake()                                 # → Bool
```

---

## 5. Practical Script Examples

### Example 1: Create Project and Import Media

```python
#!/usr/bin/env python3
"""Create a new project and import all footage from a folder."""
import DaVinciResolveScript as dvr_script
import os

resolve = dvr_script.scriptapp("Resolve")
pm = resolve.GetProjectManager()

# Create project
project = pm.CreateProject("Wedding_Johnson_2026")
if not project:
    project = pm.LoadProject("Wedding_Johnson_2026")

mp = project.GetMediaPool()

# Create organized bin structure
root = mp.GetRootFolder()
footage_bin = mp.AddSubFolder(root, "01_Footage")
audio_bin = mp.AddSubFolder(root, "02_Audio")
graphics_bin = mp.AddSubFolder(root, "03_Graphics")

# Import footage
ms = resolve.GetMediaStorage()
mp.SetCurrentFolder(footage_bin)

footage_path = "/Volumes/Edit_Drive/Wedding_Johnson/Footage/"
clips = ms.AddItemListToMediaPool([footage_path])
print(f"Imported {len(clips)} clips")

# Import audio
mp.SetCurrentFolder(audio_bin)
audio_path = "/Volumes/Edit_Drive/Wedding_Johnson/Audio/"
audio_clips = ms.AddItemListToMediaPool([audio_path])
print(f"Imported {len(audio_clips)} audio files")
```

### Example 2: Build Timeline from Marked Clips

```python
#!/usr/bin/env python3
"""Create a timeline using clips marked with green flags."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()

# Find all clips with green flags
root = mp.GetRootFolder()
selected_clips = []

def find_flagged_clips(folder):
    for clip in folder.GetClipList():
        flags = clip.GetFlagList()
        if "Green" in flags:
            selected_clips.append(clip)
    for subfolder in folder.GetSubFolderList():
        find_flagged_clips(subfolder)

find_flagged_clips(root)
print(f"Found {len(selected_clips)} flagged clips")

# Create timeline from selected clips
if selected_clips:
    timeline = mp.CreateTimelineFromClips("Selects_v1", selected_clips)
    project.SetCurrentTimeline(timeline)
    print(f"Created timeline: {timeline.GetName()}")
```

### Example 3: Batch Apply LUT to All Clips

```python
#!/usr/bin/env python3
"""Apply a specific LUT to all clips in the current timeline."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()

lut_path = "Sony/Sony SLog3 SGamut3.Cine to LC-709TypeA.cube"

video_track_count = timeline.GetTrackCount("video")
total_applied = 0

for track_idx in range(1, video_track_count + 1):
    items = timeline.GetItemListInTrack("video", track_idx)
    for item in items:
        success = item.SetLUT(1, lut_path)  # Apply to node 1
        if success:
            total_applied += 1

print(f"Applied LUT to {total_applied} clips")
```

### Example 4: Add Markers Based on Clip Duration

```python
#!/usr/bin/env python3
"""Add red markers on clips longer than 30 seconds (potential trim candidates)."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()

fps = float(project.GetSetting("timelineFrameRate"))
threshold_frames = int(30 * fps)  # 30 seconds

items = timeline.GetItemListInTrack("video", 1)
for item in items:
    duration = item.GetDuration()
    if duration > threshold_frames:
        frame_id = item.GetStart()
        seconds = duration / fps
        item.AddMarker(0, "Red", "Long Clip",
            f"Duration: {seconds:.1f}s - consider trimming", 1)

print("Markers added for long clips")
```

### Example 5: Automated Render for Multiple Platforms

```python
#!/usr/bin/env python3
"""Set up render jobs for YouTube, Instagram, and Archive."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()

output_dir = "/Volumes/Edit_Drive/Exports/"

# YouTube 4K
project.SetCurrentRenderFormatAndCodec("mp4", "H264")
project.SetRenderSettings({
    "SelectAllFrames": True,
    "TargetDir": output_dir + "YouTube/",
    "CustomName": project.GetName() + "_YouTube_4K",
    "FormatWidth": "3840",
    "FormatHeight": "2160",
    "ExportVideo": True,
    "ExportAudio": True
})
youtube_job = project.AddRenderJob()
print(f"Added YouTube render job: {youtube_job}")

# Instagram Reels (Vertical)
project.SetCurrentRenderFormatAndCodec("mp4", "H264")
project.SetRenderSettings({
    "SelectAllFrames": True,
    "TargetDir": output_dir + "Instagram/",
    "CustomName": project.GetName() + "_IG_Reel",
    "FormatWidth": "1080",
    "FormatHeight": "1920",
    "ExportVideo": True,
    "ExportAudio": True
})
ig_job = project.AddRenderJob()
print(f"Added Instagram render job: {ig_job}")

# ProRes Master
project.SetCurrentRenderFormatAndCodec("mov", "ProRes422HQ")
project.SetRenderSettings({
    "SelectAllFrames": True,
    "TargetDir": output_dir + "Master/",
    "CustomName": project.GetName() + "_MASTER",
    "ExportVideo": True,
    "ExportAudio": True
})
master_job = project.AddRenderJob()
print(f"Added Master render job: {master_job}")

# Start all rendering
project.StartRendering()
print("Rendering started!")

# Monitor progress
import time
while project.IsRenderingInProgress():
    for job_id in [youtube_job, ig_job, master_job]:
        status = project.GetRenderJobStatus(job_id)
        print(f"Job {job_id}: {status}")
    time.sleep(5)

print("All renders complete!")
```

### Example 6: Export Metadata Report

```python
#!/usr/bin/env python3
"""Export a CSV of all clip metadata from the media pool."""
import DaVinciResolveScript as dvr_script
import csv

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()

# Collect all clips
all_clips = []
def collect_clips(folder):
    all_clips.extend(folder.GetClipList())
    for sub in folder.GetSubFolderList():
        collect_clips(sub)

collect_clips(mp.GetRootFolder())

# Export metadata
output_file = "/Users/agentarri/Desktop/clip_metadata.csv"
with open(output_file, 'w', newline='') as f:
    writer = None
    for clip in all_clips:
        props = clip.GetClipProperty()
        if writer is None:
            writer = csv.DictWriter(f, fieldnames=props.keys())
            writer.writeheader()
        writer.writerow(props)

print(f"Exported metadata for {len(all_clips)} clips to {output_file}")
```

### Example 7: Copy Color Grade Across Clips

```python
#!/usr/bin/env python3
"""Copy the color grade from the first clip to all other clips on V1."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
timeline = project.GetCurrentTimeline()

items = timeline.GetItemListInTrack("video", 1)
if len(items) < 2:
    print("Need at least 2 clips")
    exit()

source = items[0]
targets = items[1:]

success = source.CopyGrades(targets)
print(f"Grade copy {'succeeded' if success else 'failed'} for {len(targets)} clips")
```

---

## 6. Fusion Scripting

Fusion has its own scripting layer accessible through the `resolve.Fusion()` object or through Fusion composition objects from timeline items.

### Accessing Fusion from a Timeline Item

```python
timeline = project.GetCurrentTimeline()
item = timeline.GetCurrentVideoItem()

# Get Fusion composition
comp_count = item.GetFusionCompCount()
if comp_count > 0:
    comp = item.GetFusionCompByIndex(1)
    
    # List all tools in the composition
    tools = comp.GetToolList()
    for tool_name, tool in tools.items():
        print(f"Tool: {tool_name}, Type: {tool.GetAttrs()['TOOLS_RegID']}")
```

### Fusion Console Commands (Python)

```python
# In the Fusion page console:
comp = fusion.GetCurrentComp()
comp.AddTool("Background", -32768, -32768)  # Add Background node
comp.AddTool("Merge", -32768, -32768)       # Add Merge node
comp.AddTool("Text", -32768, -32768)        # Add Text+ node
comp.AddTool("Transform", -32768, -32768)   # Add Transform node

# Get a specific tool
bg = comp.FindTool("Background1")
bg.TopLeftRed = 0.2
bg.TopLeftGreen = 0.3
bg.TopLeftBlue = 0.8

# Animate a property
text = comp.FindTool("Text1")
text.StyledText = "Hello World"
text.Size = 0.1

# Set keyframes
text.Center = comp.Path({
    [0] = {0.5, 0.5},
    [30] = {0.8, 0.2},
    [60] = {0.5, 0.5}
})
```

### Fusion Script Reference

The Fusion scripting API is extensive and documented separately in:
- Blackmagic Design → Help → Documentation → Developer → Fusion Scripting Guide
- PDF: `Fusion8_Scripting_Guide.pdf` (ships with Resolve)
- Location: `/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Docs/`

Key Fusion objects: `Fusion`, `Composition`, `Tool`, `Input`, `Output`, `Flow`, `Loader`, `Saver`

---

## 7. Automation Recipes

### Recipe: Nightly Batch Render

```python
#!/usr/bin/env python3
"""Open each project in a folder, set render settings, and render overnight."""
import DaVinciResolveScript as dvr_script
import time

resolve = dvr_script.scriptapp("Resolve")
pm = resolve.GetProjectManager()

projects_to_render = ["Client_A_Final", "Client_B_Draft", "YouTube_Ep42"]
output_base = "/Volumes/Render_Drive/"

for project_name in projects_to_render:
    project = pm.LoadProject(project_name)
    if not project:
        print(f"SKIP: Could not load {project_name}")
        continue
    
    project.DeleteAllRenderJobs()
    project.SetCurrentRenderFormatAndCodec("mp4", "H264")
    project.SetRenderSettings({
        "SelectAllFrames": True,
        "TargetDir": f"{output_base}{project_name}/",
        "CustomName": f"{project_name}_final"
    })
    project.AddRenderJob()
    project.StartRendering()
    
    while project.IsRenderingInProgress():
        time.sleep(10)
    
    print(f"DONE: {project_name}")
    pm.SaveProject()
    pm.CloseProject(project)

print("All batch renders complete!")
```

### Recipe: Auto-Organize Media Pool by Camera

```python
#!/usr/bin/env python3
"""Sort clips into bins by camera name/model."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()
root = mp.GetRootFolder()

# Get all clips
clips = root.GetClipList()

# Group by camera
camera_groups = {}
for clip in clips:
    metadata = clip.GetMetadata()
    camera = metadata.get("Camera Type", "Unknown")
    if camera not in camera_groups:
        camera_groups[camera] = []
    camera_groups[camera].append(clip)

# Create bins and move clips
for camera_name, camera_clips in camera_groups.items():
    safe_name = camera_name.replace("/", "-").replace("\\", "-")
    bin_folder = mp.AddSubFolder(root, f"Camera_{safe_name}")
    if bin_folder:
        mp.MoveClips(camera_clips, bin_folder)
        print(f"Moved {len(camera_clips)} clips to Camera_{safe_name}")
```

### Recipe: Generate Proxy Media for All Clips

```python
#!/usr/bin/env python3
"""Tag clips that need proxy generation based on resolution."""
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
project = resolve.GetProjectManager().GetCurrentProject()
mp = project.GetMediaPool()

def process_folder(folder):
    for clip in folder.GetClipList():
        props = clip.GetClipProperty()
        width = int(props.get("Resolution", "0x0").split("x")[0]) if "x" in props.get("Resolution", "") else 0
        if width >= 3840:  # 4K or higher
            clip.SetClipColor("Orange")  # Mark for proxy generation
            clip.SetMetadata("Comments", "Needs proxy - 4K+")
    for sub in folder.GetSubFolderList():
        process_folder(sub)

process_folder(mp.GetRootFolder())
print("Clips marked for proxy generation (Orange)")
```

---

## 8. Tips & Gotchas

### Common Pitfalls

1. **Resolve must be running** — Scripts connect to a live instance. No offline scripting.
2. **Node indices are 1-based** (since v16.2.0) — `SetLUT(1, path)` for the first node.
3. **String values everywhere** — Most settings use strings even for numbers: `"FormatWidth": "3840"`
4. **Save before closing** — `CloseProject()` does NOT auto-save. Call `SaveProject()` first.
5. **Frame rates as strings** — `"timelineFrameRate"` returns string like `"23.976"`
6. **API availability** — Some methods only exist in Studio version.
7. **Thread safety** — API is not thread-safe. Don't call from multiple threads simultaneously.
8. **Console vs External** — Console scripts have `resolve` and `fusion` pre-defined. External scripts must import `DaVinciResolveScript`.

### Debugging Tips

```python
# Inspect available methods on any object
print(dir(resolve))
print(dir(project))

# Get all project settings
all_settings = project.GetSetting("")  # Empty string = all settings
for key, value in all_settings.items():
    print(f"{key}: {value}")

# Get all clip properties
clip = mp.GetRootFolder().GetClipList()[0]
props = clip.GetClipProperty()
for key, value in props.items():
    print(f"{key}: {value}")

# Get all render formats and codecs
formats = project.GetRenderFormats()
for fmt, ext in formats.items():
    codecs = project.GetRenderCodecs(fmt)
    print(f"\n{fmt} (.{ext}):")
    for desc, name in codecs.items():
        print(f"  {desc}: {name}")
```

### Performance Tips

- **Batch operations** — Import media as arrays, not one file at a time
- **Minimize page switches** — `OpenPage()` is slow; batch your work per page
- **Use headless mode** for render farms (Studio only)
- **Close unused projects** before scripting — frees memory
- **Use `customData` on markers** to store script-specific metadata without cluttering the UI

### Lua vs Python

| Feature | Python | Lua |
|---------|--------|-----|
| Community support | Larger | Smaller |
| External libraries | Extensive (pip) | Limited |
| Speed in Console | Slightly slower | Slightly faster |
| Fusion native | Via bridge | Native |
| Recommended for | External scripts, complex automation | Quick console commands, Fusion scripts |

### Useful Render Format/Codec Strings

| Format String | Codec String | Description |
|--------------|-------------|-------------|
| `"mp4"` | `"H264"` | H.264 in MP4 |
| `"mp4"` | `"H265"` | H.265/HEVC in MP4 (Studio) |
| `"mov"` | `"ProRes422"` | ProRes 422 |
| `"mov"` | `"ProRes422HQ"` | ProRes 422 HQ |
| `"mov"` | `"ProRes4444"` | ProRes 4444 |
| `"mov"` | `"ProRes4444XQ"` | ProRes 4444 XQ |
| `"mxf"` | `"DNxHR_HQ"` | DNxHR HQ |
| `"mov"` | `"H264_NVIDIA"` | H.264 (NVIDIA GPU) |
| `"mov"` | `"H265_NVIDIA"` | H.265 (NVIDIA GPU, Studio) |

*Note: Available codecs depend on your hardware and whether you have the free or Studio version. Use `project.GetRenderCodecs(format)` to list what's available on your system.*

---

*Last updated: March 2026*
*Compatible with DaVinci Resolve 18, 19, and 20*
*For the latest API reference, always check: Help → Documentation → Developer in your Resolve installation*
