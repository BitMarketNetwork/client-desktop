Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 96

################################################################################

!define BMN_INSTALL_NAME \
    "${BMN_NAME} ${BMN_VERSION_STRING} Setup"
!define BMN_UNINSTALL_REGKEY \
    "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BMN_NAME}"

################################################################################

# https://nsis.sourceforge.io/Docs/MultiUser/Readme.html
!define MULTIUSER_MUI
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_USE_PROGRAMFILES64
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY "${BMN_UNINSTALL_REGKEY}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "NSISInstallMode"
!define MULTIUSER_INSTALLMODE_INSTDIR "${BMN_NAME}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "${BMN_UNINSTALL_REGKEY}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "NSISInstallPath"
!include "MultiUser.nsh"

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "x64.nsh"

################################################################################

Name "${BMN_NAME} ${BMN_VERSION_STRING}"
BrandingText "${BMN_INSTALL_NAME}"
Caption "${BMN_INSTALL_NAME}"

CRCCheck force
AllowSkipFiles off

OutFile "${DIST_TARGET}"

# Sync with pyinstaller.spec
VIFileVersion ${BMN_VERSION_STRING}.0
VIProductVersion ${BMN_VERSION_STRING}.0

VIAddVersionKey FileDescription "${BMN_INSTALL_NAME}"
VIAddVersionKey FileVersion ${BMN_VERSION_STRING}
VIAddVersionKey OriginalFilename "${DIST_TARGET_FILE_NAME}"

VIAddVersionKey ProductName "${BMN_NAME}"
VIAddVersionKey ProductVersion ${BMN_VERSION_STRING}

VIAddVersionKey CompanyName "${BMN_MAINTAINER}"
VIAddVersionKey LegalCopyright "© ${BMN_MAINTAINER}. All rights reserved."

################################################################################

# https://nsis.sourceforge.io/Docs/Modern%20UI%202/Readme.html

!define MUI_ABORTWARNING
!define MUI_ABORTWARNING_TEXT "Are you sure you want to quit?"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "../../LICENSE"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\${DIST_TARGET_NAME_RELEASE}"
!define MUI_FINISHPAGE_RUN_TEXT "Run $(^Name)"
!define MUI_FINISHPAGE_LINK "Visit project website"
!define MUI_FINISHPAGE_LINK_LOCATION "${BMN_MAINTAINER_URL}"
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_UNFINISHPAGE_NOAUTOCLOSE
!insertmacro MUI_UNPAGE_FINISH

# TODO
!insertmacro MUI_LANGUAGE "English"

################################################################################

Function .onInit
    !insertmacro MULTIUSER_INIT
    ${If} ${RunningX64}
    ${Else}
        MessageBox mb_iconstop "Unsupported CPU architecture!"
        SetErrorLevel 1633 # ERROR_INSTALL_PLATFORM_UNSUPPORTED
        Quit
    ${EndIf}
FunctionEnd

Function un.onInit
    !insertmacro MULTIUSER_UNINIT
FunctionEnd

Section
    SetOutPath $INSTDIR
    ${DisableX64FSRedirection}

    RMDir /r "$INSTDIR\*.*"
    File /r "${DIST_SOURCE_DIR}\*.*"
    WriteUninstaller "$INSTDIR\uninstall.exe"

    CreateShortCut \
        "$DESKTOP\${BMN_NAME}.lnk" \
        "$INSTDIR\${DIST_TARGET_NAME_RELEASE}"
    CreateDirectory "$SMPROGRAMS\${BMN_NAME}"
    CreateShortCut \
        "$SMPROGRAMS\${BMN_NAME}\${BMN_NAME}.lnk" \
        "$INSTDIR\${DIST_TARGET_NAME_RELEASE}"
    CreateShortCut \
        "$SMPROGRAMS\${BMN_NAME}\Uninstall.lnk" \
        "$INSTDIR\uninstall.exe"

    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "DisplayName" \
        "$(^Name)"
    ${GetTime} "" "L" $0 $1 $2 $3 $4 $5 $6
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "InstallDate" \
        "$2$1$0"
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "EstimatedSize" \
        "$0"
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "UninstallString" \
        "$INSTDIR\uninstall.exe"
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "DisplayVersion" \
        "${BMN_VERSION_STRING}"
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "URLInfoAbout" \
        "${BMN_MAINTAINER_URL}"
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "Publisher" "${BMN_MAINTAINER}"
    WriteRegStr SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}" \
        "DisplayIcon" \
        "$INSTDIR\${DIST_TARGET_NAME_RELEASE},0"

    WriteRegStr SHELL_CONTEXT \
        "${MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY}" \
        "${MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME}" \
        "$MultiUser.InstallMode"
    WriteRegStr SHELL_CONTEXT \
        "${MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY}" \
        "${MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME}" \
        "$INSTDIR"
SectionEnd

################################################################################

Section "Uninstall"
    ${DisableX64FSRedirection}

    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\${BMN_NAME}"
    Delete "$DESKTOP\${BMN_NAME}.lnk"

    DeleteRegKey SHELL_CONTEXT "${BMN_UNINSTALL_REGKEY}"
    DeleteRegKey SHELL_CONTEXT "${MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY}"
    DeleteRegKey SHELL_CONTEXT "${MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY}"

    SetShellVarContext current
    RMDir /r "$APPDATA\${BMN_NAME}"
    RMDir /r "$LOCALAPPDATA\${BMN_NAME}"

    SetShellVarContext all
    RMDir /r "$APPDATA\${BMN_NAME}"
    RMDir /r "$LOCALAPPDATA\${BMN_NAME}"
SectionEnd
